"""API for TraktTV bound to Home Assistant OAuth."""

import logging
from asyncio import gather, sleep
from typing import Any

from aiohttp import ClientSession
from async_timeout import timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from homeassistant.util import dt as dt_util

from custom_components.trakt_tv.utils import compute_calendar_args

from ..configuration import Configuration
from ..const import API_HOST, DOMAIN
from ..exception import TraktException
from ..models.kind import BASIC_KINDS, NEXT_TO_WATCH_KINDS, UPCOMING_KINDS, TraktKind
from ..models.media import Medias
from ..utils import (
    cache_insert,
    cache_retrieve,
    deserialize_json,
    extract_value_from,
    is_int_like,
)

LOGGER = logging.getLogger(__name__)


class TraktApi:
    """Provide TraktTV authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: OAuth2Session,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ):
        """Initialize TraktTV auth."""
        self.web_session = websession
        self.host = API_HOST
        self.oauth_session = oauth_session
        self.hass = hass
        self.config_entry = entry
        self.configuration = Configuration(hass, entry)

    def cache(self) -> dict:
        bucket = self.hass.data.setdefault(DOMAIN, {}).setdefault(
            self.config_entry.entry_id, {}
        )
        return bucket.setdefault("cache", {})

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if not self.oauth_session.valid_token:
            await self.oauth_session.async_ensure_token_valid()

        return self.oauth_session.token["access_token"]

    async def retry_request(self, wait_time, response, method, url, retry, **kwargs):
        """Retry a request {retry} times before logging an error and raising an exception."""
        content = await response.text()
        error = f"Can't request {url} with {method} because it returns a {response.status} status code with content {content}."

        if retry > 0:
            retry = retry - 1
            guidance = f"Retrying at least {retry} time(s)."
            LOGGER.warn(f"{error} {guidance}")
            await sleep(wait_time)
            return await self.request(method, url, retry, **kwargs)
        else:
            guidance = f"Too many retries, if you find this error, please raise an issue at https://github.com/dylandoamaral/trakt-integration/issues."
            raise TraktException(f"{error} {guidance}")

    async def request(self, method, url, retry=10, **kwargs) -> dict[str, Any]:
        """Make a request."""
        access_token = await self.async_get_access_token()
        client_id = self.oauth_session.implementation.client_id
        headers = {
            **kwargs.get("headers", {}),
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "trakt-api-version": "2",
            "trakt-api-key": client_id,
        }

        response = await self.web_session.request(
            method,
            f"{self.host}/{url}",
            **kwargs,
            headers=headers,
        )

        async with response:
            if response.ok:
                text = await response.text()
                return deserialize_json(text)
            elif response.status == 429:
                wait_time = (
                    int(response.headers["Retry-After"]) + 20
                )  # Arbitrary value to have a security
                await self.retry_request(
                    wait_time, response, method, url, retry, **kwargs
                )
            else:
                await self.retry_request(300, response, method, url, retry, **kwargs)

    async def fetch_calendar(
        self, path: str, from_date: str, nb_days: int, all_medias: bool
    ):
        cache_key = f"user_calendar_{path}_{from_date}_{nb_days}"

        maybe_answer = cache_retrieve(self.cache(), cache_key)
        if maybe_answer is not None:
            return maybe_answer

        root = "all" if all_medias else "my"
        response = await self.request(
            "get", f"calendars/{root}/{path}/{from_date}/{nb_days}"
        )

        cache_insert(self.cache(), cache_key, response)

        return response

    def is_show_excluded(self, show, excluded_shows: list, hidden_shows: list) -> bool:
        """Check if a show should be excluded or not."""
        try:
            ids = show["show"]["ids"]
            return ids["slug"] in excluded_shows or ids["trakt"] in hidden_shows
        except IndexError:
            return False

    def is_show_finished(self, show) -> bool:
        """Check if a show is finished or not."""
        try:
            return show["aired"] == show["completed"]
        except KeyError:
            return False

    async def fetch_watched(
        self, excluded_shows: list, excluded_finished: bool = False
    ):
        """First, let's retrieve hidden items from user as a workaround for a potential bug in show progress_watch API"""
        cache_key = f"user_hidden_shows"

        maybe_answer = cache_retrieve(self.cache(), cache_key)
        if maybe_answer is not None:
            hidden_shows = maybe_answer
        else:
            hidden_shows = []
            for section in [
                "calendar",
                "progress_watched",
                "progress_watched_reset",
                "progress_collected",
            ]:
                hidden_items = await self.request(
                    "get", f"users/hidden/{section}?type=show"
                )
                if hidden_items is not None:
                    for hidden_item in hidden_items:
                        try:
                            trakt_id = hidden_item["show"]["ids"]["trakt"]
                            hidden_shows.append(trakt_id)
                        except IndexError:
                            LOGGER.error(
                                "Error while trying to retrieve hidden items in section %s",
                                section,
                            )
            cache_insert(self.cache(), cache_key, hidden_shows)

        """Then, let's retrieve progress for current user by removing hidden or excluded shows"""
        raw_shows = await self.request("get", f"sync/watched/shows?extended=noseasons")
        raw_medias = []

        for show in raw_shows or []:
            try:
                ids = extract_value_from(show, ["show", "ids"])
                identifier = extract_value_from(ids, ["slug"])
            except Exception as e:
                LOGGER.warning(f"Raw show {show} can't be extracted because: {e}")
                continue

            try:
                is_excluded = self.is_show_excluded(show, excluded_shows, hidden_shows)

                if is_excluded:
                    continue

                trakt_identifier = extract_value_from(ids, ["trakt"])

                raw_show_progress = await self.fetch_show_progress(trakt_identifier)
                is_finished = self.is_show_finished(raw_show_progress)

                """aired date and completed date will always be the same for next to watch tvshows if you're up-to-date"""
                if excluded_finished and is_finished:
                    continue

                raw_next_episode = await self.fetch_show_informations(
                    trakt_identifier,
                    extract_value_from(raw_show_progress, ["next_episode", "season"]),
                    extract_value_from(raw_show_progress, ["next_episode", "number"]),
                )

                show["episode"] = raw_next_episode

                if raw_next_episode.get("first_aired") is not None:
                    show["first_aired"] = raw_next_episode["first_aired"]

                raw_medias.append(show)
            except IndexError:
                LOGGER.warning(f"Show {identifier} doesn't contain any trakt ID")
                continue
            except TraktException as e:
                LOGGER.warning(f"Show {identifier} can't be extracted because: {e}")
                continue
            except TypeError as e:
                LOGGER.warning(f"Show {identifier} can't be extracted because: {e}")
                continue
            except KeyError as e:
                LOGGER.warning(f"Show {identifier} can't be extracted because: {e}")
                continue

        return raw_medias

    async def fetch_show_progress(self, id: str):
        cache_key = f"show_progress_{id}"

        maybe_answer = cache_retrieve(self.cache(), cache_key)

        if maybe_answer is not None:
            return maybe_answer

        response = await self.request("get", f"shows/{id}/progress/watched")

        cache_insert(self.cache(), cache_key, response)

        return response

    async def fetch_show_informations(
        self, show_id: str, season_nbr: str, episode_nbr: str
    ):
        return await self.request(
            "get",
            f"shows/{show_id}/seasons/{season_nbr}/episodes/{episode_nbr}?extended=full",
        )

    async def fetch_upcoming(
        self,
        trakt_kind: TraktKind,
        all_medias: bool,
        next_to_watch: bool,
        only_aired: bool,
        only_upcoming: bool,
    ):
        """
        Fetch the calendar of the user trakt account based on the trak_type containing
        the calendar type.

        Since the maximum number of days to fetch using trakt API is 33 days, we have to
        make multiple API calls if we want to retrieve a larger amount of time.

        :param trak_type: The TraktKind describing which calendar we should request
        """

        path = trakt_kind.value.path
        identifier = trakt_kind.value.identifier

        upcoming_identifier_exists = self.configuration.upcoming_identifier_exists(
            identifier, all_medias
        )
        next_to_watch_identifier_exists = self.configuration.identifier_exists(
            identifier, "next_to_watch"
        )

        if (next_to_watch and (not next_to_watch_identifier_exists)) or (
            (not next_to_watch) and (not upcoming_identifier_exists)
        ):
            return None

        max_medias = self.configuration.get_upcoming_max_medias(identifier, all_medias)
        language = self.configuration.get_language()

        if next_to_watch:
            excluded_shows = self.configuration.get_exclude_items(
                identifier, "next_to_watch"
            )
            raw_medias = await self.fetch_watched(excluded_shows, not only_upcoming)
        else:
            days_to_fetch = self.configuration.get_upcoming_days_to_fetch(
                identifier, all_medias
            )
            calendar_args = compute_calendar_args(days_to_fetch, 33)
            data = await gather(
                *[
                    self.fetch_calendar(path, args[0], args[1], all_medias)
                    for args in calendar_args
                ]
            )
            raw_medias = [media for medias in data for media in medias]
            raw_medias = raw_medias[0:max_medias]

        medias = [trakt_kind.value.model.from_trakt(media) for media in raw_medias]

        if next_to_watch:
            if only_aired:
                new_medias = [
                    media for media in medias if media.released <= dt_util.utcnow()
                ]
            elif only_upcoming:
                new_medias = [
                    media for media in medias if media.released > dt_util.utcnow()
                ]
            else:
                new_medias = medias
        else:
            new_medias = [
                media for media in medias if media.released >= dt_util.utcnow()
            ]

        await gather(*[media.get_more_information(language) for media in new_medias])

        return trakt_kind, Medias(new_medias)

    async def fetch_next_to_watch(self, configured_kind: TraktKind):
        only_aired = False
        only_upcoming = False
        if configured_kind == TraktKind.NEXT_TO_WATCH_AIRED:
            only_aired = True
        elif configured_kind == TraktKind.NEXT_TO_WATCH_UPCOMING:
            only_upcoming = True

        return await self.fetch_upcoming(
            configured_kind,
            False,
            True,
            only_aired,
            only_upcoming,
        )

    async def fetch_next_to_watch_medias(self, configured_kinds: list[TraktKind]):
        kinds = [kind for kind in configured_kinds if kind in NEXT_TO_WATCH_KINDS]

        data = await gather(*[self.fetch_next_to_watch(kind) for kind in kinds])
        data = filter(lambda x: x is not None, data)
        return {trakt_kind: medias for trakt_kind, medias in data}

    async def fetch_upcomings(
        self, configured_kinds: list[TraktKind], all_medias: bool
    ):
        kinds = [kind for kind in configured_kinds if kind in UPCOMING_KINDS]

        data = await gather(
            *[
                self.fetch_upcoming(kind, all_medias, False, False, False)
                for kind in kinds
            ]
        )
        data = filter(lambda x: x is not None, data)
        return {trakt_kind: medias for trakt_kind, medias in data}

    async def fetch_recommendation(self, path: str, max_items: int):
        return await self.request(
            "get", f"recommendations/{path}?limit={max_items}&ignore_collected=false"
        )

    async def fetch_recommendations(self, configured_kinds: list[TraktKind]):
        kinds = [kind for kind in configured_kinds if kind in BASIC_KINDS]

        language = self.configuration.get_language()
        data = await gather(
            *[
                self.fetch_recommendation(
                    kind.value.path,
                    self.configuration.get_max_medias(
                        kind.value.identifier, "recommendation"
                    ),
                )
                for kind in kinds
            ]
        )

        res = {}

        for trakt_kind, raw_medias in zip(kinds, data):
            if raw_medias is not None:
                medias = [
                    trakt_kind.value.model.from_trakt(media) for media in raw_medias
                ]
                await gather(
                    *[media.get_more_information(language) for media in medias]
                )
                res[trakt_kind] = Medias(medias)

        return res

    async def fetch_list(
        self,
        path: str,
        list_id: str,
        is_user_path: bool,
        media_type: str,
    ):
        """Fetch the list. If is_user_path is True, the list will be fetched from the user end-point"""
        # Add the user path if needed
        if is_user_path:
            path = f"users/me/{path}"

            # Drop /lists and /items from the path if fetching watchlist or favorites, Trakt API has a different path for these
            if list_id in ["watchlist", "favorites"]:
                path = path.replace("/lists", "").replace("/items", "")
        else:
            # Check that the list_id is numeric for public lists
            if not is_int_like(list_id):
                LOGGER.warning(
                    f"Public lists only support numeric List ID, {list_id} is not valid"
                )
                return None

        # Replace the list_id in the path
        path = path.replace("{list_id}", list_id)

        # Add media type filter to the path
        if media_type and media_type != "any":
            # Check if the media type is supported
            if Medias.trakt_to_class(media_type):
                path = f"{path}/{media_type}"
            else:
                LOGGER.warning(f"Filtering list on {media_type} is not supported")
                return None

        # Add extended info used for sorting
        path = f"{path}?extended=full"

        return await self.request("get", path)

    async def fetch_lists(self, configured_kind: TraktKind):

        # Get config for all lists
        lists = self.configuration.get_sensor_config(configured_kind.value.identifier)

        # Fetch the lists
        data = await gather(
            *[
                self.fetch_list(
                    configured_kind.value.path,
                    list_config["list_id"],
                    list_config["private_list"],
                    list_config["media_type"],
                )
                for list_config in lists
            ]
        )

        # Process the results
        language = self.configuration.get_language()

        res = {}
        for list_config, raw_medias in zip(lists, data):
            if raw_medias is not None:
                medias = []
                for media in raw_medias:
                    # Get model based on media type in data
                    media_type = media.get("type")
                    model = Medias.trakt_to_class(media_type)

                    if model:
                        medias.append(model.from_trakt(media))
                    else:
                        LOGGER.warning(
                            f"Media type {media_type} in {list_config['friendly_name']} is not supported"
                        )

                if not medias:
                    LOGGER.warning(
                        f"No entries found for list {list_config['friendly_name']}"
                    )
                    continue

                # Filtering out watched/collected if needed
                if list_config.get("exclude_collected", False):

                    # Determine media types to check
                    media_types = []
                    if list_config["media_type"] in ["movie", "any"]:
                        media_types.append("movie")
                    if list_config["media_type"] in ["show", "any"]:
                        media_types.append("show")

                    # Collect watched/collected IDs
                    collected_ids = set()
                    for media_type in media_types:
                        for type in ["watched", "collection"]:
                            data = await self.request(
                                "get", f"sync/{type}/{media_type}s"
                            )
                            if data:
                                ids = {
                                    item[media_type]["ids"]["trakt"] for item in data
                                }
                                collected_ids.update(ids)

                    if collected_ids:
                        unwatched_medias = []
                        for media in medias:
                            if media.ids.trakt not in collected_ids:
                                unwatched_medias.append(media)
                        medias = unwatched_medias

                # Filtering out unreleased items if needed
                if list_config.get("only_released", False):
                    medias = [
                        media
                        for media in medias
                        if media.released and media.released <= dt_util.utcnow()
                    ]

                # Apply sorting
                sort_by = list_config.get("sort_by", "rank")
                sort_order = list_config.get("sort_order", "asc")

                if sort_by == "rating":
                    medias.sort(
                        key=lambda m: m.rating or 0, reverse=(sort_order == "desc")
                    )
                elif sort_order == "desc":
                    medias.reverse()

                # Slicing to max_medias
                medias = medias[: list_config["max_medias"]]

                await gather(
                    *[media.get_more_information(language) for media in medias]
                )
                res[list_config["friendly_name"]] = Medias(medias)

        return {configured_kind: res}

    async def fetch_stats(self):
        # Load data
        data = await self.request("get", f"users/me/stats")

        # Flatten data dictionary
        stats = {}
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    stats[f"{key}_{sub_key}"] = sub_value
            else:
                stats[key] = value

        return stats

    async def fetch_anticipated(self, path: str, limit: int, ignore_collected: bool):
        return await self.request(
            "get",
            f"{path}/anticipated?limit={limit}&ignore_collected={ignore_collected}",
        )

    async def fetch_anticipated_medias(self, configured_kinds: list[TraktKind]):
        kinds = [kind for kind in configured_kinds if kind in BASIC_KINDS]

        language = self.configuration.get_language()
        data = await gather(
            *[
                self.fetch_anticipated(
                    kind.value.path,
                    self.configuration.get_max_medias(
                        kind.value.identifier, "anticipated"
                    ),
                    self.configuration.get_exclude_collected(
                        kind.value.identifier, "anticipated"
                    ),
                )
                for kind in kinds
            ]
        )

        res = {}

        for trakt_kind, raw_medias in zip(kinds, data):
            if raw_medias is not None:
                medias = [
                    trakt_kind.value.model.from_trakt(
                        media[trakt_kind.value.identifier]
                    )
                    for media in raw_medias
                ]
                await gather(
                    *[media.get_more_information(language) for media in medias]
                )
                res[trakt_kind] = Medias(medias)

        return res

    async def retrieve_data(self):
        async with timeout(1800):

            sources = []
            coroutine_sources_data = []

            source_function = {
                "upcoming": lambda kinds: self.fetch_upcomings(
                    configured_kinds=kinds,
                    all_medias=False,
                ),
                "all_upcoming": lambda kinds: self.fetch_upcomings(
                    configured_kinds=kinds,
                    all_medias=True,
                ),
                "recommendation": lambda kinds: self.fetch_recommendations(
                    configured_kinds=kinds,
                ),
                "anticipated": lambda kinds: self.fetch_anticipated_medias(
                    configured_kinds=kinds,
                ),
                "next_to_watch": lambda kinds: self.fetch_next_to_watch_medias(
                    configured_kinds=kinds,
                ),
                "lists": lambda: self.fetch_lists(
                    configured_kind=TraktKind.LIST,
                ),
                "stats": lambda: self.fetch_stats(),
            }

            """Configure sources dependant on kinds"""
            for source in [
                "upcoming",
                "all_upcoming",
                "recommendation",
                "anticipated",
                "next_to_watch",
            ]:
                if self.configuration.source_exists(source):
                    sources.append(source)
                    kinds = self.configuration.get_kinds(source)
                    coroutine_sources_data.append(source_function.get(source)(kinds))

            """Configure other sources"""
            for source in [
                "lists",
                "stats",
            ]:
                if self.configuration.source_exists(source):
                    sources.append(source)
                    coroutine_sources_data.append(source_function.get(source)())

            sources_data = await gather(*coroutine_sources_data)

            return {
                source: source_data
                for source, source_data in zip(sources, sources_data)
            }
