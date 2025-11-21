from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .media import Media, Movie, Show


@dataclass
class CalendarInformation:
    identifier: str
    name: str | None
    path: str
    model: Media
    unit: Optional[str] = None


class TraktKind(Enum):
    SHOW = CalendarInformation("show", "Shows", "shows", Show)
    NEW_SHOW = CalendarInformation("new_show", "New Shows", "shows/new", Show)
    PREMIERE = CalendarInformation("premiere", "Premieres", "shows/premieres", Show)
    MOVIE = CalendarInformation("movie", "Movies", "movies", Movie)
    DVD = CalendarInformation("dvd", "DVD", "dvd", Movie)
    NEXT_TO_WATCH_ALL = CalendarInformation("next_to_watch_all", "All", "shows", Show)
    NEXT_TO_WATCH_AIRED = CalendarInformation(
        "next_to_watch_aired", "Only Aired", "shows", Show
    )
    NEXT_TO_WATCH_UPCOMING = CalendarInformation(
        "next_to_watch_upcoming", "Only Upcoming", "shows", Show
    )
    LIST = CalendarInformation("lists", None, "lists/{list_id}/items", Media, "medias")

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
