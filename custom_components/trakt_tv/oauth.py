"""OAuth2 implementation selection for Trakt."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    LocalOAuth2Implementation,
    LocalOAuth2ImplementationWithPkce,
)

from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN


def build_implementation(
    hass: HomeAssistant, client_id: str, client_secret: str | None
) -> LocalOAuth2Implementation:
    """Return a PKCE implementation, or the classic one for legacy apps with a secret."""
    if client_secret:
        return LocalOAuth2Implementation(
            hass, DOMAIN, client_id, client_secret, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
        )
    # Trakt apps created since October 2026 get no secret and must use PKCE.
    return LocalOAuth2ImplementationWithPkce(
        hass, DOMAIN, client_id, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
    )
