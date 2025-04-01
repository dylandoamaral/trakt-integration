from typing import Any, Dict, Optional

import aiohttp

from custom_components.trakt_tv.const import TMDB_HOST, TMDB_TOKEN


async def get_media_data(
    kind: str, prefix: str, tmbd_id: int, language: str
) -> Dict[str, Any]:
    """
    Get information from TMDB about a kind of media.

    :param kind: The kind of media
    :param prefix: The route prefix
    :param tmbd_id: The ID of the media
    :param language: The favorite language of the user
    """
    url = f"{TMDB_HOST}/3/{kind}/{tmbd_id}{prefix}?api_key={TMDB_TOKEN}&language={language}"
    async with aiohttp.request("GET", url) as response:
        return await response.json()


async def get_movie_data(tmbd_id: int, language: str) -> Dict[str, Any]:
    """
    Get information from TMDB about a movie.

    :param tmbd_id: The ID of the movie
    :param language: The favorite language of the user
    """
    return await get_media_data("movie", "", tmbd_id, language)


async def get_show_data(tmbd_id: int, language: str) -> Dict[str, Any]:
    """
    Get information from TMDB about a show.

    :param tmbd_id: The ID of the show
    :param language: The favorite language of the user
    """
    return await get_media_data("tv", "", tmbd_id, language)


def _extract_trailer_from_data(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract trailer data from video data.
    """
    videos = data.get("results", {})

    for video in videos:
        site = video.get("site")
        _type = video.get("type")
        key = video.get("key")

        if site == "YouTube" and _type == "Trailer" and key is not None:
            return f"https://www.youtube.com/watch?v={key}"

    return None


async def get_movie_trailer(tmbd_id: int, language: str) -> Optional[str]:
    """
    Get trailer url from TMDB about a movie.

    :param tmbd_id: The ID of the movie
    :param language: The favorite language of the user
    """
    data = await get_media_data("movie", "/videos", tmbd_id, language)
    return _extract_trailer_from_data(data)


async def get_show_trailer(tmbd_id: int, language: str) -> Optional[str]:
    """
    Get trailer url from TMDB about a show.

    :param tmbd_id: The ID of the show
    :param language: The favorite language of the user
    """
    data = await get_media_data("tv", "/videos", tmbd_id, language)
    return _extract_trailer_from_data(data)
