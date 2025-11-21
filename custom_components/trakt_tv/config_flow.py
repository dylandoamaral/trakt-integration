"""Config flow for Trakt (OAuth via Application Credentials)."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.selector import (
    LanguageSelector,
    LanguageSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from custom_components.trakt_tv.utils import is_int_like

from .const import (
    CONF_LANGUAGE,
    CONF_SENSORS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    LANGUAGE_CODES,
    S_LIST,
)
from .schema_meta import (
    build_list_form_schema,
    build_options_schema,
    get_menu_labels,
    parse_list_form,
    parse_options_submission,
)

_LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle the OAuth2 flow with Application Credentials."""

    VERSION = 1
    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    _stored_tokens: dict | None = None
    _reauth_entry: config_entries.ConfigEntry | None = None

    @property
    def logger(self) -> logging.Logger:
        return _LOGGER

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Kick off OAuth immediately using the built-in credentials picker."""
        return await self.async_step_pick_implementation()

    async def async_oauth_create_entry(self, data: dict) -> FlowResult:
        """Store tokens, then collect profile settings."""
        if self.source == config_entries.SOURCE_REAUTH and self._reauth_entry:
            return self.async_update_reload_and_abort(self._reauth_entry, data=data)
        self._stored_tokens = data
        return await self.async_step_profile()

    async def async_step_profile(self, user_input=None) -> FlowResult:
        """Collect options after OAuth."""
        if user_input is not None:
            # Get the credentials name from the OAuth2 implementation
            cred_name = getattr(self.flow_impl, "name", None)

            # Create the config entry; sensors live in options via OptionsFlow
            title = f"Trakt ({cred_name})" if cred_name else "Trakt"
            return self.async_create_entry(
                title=title,
                data={
                    **(self._stored_tokens or {}),
                    CONF_LANGUAGE: user_input[CONF_LANGUAGE],
                    CONF_UPDATE_INTERVAL: int(
                        user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                    ),
                },
            )

        # Set defaults
        default_lang = self.hass.config.language or "en"
        default_minutes = DEFAULT_UPDATE_INTERVAL

        # Set up form
        fields = {
            vol.Required(CONF_LANGUAGE, default=default_lang): LanguageSelector(
                LanguageSelectorConfig(
                    native_name=True,  # show names in their own language
                    languages=LANGUAGE_CODES,
                )
            ),
        }

        if self.show_advanced_options:
            fields[vol.Required(CONF_UPDATE_INTERVAL, default=default_minutes)] = (
                NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=1440, step=1, mode=NumberSelectorMode.BOX
                    )
                )
            )

        return self.async_show_form(step_id="profile", data_schema=vol.Schema(fields))

    async def async_step_import(self, import_config: dict) -> FlowResult:
        """Create entry without tokens; async_setup_entry will raise ConfigEntryAuthFailed → HA starts reauth."""
        return self.async_create_entry(
            title="Trakt",
            data={
                CONF_LANGUAGE: import_config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            },
            options=import_config.get("sensors", {})
            and {"sensors": import_config["sensors"]}
            or {},
        )

    async def async_step_reauth(self, entry_data) -> FlowResult:
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm", data_schema=vol.Schema({})
            )
        return await self.async_step_pick_implementation()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TraktOptionsFlow(config_entry)


# -------------------------
# Options Flow
# -------------------------
class TraktOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry):
        self.entry = entry
        self._opts: dict = dict(entry.options or {})
        self._sensors: dict = dict(self._opts.get(CONF_SENSORS, {}))
        self._lists: list[dict] = list(self._sensors.get(S_LIST, []) or [])
        self._edit_index: int | None = None

    # ---------- Top menu ----------
    async def async_step_init(self, user_input=None) -> FlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=get_menu_labels("init"),
        )

    # ---------- Sensors branch (sections built from schema_meta) ----------
    async def async_step_sensors(self, user_input=None) -> FlowResult:
        if user_input is not None:
            sensors = parse_options_submission(user_input)
            sensors[S_LIST] = self._lists  # keep lists
            self._opts[CONF_SENSORS] = sensors
            return await self.async_step_init()

        current = {k: v for k, v in self._sensors.items() if k != S_LIST}
        schema = build_options_schema(current)
        return self.async_show_form(step_id="sensors", data_schema=schema)

    # ---------- Lists menu ----------
    async def async_step_lists_menu(self, user_input=None) -> FlowResult:
        # Rehydrate in case sensors step ran
        self._lists = list(
            (self._opts.get(CONF_SENSORS, {}) or {}).get(S_LIST, self._lists) or []
        )
        return self.async_show_menu(
            step_id="lists_menu",
            menu_options=get_menu_labels("lists_menu"),
        )

    # ---------- Add list (form from schema_meta) ----------
    async def async_step_lists_add(self, user_input=None) -> FlowResult:
        if user_input is not None:
            entry = parse_list_form(user_input)

            # Ensure unique friendly_name
            if any(e["friendly_name"] == entry["friendly_name"] for e in self._lists):
                return self.async_show_form(
                    step_id="lists_add",
                    data_schema=build_list_form_schema(),
                    errors={"friendly_name": "name_exists"},
                )

            # Validate list_id (slug or numeric id)
            if not entry["private_list"] and not is_int_like(entry["list_id"]):
                return self.async_show_form(
                    step_id="lists_add",
                    data_schema=build_list_form_schema(
                        current=user_input
                    ),  # save input values
                    errors={
                        "list_id": "numeric_required_for_public"
                    },  # key for translations
                )

            # Add it
            self._lists.append(entry)
            self._write_lists()
            return await self.async_step_lists_menu()

        return self.async_show_form(
            step_id="lists_add", data_schema=build_list_form_schema()
        )

    # ---------- Pick which list to edit ----------
    async def async_step_lists_edit_pick(self, user_input=None) -> FlowResult:
        if not self._lists:
            return await self.async_step_lists_menu()

        options = [e["friendly_name"] for e in self._lists]
        schema = vol.Schema(
            {
                vol.Required("pick"): SelectSelector(
                    SelectSelectorConfig(
                        options=options, mode=SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )

        if user_input is not None:
            name = user_input["pick"]
            self._edit_index = next(
                (i for i, e in enumerate(self._lists) if e["friendly_name"] == name),
                None,
            )
            return await self.async_step_lists_edit()

        return self.async_show_form(step_id="lists_edit_pick", data_schema=schema)

    # ---------- Edit list (form from schema_meta) ----------
    async def async_step_lists_edit(self, user_input=None) -> FlowResult:
        if self._edit_index is None or self._edit_index >= len(self._lists):
            return await self.async_step_lists_menu()

        cur = self._lists[self._edit_index]

        if user_input is not None:
            updated = parse_list_form(
                user_input, keep_friendly_name=cur["friendly_name"]
            )

            # Validate list_id (slug or numeric id)
            if not updated["private_list"] and not is_int_like(updated["list_id"]):
                return self.async_show_form(
                    step_id="lists_add",
                    data_schema=build_list_form_schema(
                        current=user_input
                    ),  # save input values
                    errors={
                        "list_id": "numeric_required_for_public"
                    },  # key for translations
                )

            self._lists[self._edit_index] = updated
            self._write_lists()
            self._edit_index = None
            return await self.async_step_lists_menu()

        return self.async_show_form(
            step_id="lists_edit", data_schema=build_list_form_schema(current=cur)
        )

    # ---------- Delete lists ----------
    async def async_step_lists_delete(self, user_input=None) -> FlowResult:
        if not self._lists:
            return await self.async_step_lists_menu()

        options = [e["friendly_name"] for e in self._lists]
        schema = vol.Schema(
            {
                vol.Required("names", default=[]): SelectSelector(
                    SelectSelectorConfig(
                        options=options, multiple=True, mode=SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )

        if user_input is not None:
            to_remove = set(user_input["names"])
            self._lists = [
                e for e in self._lists if e["friendly_name"] not in to_remove
            ]
            self._write_lists()
            return await self.async_step_lists_menu()

        return self.async_show_form(step_id="lists_delete", data_schema=schema)

    # ---------- Finish / save ----------
    async def async_step_finish(self, user_input=None) -> FlowResult:
        sensors = dict(self._opts.get(CONF_SENSORS, {}))
        sensors[S_LIST] = self._lists
        self._opts[CONF_SENSORS] = sensors
        return self.async_create_entry(title="", data=self._opts)

    # ---------- Helpers ----------
    def _write_lists(self) -> None:
        sensors = dict(self._opts.get(CONF_SENSORS, {}))
        sensors[S_LIST] = self._lists
        self._opts[CONF_SENSORS] = sensors
