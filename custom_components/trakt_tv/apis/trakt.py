"""API for TraktTV bound to Home Assistant OAuth."""
import json
import logging
import math
from asyncio import gather
from datetime import datetime, timedelta

from aiohttp import ClientResponse, ClientSession
from async_timeout import timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from custom_components.trakt_tv.utils import compute_calendar_args, split

from ..configuration import Configuration
from ..const import API_HOST, DOMAIN
from ..models.kind import TraktKind
from ..models.media import Medias

LOGGER = logging.getLogger(__name__)


class TraktApi:
    """Provide TraktTV authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: OAuth2Session,
        hass: HomeAssistant,
    ):
        """Initialize TraktTV auth."""
        self.web_session = websession
        self.host = API_HOST
        self.oauth_session = oauth_session
        self.hass = hass

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if not self.oauth_session.valid_token:
            await self.oauth_session.async_ensure_token_valid()

        return self.oauth_session.token["access_token"]

    async def request(self, method, url, **kwargs) -> ClientResponse:
        """Make a request."""
        access_token = await self.async_get_access_token()
        client_id = self.hass.data[DOMAIN]["configuration"]["client_id"]
        headers = {
            **kwargs.get("headers", {}),
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "trakt-api-version": "2",
            "trakt-api-key": client_id,
        }

        return await self.web_session.request(
            method,
            f"{self.host}/{url}",
            **kwargs,
            headers=headers,
        )

    async def fetch_calendar(self, path, from_date, nb_days):
        return await self.request("get", f"calendars/{path}/{from_date}/{nb_days}")

    async def fetch_upcoming(self, trakt_kind: TraktKind):
        """
        Fetch the calendar of the user trakt account based on the trak_type containing
        the calendar type.

        Since the maximum number of days to fetch using trakt API is 33 days, we have to
        make multiple API calls if we want to retrieve a larger amount of time.

        :param trak_type: The TraktKind describing which calendar we should request
        """
        configuration = Configuration(data=self.hass.data)
        path = trakt_kind.value.path
        identifier = trakt_kind.value.identifier

        if not configuration.identifier_exists(identifier):
            return None

        configuration = Configuration(data=self.hass.data)
        days_to_fetch = configuration.get_days_to_fetch(identifier)
        language = configuration.get_language()

        calendar_args = compute_calendar_args(days_to_fetch, 33)

        responses = await gather(
            *[self.fetch_calendar(path, args[0], args[1]) for args in calendar_args]
        )
        texts = await gather(*[response.text() for response in responses])
        data = [media for medias in texts for media in json.loads(medias)]
        medias = [trakt_kind.value.model.from_trakt(movie) for movie in data]
        await gather(*[media.get_more_information(language) for media in medias])

        return trakt_kind, Medias(medias)

    async def retrieve_data(self):
        async with timeout(60):
            data = await gather(*[self.fetch_upcoming(kind) for kind in TraktKind])
            data = filter(lambda x: x is not None, data)
            return {trakt_kind: medias for trakt_kind, medias in data}
