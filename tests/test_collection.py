import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from custom_components.trakt_tv.apis.trakt import TraktApi
from custom_components.trakt_tv.const import DOMAIN
from custom_components.trakt_tv.models.kind import TraktKind
from custom_components.trakt_tv.models.media import Identifiers, Medias, Movie, Show
from custom_components.trakt_tv.sensor import async_setup_entry


def collection_item(identifier, trakt_id):
    media = {
        "title": f"Title {trakt_id}",
        "ids": {"trakt": trakt_id},
    }
    if identifier == "movie":
        media["released"] = "2020-01-01T00:00:00.000Z"
    else:
        media["first_aired"] = "2020-01-01T00:00:00.000Z"
    return {identifier: media}


def collection_hass(movie_max=20, show_max=20):
    return SimpleNamespace(
        data={
            DOMAIN: {
                "configuration": {
                    "language": "en",
                    "timezone": "UTC",
                    "sensors": {
                        "collection": {
                            "movie": {"max_medias": movie_max},
                            "show": {"max_medias": show_max},
                        }
                    },
                }
            }
        }
    )


def test_collection_urls_pagination_limit_and_coordinator_data():
    hass = collection_hass(movie_max=101, show_max=101)
    api = TraktApi.__new__(TraktApi)
    api.hass = hass

    responses = {
        "sync/collection/movies?extended=full&page=1&limit=100": [
            collection_item("movie", trakt_id) for trakt_id in range(1, 101)
        ],
        "sync/collection/movies?extended=full&page=2&limit=1": [
            collection_item("movie", 101)
        ],
        "sync/collection/shows?extended=full&page=1&limit=100": [
            collection_item("show", trakt_id) for trakt_id in range(1, 101)
        ],
        "sync/collection/shows?extended=full&page=2&limit=1": [
            collection_item("show", 101)
        ],
    }

    async def request(method, url):
        assert method == "get"
        return responses[url]

    api.request = AsyncMock(side_effect=request)

    with patch.object(Movie, "get_more_information", new=AsyncMock()), patch.object(
        Show, "get_more_information", new=AsyncMock()
    ):
        coordinator = SimpleNamespace(data=asyncio.run(api.retrieve_data()))

    assert [call.args[1] for call in api.request.await_args_list] == list(responses)
    assert len(coordinator.data["collection"][TraktKind.MOVIE].items) == 101
    assert len(coordinator.data["collection"][TraktKind.SHOW].items) == 101


def test_collection_empty_responses():
    hass = collection_hass()
    api = TraktApi.__new__(TraktApi)
    api.hass = hass
    api.request = AsyncMock(return_value=[])

    coordinator = SimpleNamespace(data=asyncio.run(api.retrieve_data()))

    assert api.request.await_count == 2
    assert coordinator.data["collection"][TraktKind.MOVIE].items == []
    assert coordinator.data["collection"][TraktKind.SHOW].items == []


def test_collection_entities_are_created_and_keep_api_order():
    hass = collection_hass(movie_max=2, show_max=2)
    movie_ids = [2, 1]
    show_ids = [4, 3]
    released = datetime(2020, 1, 1, tzinfo=timezone.utc)
    coordinator = SimpleNamespace(
        data={
            "collection": {
                TraktKind.MOVIE: Medias(
                    [
                        Movie(
                            name=f"Movie {trakt_id}",
                            ids=Identifiers(trakt_id, None, None, None, None),
                            released=released,
                        )
                        for trakt_id in movie_ids
                    ]
                ),
                TraktKind.SHOW: Medias(
                    [
                        Show(
                            name=f"Show {trakt_id}",
                            ids=Identifiers(trakt_id, None, None, None, None),
                            released=released,
                        )
                        for trakt_id in show_ids
                    ]
                ),
            }
        }
    )
    hass.data[DOMAIN]["instances"] = {"coordinator": coordinator}
    config_entry = SimpleNamespace(entry_id="entry")
    entities = []

    asyncio.run(async_setup_entry(hass, config_entry, entities.extend))

    collection_entities = [
        entity for entity in entities if entity.source == "collection"
    ]
    assert [entity.trakt_kind for entity in collection_entities] == [
        TraktKind.MOVIE,
        TraktKind.SHOW,
    ]
    assert [item["title"] for item in collection_entities[0].data[1:]] == [
        "Movie 2",
        "Movie 1",
    ]
    assert [item["title"] for item in collection_entities[1].data[1:]] == [
        "Show 4",
        "Show 3",
    ]
