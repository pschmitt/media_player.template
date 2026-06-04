"""Config flow for Media Player Template."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_UNIQUE_ID
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ALBUM_TEMPLATE,
    CONF_ARTIST_TEMPLATE,
    CONF_DURATION_TEMPLATE,
    CONF_MEDIA_TYPE_TEMPLATE,
    CONF_MUTE_SCRIPT,
    CONF_MUTED_TEMPLATE,
    CONF_NEXT_SCRIPT,
    CONF_PAUSE_SCRIPT,
    CONF_PLAY_MEDIA_SCRIPT,
    CONF_PLAY_SCRIPT,
    CONF_POSITION_TEMPLATE,
    CONF_PREVIOUS_SCRIPT,
    CONF_SEEK_SCRIPT,
    CONF_SELECT_SOUND_MODE_SCRIPT,
    CONF_SELECT_SOURCE_SCRIPT,
    CONF_SET_VOLUME_SCRIPT,
    CONF_SOUND_MODE_TEMPLATE,
    CONF_SOURCE_TEMPLATE,
    CONF_STATE_TEMPLATE,
    CONF_STOP_SCRIPT,
    CONF_THUMBNAIL_TEMPLATE,
    CONF_TITLE_TEMPLATE,
    CONF_TURN_OFF_SCRIPT,
    CONF_TURN_ON_SCRIPT,
    CONF_VOLUME_DOWN_SCRIPT,
    CONF_VOLUME_TEMPLATE,
    CONF_VOLUME_UP_SCRIPT,
    DOMAIN,
)

_TEMPLATE_SELECTOR = selector.TemplateSelector()
_TEXT_SELECTOR = selector.TextSelector()
_OPTIONAL_TEMPLATE = selector.TemplateSelector(selector.TemplateSelectorConfig())
_OPTIONAL_TEXT = selector.TextSelector(selector.TextSelectorConfig(multiline=False))

_TEMPLATE_KEYS = (
    CONF_TITLE_TEMPLATE,
    CONF_ARTIST_TEMPLATE,
    CONF_ALBUM_TEMPLATE,
    CONF_THUMBNAIL_TEMPLATE,
    CONF_VOLUME_TEMPLATE,
    CONF_MUTED_TEMPLATE,
    CONF_SOURCE_TEMPLATE,
    CONF_SOUND_MODE_TEMPLATE,
    CONF_POSITION_TEMPLATE,
    CONF_DURATION_TEMPLATE,
    CONF_MEDIA_TYPE_TEMPLATE,
)

_ACTION_KEYS = (
    CONF_PLAY_SCRIPT,
    CONF_PAUSE_SCRIPT,
    CONF_STOP_SCRIPT,
    CONF_NEXT_SCRIPT,
    CONF_PREVIOUS_SCRIPT,
    CONF_VOLUME_UP_SCRIPT,
    CONF_VOLUME_DOWN_SCRIPT,
    CONF_SET_VOLUME_SCRIPT,
    CONF_MUTE_SCRIPT,
    CONF_TURN_ON_SCRIPT,
    CONF_TURN_OFF_SCRIPT,
    CONF_PLAY_MEDIA_SCRIPT,
    CONF_SEEK_SCRIPT,
    CONF_SELECT_SOURCE_SCRIPT,
    CONF_SELECT_SOUND_MODE_SCRIPT,
)


def _opt_template(key: str, data: dict) -> vol.Optional:
    val = data.get(key, "")
    if isinstance(val, dict):
        val = val.get("service", "")
    return vol.Optional(key, default=val or "")


def _template_schema(data: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_STATE_TEMPLATE,
                default=data.get(CONF_STATE_TEMPLATE, ""),
            ): _OPTIONAL_TEMPLATE,
            **{_opt_template(k, data): _OPTIONAL_TEMPLATE for k in _TEMPLATE_KEYS},
        }
    )


def _action_schema(data: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {_opt_template(k, data): _OPTIONAL_TEXT for k in _ACTION_KEYS}
    )


class MediaPlayerTemplateConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for Media Player Template."""

    VERSION = 1

    def __init__(self) -> None:
        self._name: str = ""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._name = user_input["name"]
            await self.async_set_unique_id(self._name.lower())
            self._abort_if_unique_id_configured()
            self._data = {
                "name": self._name,
                CONF_STATE_TEMPLATE: user_input[CONF_STATE_TEMPLATE],
            }
            return await self.async_step_templates()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): _TEXT_SELECTOR,
                    vol.Required(CONF_STATE_TEMPLATE): _TEMPLATE_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_templates(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data.update({k: v for k, v in user_input.items() if v})
            return await self.async_step_actions()

        return self.async_show_form(
            step_id="templates",
            data_schema=vol.Schema(
                {vol.Optional(k, default=""): _OPTIONAL_TEMPLATE for k in _TEMPLATE_KEYS}
            ),
        )

    async def async_step_actions(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data.update({k: v for k, v in user_input.items() if v})
            return self.async_create_entry(title=self._name, data=self._data)

        return self.async_show_form(
            step_id="actions",
            data_schema=vol.Schema(
                {vol.Optional(k, default=""): _OPTIONAL_TEXT for k in _ACTION_KEYS}
            ),
        )

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle import from YAML configuration (migration to config entry)."""
        unique_id = import_data.get(CONF_UNIQUE_ID) or import_data.get("name", "").lower()
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=import_data.get("name", unique_id),
            data=import_data,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MediaPlayerTemplateOptionsFlow(config_entry)


class MediaPlayerTemplateOptionsFlow(OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    def _merged(self) -> dict[str, Any]:
        return {**self._entry.data, **self._entry.options}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=["templates", "actions"],
        )

    async def async_step_templates(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        data = self._merged()
        if user_input is not None:
            updated = {**data}
            updated.update({k: v for k, v in user_input.items()})
            return self.async_create_entry(data=updated)

        return self.async_show_form(
            step_id="templates",
            data_schema=_template_schema(data),
        )

    async def async_step_actions(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        data = self._merged()
        if user_input is not None:
            updated = {**data}
            for k, v in user_input.items():
                if not v:
                    updated.pop(k, None)
                    continue
                existing = data.get(k)
                if isinstance(existing, dict) and v == existing.get("service", ""):
                    updated[k] = existing
                else:
                    updated[k] = v
            return self.async_create_entry(data=updated)

        return self.async_show_form(
            step_id="actions",
            data_schema=_action_schema(data),
        )
