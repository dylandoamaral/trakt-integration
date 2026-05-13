import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from custom_components.trakt_tv.apis.trakt import TraktApi
from custom_components.trakt_tv.const import DOMAIN
from custom_components.trakt_tv.sensor import (
    TraktNowPlayingSensor,
    _seconds_left_from_payload,
)


class MockResponse:
    def __init__(self, status: int, text: str = "", headers: dict | None = None):
        self.status = status
        self._text = text
        self.headers = headers or {}

    @property
    def ok(self):
        return 200 <= self.status < 300

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _make_api(response):
    hass = SimpleNamespace(data={DOMAIN: {"configuration": {"client_id": "client"}}})
    oauth_session = SimpleNamespace(valid_token=True, token={"access_token": "token"})
    web_session = SimpleNamespace(request=AsyncMock(return_value=response))
    return TraktApi(websession=web_session, oauth_session=oauth_session, hass=hass)


def test_fetch_now_playing_returns_none_for_204():
    api = _make_api(MockResponse(status=204, text=""))
    answer = asyncio.run(api.fetch_now_playing())
    assert answer is None


def test_fetch_now_playing_returns_payload_without_tmdb():
    payload = {"type": "movie", "movie": {"title": "Test", "ids": {}}}
    api = _make_api(
        MockResponse(
            status=200, text='{"type": "movie", "movie": {"title": "Test", "ids": {}}}'
        )
    )
    answer = asyncio.run(api.fetch_now_playing())
    assert answer is not None
    assert answer["type"] == "movie"
    assert answer["movie"]["title"] == "Test"
    # No tmdb id means no artwork enrichment
    assert "artwork" not in answer


def test_seconds_left_from_payload():
    future = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload = {"expires_at": future.isoformat().replace("+00:00", "Z")}
    seconds = _seconds_left_from_payload(payload)
    assert seconds is not None
    assert 0 < seconds <= 600


def test_seconds_left_handles_missing_expires():
    assert _seconds_left_from_payload({}) is None


def test_seconds_left_handles_invalid_value():
    assert _seconds_left_from_payload({"expires_at": "not-a-date"}) is None


def test_seconds_left_clamps_to_zero():
    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    payload = {"expires_at": past.isoformat().replace("+00:00", "Z")}
    assert _seconds_left_from_payload(payload) == 0


class _StubCoordinator:
    def __init__(self, data):
        self.data = data


def _make_now_playing_sensor(payload):
    coordinator = _StubCoordinator(payload)
    config_entry = SimpleNamespace(entry_id="entry-1")
    sensor = TraktNowPlayingSensor(
        hass=SimpleNamespace(data={}),
        config_entry=config_entry,
        coordinator=coordinator,
    )
    return sensor


def test_now_playing_sensor_idle_when_payload_none():
    sensor = _make_now_playing_sensor(None)
    assert sensor.state == "Idle"
    assert sensor.extra_state_attributes == {}


def test_now_playing_sensor_movie_state():
    payload = {"type": "movie", "movie": {"title": "Dune"}}
    sensor = _make_now_playing_sensor(payload)
    assert sensor.state == "Dune"


def test_now_playing_sensor_episode_state():
    payload = {
        "type": "episode",
        "show": {"title": "Foundation"},
        "episode": {"season": 2, "number": 4},
    }
    sensor = _make_now_playing_sensor(payload)
    assert sensor.state == "Foundation - S02E04"


def test_now_playing_sensor_idle_for_unknown_type():
    sensor = _make_now_playing_sensor({"type": "something"})
    assert sensor.state == "Idle"


def test_now_playing_sensor_attributes_include_artwork_and_seconds_left():
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    payload = {
        "type": "movie",
        "movie": {"title": "Dune"},
        "expires_at": future.isoformat().replace("+00:00", "Z"),
        "artwork": {
            "poster": "https://image.tmdb.org/p1.jpg",
            "fanart": "https://image.tmdb.org/f1.jpg",
        },
    }
    sensor = _make_now_playing_sensor(payload)
    attrs = sensor.extra_state_attributes
    assert attrs["poster"] == "https://image.tmdb.org/p1.jpg"
    assert attrs["fanart"] == "https://image.tmdb.org/f1.jpg"
    assert attrs["entity_picture"] == attrs["poster"]
    assert 0 < attrs["seconds_left"] <= 300
    assert attrs["data"] is payload
