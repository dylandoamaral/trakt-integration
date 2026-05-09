import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from custom_components.trakt_tv.apis.trakt import TraktApi
from custom_components.trakt_tv.const import DOMAIN


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


def test_request_allow_no_content_returns_none_for_204():
    hass = SimpleNamespace(data={DOMAIN: {"configuration": {"client_id": "client"}}})
    oauth_session = SimpleNamespace(valid_token=True, token={"access_token": "token"})
    web_session = SimpleNamespace(
        request=AsyncMock(return_value=MockResponse(status=204, text=""))
    )
    api = TraktApi(websession=web_session, oauth_session=oauth_session, hass=hass)

    answer = asyncio.run(
        api.request("get", "users/me/watching", allow_no_content=True)
    )

    assert answer is None


def test_request_allow_no_content_returns_none_for_empty_body():
    hass = SimpleNamespace(data={DOMAIN: {"configuration": {"client_id": "client"}}})
    oauth_session = SimpleNamespace(valid_token=True, token={"access_token": "token"})
    web_session = SimpleNamespace(
        request=AsyncMock(return_value=MockResponse(status=200, text=""))
    )
    api = TraktApi(websession=web_session, oauth_session=oauth_session, hass=hass)

    answer = asyncio.run(
        api.request("get", "users/me/watching", allow_no_content=True)
    )

    assert answer is None
