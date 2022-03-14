from abc import ABC, abstractmethod, abstractstaticmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from custom_components.trakt_tv.apis.tmdb import get_movie_data, get_show_data

from ..const import UPCOMING_DATA_FORMAT


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
    released: Optional[datetime] = None

    @abstractstaticmethod
    def from_upcoming_trakt(data) -> "Media":
        """
        Create a model from upcoming trakt api.
        """

    @abstractstaticmethod
    def from_recommendation_trakt(data) -> "Media":
        """
        Create a model from upcoming trakt api.
        """

    @abstractmethod
    def to_upcoming(self) -> Dict[str, Any]:
        """
        Convert the Media to upcoming data.

        :return: The dictionary containing all necessary information for upcoming media
                 card
        """

    def common_upcoming_information(self) -> Dict[str, Any]:
        """
        Common upcoming information.

        :return: The dictionary containing all common information for all kind of medias
        """
        default = {
            "title": self.name,
            "release": "$day, $date $time",
            "airdate": self.released.isoformat() + "Z",
            "poster": self.poster,
            "fanart": self.fanart,
            "genres": self.genres,
            "rating": self.rating,
            "studio": self.studio,
        }

        return {k: v for k, v in default.items() if v is not None}

    async def get_more_information(self, language):
        """
        Get information from other API calls to complete the trakt movie.

        :param language: The favorite language of the user
        """


@dataclass
class Movie(Media):
    """
    A movie
    """

    poster: Optional[str] = None
    fanart: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    rating: Optional[int] = None
    runtime: Optional[int] = None
    studio: Optional[str] = None

    @staticmethod
    def from_upcoming_trakt(data) -> "Movie":
        """
        Create a Movie from trakt api.
        """
        movie = data["movie"]

        return Movie(
            name=movie["title"],
            released=datetime.fromisoformat(data["released"]),
            ids=Identifiers.from_trakt(movie),
        )

    @staticmethod
    def from_recommendation_trakt(data) -> "Movie":
        """
        Create a Movie from trakt api.
        """
        movie = data

        return Movie(
            name=movie["title"],
            ids=Identifiers.from_trakt(movie),
        )

    async def get_more_information(self, language):
        """
        Get information from other API calls to complete the trakt movie.

        :param language: The favorite language of the user
        """
        data = await get_movie_data(self.ids.tmdb, language)
        if title := data.get("title"):
            self.name = title
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

    def to_upcoming(self) -> Dict[str, Any]:
        """
        Convert the Movie to upcoming data.

        :return: The dictionary containing all necessary information for upcoming media
                 card
        """
        default = {
            **self.common_upcoming_information(),
            "runtime": self.runtime,
        }

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
        episode = data["episode"]

        return Episode(
            number=episode["number"],
            season=episode["season"],
            title=episode["title"],
            ids=Identifiers.from_trakt(episode),
        )


@dataclass
class Show(Media):
    episode: Optional[Episode] = None
    poster: Optional[str] = None
    fanart: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    rating: Optional[int] = None
    studio: Optional[str] = None

    @staticmethod
    def from_upcoming_trakt(data) -> "Show":
        """
        Create a Show from trakt api.
        """
        show = data["show"]

        return Show(
            name=show["title"],
            released=datetime.strptime(data["first_aired"], UPCOMING_DATA_FORMAT),
            ids=Identifiers.from_trakt(show),
            episode=Episode.from_trakt(data),
        )

    @staticmethod
    def from_recommendation_trakt(data) -> "Show":
        """
        Create a Show from trakt api.
        """
        show = data

        return Show(
            name=show["title"],
            ids=Identifiers.from_trakt(show),
        )

    async def get_more_information(self, language):
        """
        Get information from other API calls to complete the trakt movie.

        :param language: The favorite language of the user
        """
        data = await get_show_data(self.ids.tmdb, language)
        if title := data.get("title"):
            self.name = title
        season = [
            season
            for season in data.get("seasons", [])
            if season["season_number"] == self.episode.season
        ]
        if season:
            poster = season[0]["poster_path"]
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

    def season_number(self) -> Optional[str]:
        if not self.episode:
            return None

        season = self.episode.season
        season = season if season >= 10 else f"0{season}"

        episode = self.episode.number
        episode = episode if episode >= 10 else f"0{episode}"

        return f"S{season}E{episode}"

    def to_upcoming(self) -> Dict[str, Any]:
        """
        Convert the Show to upcoming data.

        :return: The dictionary containing all necessary information for upcoming media
                 card
        """
        default = {
            **self.common_upcoming_information(),
            "episode": self.episode.title,
            "number": self.season_number(),
        }

        return default


@dataclass
class Medias:
    items: List[Media]

    @staticmethod
    def first_item():
        return {
            "title_default": "$title",
            "line1_default": "$episode",
            "line2_default": "$release",
            "line3_default": "$rating - $runtime",
            "line4_default": "$number - $studio",
            "icon": "mdi:arrow-down-bold",
        }

    def to_upcoming(self) -> Dict[str, Any]:
        """
        Convert the List of medias to upcoming data.

        :return: The dictionary containing all necessary information for upcoming media
                 card
        """
        medias = sorted(self.items, key=lambda media: media.released or media.title)
        medias = [media.to_upcoming() for media in medias]
        return [Medias.first_item()] + medias
