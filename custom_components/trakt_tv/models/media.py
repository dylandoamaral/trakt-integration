from abc import ABC, abstractmethod, abstractstaticmethod
from asyncio import gather
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from custom_components.trakt_tv.apis.tmdb import (
    get_movie_data,
    get_movie_trailer,
    get_show_data,
    get_show_trailer,
)
from custom_components.trakt_tv.utils import parse_utc_date

first_item = {
    "title_default": "$title",
    "line1_default": "$episode",
    "line2_default": "$release",
    "line3_default": "$rating - $runtime",
    "line4_default": "$number - $studio",
    "icon": "mdi:arrow-down-bold",
}


@dataclass
class Identifiers:
    trakt: Optional[int]
    slug: Optional[str]
    tvdb: Optional[int]
    imdb: Optional[str]
    tmdb: Optional[int]

    @staticmethod
    def from_trakt(data) -> "Identifiers":
        """
        Create identifiers from trakt api by providing the base root of the ids.
        """
        ids = data["ids"]

        return Identifiers(
            trakt=int(ids["trakt"]) if ids.get("trakt") else None,
            slug=ids.get("slug"),
            tvdb=int(ids["tvdb"]) if ids.get("tvdb") else None,
            imdb=ids.get("imdb"),
            tmdb=int(ids["tmdb"]) if ids.get("tmdb") else None,
        )


@dataclass
class Media(ABC):
    name: str
    ids: Identifiers

    @abstractstaticmethod
    def from_trakt(data) -> "Media":
        """
        Create a model from trakt api.
        """

    @abstractmethod
    def to_homeassistant(self) -> Dict[str, Any]:
        """
        Convert the Media to upcoming data.

        :return: The dictionary containing all necessary information for upcoming media
                 card
        """

    def common_information(self) -> Dict[str, Any]:
        """
        Common upcoming information.

        :return: The dictionary containing all common information for all kind of medias
        """
        default = {
            "title": self.name,
            "poster": self.poster,
            "fanart": self.fanart,
            "genres": self.genres,
            "rating": self.rating,
            "rating_trakt": self.rating_trakt,
            "studio": self.studio,
        }

        return {k: v for k, v in default.items() if v is not None}

    async def get_more_information(self, language: str):
        """
        Get information from other API calls to complete the trakt movie.

        :param language: The favorite language of the user
        """


@dataclass
class Movie(Media):
    """
    An upcoming movie
    """

    genres: List[str] = field(default_factory=list)
    trailer: Optional[str] = None
    summary: Optional[str] = None
    poster: Optional[str] = None
    fanart: Optional[str] = None
    rating: Optional[int] = None
    runtime: Optional[int] = None
    studio: Optional[str] = None
    released: Optional[datetime] = None  # This one is actually mandatory
    rank: Optional[int] = None
    listed_at: Optional[datetime] = None
    rating_trakt: Optional[int] = None

    @staticmethod
    def from_trakt(data) -> "Movie":
        """
        Create a Movie from trakt api.
        """
        movie = data if data.get("title") else data["movie"]

        return Movie(
            name=movie["title"],
            released=parse_utc_date(data.get("released")),
            ids=Identifiers.from_trakt(movie),
            rank=data.get("rank"),
            listed_at=parse_utc_date(data.get("listed_at")),
            rating_trakt=movie.get("rating"),
        )

    async def get_more_information(self, language: str):
        """
        Get information from other API calls to complete the trakt movie.

        :param language: The favorite language of the user
        """
        data, trailer = await gather(
            get_movie_data(self.ids.tmdb, language),
            get_movie_trailer(self.ids.tmdb, language),
        )

        if title := data.get("title"):
            self.name = title
        if trailer:
            self.trailer = trailer
        if summary := data.get("overview"):
            self.summary = summary
        if poster := data.get("poster_path"):
            self.poster = f"https://image.tmdb.org/t/p/w500{poster}"
        if fanart := data.get("backdrop_path"):
            self.fanart = f"https://image.tmdb.org/t/p/w500{fanart}"
        if genres := data.get("genres"):
            self.genres = [genre["name"] for genre in genres]
        if vote_average := data.get("vote_average"):
            if vote_average != 0:
                self.rating = vote_average
        if runtime := data.get("runtime"):
            self.runtime = runtime
        if production_companies := data.get("production_companies"):
            self.studio = production_companies[0].get("name")
        if not self.released:
            if data.get("release_date"):
                self.released = parse_utc_date(data.get("release_date"))
            else:
                self.released = datetime.min

    def to_homeassistant(self) -> Dict[str, Any]:
        """
        Convert the Movie to upcoming data.

        :return: The dictionary containing all necessary information for upcoming media
                 card
        """
        default = {
            **self.common_information(),
            "runtime": self.runtime,
            "release": "$day, $date $time",
            "airdate": self.released.replace(tzinfo=None).isoformat() + "Z",
            "ids": asdict(self.ids),
        }

        if self.ids.slug is not None:
            default["deep_link"] = f"https://trakt.tv/movies/{self.ids.slug}"
        if self.trailer is not None:
            default["trailer"] = self.trailer
        if self.summary is not None:
            default["summary"] = self.summary

        return default


@dataclass
class Episode:
    number: int
    season: int
    title: str
    ids: Identifiers

    @staticmethod
    def from_trakt(data) -> "Episode":
        """
        Create an Episode from trakt api.
        """
        episode = data

        return Episode(
            number=episode["number"],
            season=episode["season"],
            title=episode["title"],
            ids=Identifiers.from_trakt(episode),
        )


@dataclass
class Show(Media):
    trailer: Optional[str] = None
    summary: Optional[str] = None
    poster: Optional[str] = None
    fanart: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    rating: Optional[int] = None
    studio: Optional[str] = None
    episode: Optional[Episode] = None
    released: Optional[datetime] = None
    runtime: Optional[int] = None
    rank: Optional[int] = None
    listed_at: Optional[datetime] = None
    rating_trakt: Optional[int] = None
    last_activity_date: Optional[datetime] = None

    @staticmethod
    def from_trakt(data) -> "Show":
        """
        Create a Show from trakt api.
        """
        show = data if data.get("title") else data["show"]

        episode = Episode.from_trakt(data["episode"]) if data.get("episode") else None

        return Show(
            name=show["title"],
            ids=Identifiers.from_trakt(show),
            released=parse_utc_date(data.get("first_aired")),
            episode=episode,
            rank=data.get("rank"),
            listed_at=parse_utc_date(data.get("listed_at")),
            runtime=show.get("runtime"),
            rating_trakt=show.get("rating"),
            last_activity_date=parse_utc_date(data.get("last_watched_at")),
        )

    async def get_more_information(self, language: str):
        """
        Get information from other API calls to complete the trakt movie.

        :param language: The favorite language of the user
        """
        data, trailer = await gather(
            get_show_data(self.ids.tmdb, language),
            get_show_trailer(self.ids.tmdb, language),
        )

        if title := data.get("title"):
            self.name = title
        if trailer:
            self.trailer = trailer
        if summary := data.get("overview"):
            self.summary = summary
        if poster := data.get("poster_path"):
            self.poster = f"https://image.tmdb.org/t/p/w500{poster}"
        if fanart := data.get("backdrop_path"):
            self.fanart = f"https://image.tmdb.org/t/p/w500{fanart}"
        if genres := data.get("genres"):
            self.genres = [genre["name"] for genre in genres]
        if vote_average := data.get("vote_average"):
            if vote_average != 0:
                self.rating = vote_average
        if networks := data.get("networks"):
            self.studio = networks[0].get("name")
        if not self.released:
            if data.get("first_air_date"):
                self.released = datetime.fromisoformat(data["first_air_date"])
            else:
                # If we really can't find the release date, we set it to the minimum date
                self.released = datetime.min

    def to_homeassistant(self) -> Dict[str, Any]:
        """
        Convert the Show to upcoming data.

        :return: The dictionary containing all necessary information for upcoming media
                 card
        """
        default = {
            **self.common_information(),
            "release": "$day, $date $time",
            "airdate": self.released.replace(tzinfo=None).isoformat() + "Z",
            "ids": asdict(self.ids),
        }

        if self.episode:
            season = self.episode.season
            season = season if season >= 10 else f"0{season}"

            episode = self.episode.number
            episode = episode if episode >= 10 else f"0{episode}"

            default["episode"] = self.episode.title
            default["number"] = f"S{season}E{episode}"

            if self.ids.slug is not None:
                deep_link = f"https://trakt.tv/shows/{self.ids.slug}/seasons/{season}/episodes/{episode}"
                default["deep_link"] = deep_link
        else:
            if self.ids.slug is not None:
                default["deep_link"] = f"https://trakt.tv/shows/{self.ids.slug}"

        if self.trailer is not None:
            default["trailer"] = self.trailer
        if self.summary is not None:
            default["summary"] = self.summary

        return default


@dataclass
class Medias:
    items: List[Media]

    def to_homeassistant(self, sort_by="released", sort_order="asc") -> Dict[str, Any]:
        """
        Convert the List of medias to recommendation data.

        :return: The dictionary containing all necessary information for upcoming media
                 card
        """
        medias = sorted(
            self.items,
            key=lambda media: getattr(media, sort_by),
            reverse=sort_order == "desc",
        )
        medias = [media.to_homeassistant() for media in medias]
        return [first_item] + medias

    @staticmethod
    def trakt_to_class(
        trakt_type: str,
    ) -> Type[Show] | Type[Movie] | Type[Episode] | None:
        type_to_class = {"show": Show, "episode": Show, "movie": Movie}
        return type_to_class.get(trakt_type, None)
