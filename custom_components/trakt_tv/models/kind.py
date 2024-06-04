from dataclasses import dataclass
from enum import Enum

from .media import Media, Movie, Show


@dataclass
class CalendarInformation:
    identifier: str
    name: str
    path: str
    model: Media


class TraktKind(Enum):
    SHOW = CalendarInformation("show", "Shows", "shows", Show)
    NEW_SHOW = CalendarInformation("new_show", "New Shows", "shows/new", Show)
    PREMIERE = CalendarInformation("premiere", "Premieres", "shows/premieres", Show)
    MOVIE = CalendarInformation("movie", "Movies", "movies", Movie)
    DVD = CalendarInformation("dvd", "DVD", "dvd", Movie)
    NEXT_TO_WATCH_ALL = CalendarInformation("all", "All", "shows", Show)
    NEXT_TO_WATCH_AIRED = CalendarInformation("only_aired", "Only Aired", "shows", Show)
    NEXT_TO_WATCH_UPCOMING = CalendarInformation(
        "only_upcoming", "Only Upcoming", "shows", Show
    )
    ANTICIPATED_MOVIE = CalendarInformation("anticipated_movie", "Anticipated Movies", "movies/anticipated", Movie)
    ANTICIPATED_SHOW = CalendarInformation("anticipated_show", "Anticipated Shows", "shows/anticipated", Show)

    @classmethod
    def from_string(cls, string):
        try:
            return cls[string.upper()]
        except KeyError:
            raise ValueError(f"No enum member found for '{string}'")


UPCOMING_KINDS = [
    TraktKind.SHOW,
    TraktKind.NEW_SHOW,
    TraktKind.PREMIERE,
    TraktKind.MOVIE,
    TraktKind.DVD,
]

BASIC_KINDS = [
    TraktKind.SHOW,
    TraktKind.MOVIE,
]

NEXT_TO_WATCH_KINDS = [
    TraktKind.NEXT_TO_WATCH_ALL,
    TraktKind.NEXT_TO_WATCH_AIRED,
    TraktKind.NEXT_TO_WATCH_UPCOMING,
]

ANTICIPATED_KINDS = [
    TraktKind.ANTICIPATED_MOVIE,
    TraktKind.ANTICIPATED_SHOW,
]
