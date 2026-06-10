"""Template for media-player — fork of https://github.com/Sennevds/media_player.template"""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant.components.media_player import (
    DEVICE_CLASSES_SCHEMA,
    DOMAIN as MEDIA_PLAYER_DOMAIN,
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA as MEDIA_PLAYER_PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.components.template import DOMAIN as TEMPLATE_DOMAIN
from homeassistant.components.template.const import CONF_DEFAULT_ENTITY_ID
from homeassistant.components.template.schemas import (
    TEMPLATE_ENTITY_AVAILABILITY_SCHEMA_LEGACY,
)
from homeassistant.components.template.template_entity import TemplateEntity
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    CONF_DEVICE_CLASS,
    CONF_ENTITY_PICTURE_TEMPLATE,
    CONF_ICON_TEMPLATE,
    CONF_NAME,
    CONF_STATE,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import TemplateError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import TrackTemplate, async_track_template_result
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    AddEntitiesCallback,
)
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.util.dt as dt_util

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

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Legacy YAML platform schema (unchanged from upstream for compatibility)
# ---------------------------------------------------------------------------

LEGACY_FIELDS = {
    CONF_VALUE_TEMPLATE: CONF_STATE,
    ATTR_FRIENDLY_NAME: CONF_NAME,
}

CONF_ALBUM_ART_TEMPLATE = "album_art_template"
CONF_CURRENT_IS_MUTED_TEMPLATE = "current_is_muted_template"
CONF_CURRENT_POSITION_TEMPLATE = "current_position_template"
CONF_CURRENT_SOUND_MODE_TEMPLATE = "current_sound_mode_template"
CONF_CURRENT_SOURCE_TEMPLATE = "current_source_template"
CONF_CURRENT_VOLUME_TEMPLATE = "current_volume_template"
CONF_INPUTS = "inputs"
CONF_MEDIA_ALBUM_ARTIST_TEMPLATE = "media_album_artist_template"
CONF_MEDIA_CONTENT_TYPE_TEMPLATE = "media_content_type_template"
CONF_MEDIA_DURATION_TEMPLATE = "media_duration_template"
CONF_MEDIA_EPISODE_TEMPLATE = "media_episode_template"
CONF_MEDIA_IMAGE_URL_REMOTELY_ACCESSIBLE = "media_image_url_remotely_accessible"
CONF_MEDIA_IMAGE_URL_TEMPLATE = "media_image_url_template"
CONF_MEDIA_SEASON_TEMPLATE = "media_season_template"
CONF_MEDIA_SERIES_TITLE_TEMPLATE = "media_series_title_template"
CONF_MEDIAPLAYER = "media_players"
CONF_MUTE_ACTION = "mute"
CONF_NEXT_ACTION = "next"
CONF_OFF_ACTION = "turn_off"
CONF_ON_ACTION = "turn_on"
CONF_PAUSE_ACTION = "pause"
CONF_PLAY_ACTION = "play"
CONF_PLAY_MEDIA_ACTION = "play_media"
CONF_PREVIOUS_ACTION = "previous"
CONF_SEEK_ACTION = "seek"
CONF_SET_VOLUME_ACTION = "set_volume"
CONF_SOUND_MODES = "sound_modes"
CONF_STOP_ACTION = "stop"
CONF_TITLE_TEMPLATE_LEGACY = "title_template"
CONF_VOLUME_DOWN_ACTION = "volume_down"
CONF_VOLUME_UP_ACTION = "volume_up"

MEDIA_PLAYER_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional(ATTR_FRIENDLY_NAME): cv.template,
        vol.Optional(CONF_ALBUM_ART_TEMPLATE): cv.template,
        vol.Optional(CONF_ALBUM_TEMPLATE): cv.template,
        vol.Optional("artist_template"): cv.template,
        vol.Optional(CONF_CURRENT_IS_MUTED_TEMPLATE): cv.template,
        vol.Optional(CONF_CURRENT_POSITION_TEMPLATE): cv.template,
        vol.Optional(CONF_CURRENT_SOUND_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_CURRENT_SOURCE_TEMPLATE): cv.template,
        vol.Optional(CONF_CURRENT_VOLUME_TEMPLATE): cv.template,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_ENTITY_PICTURE_TEMPLATE): cv.template,
        vol.Optional(CONF_ICON_TEMPLATE): cv.template,
        vol.Optional(CONF_INPUTS, default={}): {cv.string: cv.SCRIPT_SCHEMA},
        vol.Optional(CONF_MEDIA_ALBUM_ARTIST_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_CONTENT_TYPE_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_DURATION_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_EPISODE_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_IMAGE_URL_REMOTELY_ACCESSIBLE): cv.boolean,
        vol.Optional(CONF_MEDIA_IMAGE_URL_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_SEASON_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_SERIES_TITLE_TEMPLATE): cv.template,
        vol.Optional(CONF_MUTE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_NEXT_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_OFF_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_ON_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_PAUSE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_PLAY_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_PLAY_MEDIA_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_PREVIOUS_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SEEK_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_VOLUME_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SOUND_MODES, default={}): {cv.string: cv.SCRIPT_SCHEMA},
        vol.Optional(CONF_STOP_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_TITLE_TEMPLATE_LEGACY): cv.template,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Required(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_VOLUME_DOWN_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_VOLUME_UP_ACTION): cv.SCRIPT_SCHEMA,
    }
).extend(TEMPLATE_ENTITY_AVAILABILITY_SCHEMA_LEGACY.schema)

PLATFORM_SCHEMA = MEDIA_PLAYER_PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_MEDIAPLAYER): cv.schema_with_slug_keys(MEDIA_PLAYER_SCHEMA)}
)


# ---------------------------------------------------------------------------
# YAML platform setup — migration trigger only (no direct entity creation)
# ---------------------------------------------------------------------------


def _normalize_action(action_cfg: Any) -> dict[str, Any] | None:
    """Collapse a cv.SCRIPT_SCHEMA action to a plain {service, data} dict."""
    if action_cfg is None:
        return None
    step = action_cfg[0] if isinstance(action_cfg, list) else action_cfg
    if not isinstance(step, dict):
        return None
    service = step.get("service") or step.get("action")
    if not service:
        return None
    result: dict[str, Any] = {"service": str(service)}
    data = {k: (v.template if hasattr(v, "template") else v) for k, v in step.get("data", {}).items()}
    # Fold target:/entity_id: into data so they survive the import.
    for src in (step.get("target") or {}, {k: step[k] for k in ("entity_id",) if k in step}):
        for k, v in src.items():
            data.setdefault(k, v.template if hasattr(v, "template") else v)
    if data:
        result["data"] = data
    return result


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Import YAML-configured players as config entries (one-time migration)."""
    await async_setup_reload_service(hass, DOMAIN, [MEDIA_PLAYER_DOMAIN])

    for object_id, entity_config in config[CONF_MEDIAPLAYER].items():
        mapped = {LEGACY_FIELDS.get(k, k): v for k, v in entity_config.items()}
        def _str(val: Any, fallback: str) -> str:
            if val is None:
                return fallback
            return val.template if hasattr(val, "template") else str(val)

        name = _str(mapped.get(CONF_NAME), object_id)
        unique_id = _str(mapped.get(CONF_UNIQUE_ID), object_id)

        entry_data: dict[str, Any] = {"name": name, CONF_UNIQUE_ID: unique_id}

        for yaml_key, entry_key in (
            (CONF_STATE, CONF_STATE_TEMPLATE),
            (CONF_TITLE_TEMPLATE_LEGACY, CONF_TITLE_TEMPLATE),
            ("artist_template", CONF_ARTIST_TEMPLATE),
            (CONF_ALBUM_TEMPLATE, CONF_ALBUM_TEMPLATE),
            (CONF_MEDIA_IMAGE_URL_TEMPLATE, CONF_THUMBNAIL_TEMPLATE),
            (CONF_CURRENT_VOLUME_TEMPLATE, CONF_VOLUME_TEMPLATE),
            (CONF_CURRENT_IS_MUTED_TEMPLATE, CONF_MUTED_TEMPLATE),
            (CONF_CURRENT_SOURCE_TEMPLATE, CONF_SOURCE_TEMPLATE),
            (CONF_CURRENT_SOUND_MODE_TEMPLATE, CONF_SOUND_MODE_TEMPLATE),
            (CONF_CURRENT_POSITION_TEMPLATE, CONF_POSITION_TEMPLATE),
            (CONF_MEDIA_DURATION_TEMPLATE, CONF_DURATION_TEMPLATE),
            (CONF_MEDIA_CONTENT_TYPE_TEMPLATE, CONF_MEDIA_TYPE_TEMPLATE),
        ):
            if tmpl := mapped.get(yaml_key):
                entry_data[entry_key] = tmpl.template if hasattr(tmpl, "template") else str(tmpl)

        for yaml_key, entry_key in (
            (CONF_PLAY_ACTION, CONF_PLAY_SCRIPT),
            (CONF_PAUSE_ACTION, CONF_PAUSE_SCRIPT),
            (CONF_STOP_ACTION, CONF_STOP_SCRIPT),
            (CONF_NEXT_ACTION, CONF_NEXT_SCRIPT),
            (CONF_PREVIOUS_ACTION, CONF_PREVIOUS_SCRIPT),
            (CONF_VOLUME_UP_ACTION, CONF_VOLUME_UP_SCRIPT),
            (CONF_VOLUME_DOWN_ACTION, CONF_VOLUME_DOWN_SCRIPT),
            (CONF_SET_VOLUME_ACTION, CONF_SET_VOLUME_SCRIPT),
            (CONF_MUTE_ACTION, CONF_MUTE_SCRIPT),
            (CONF_ON_ACTION, CONF_TURN_ON_SCRIPT),
            (CONF_OFF_ACTION, CONF_TURN_OFF_SCRIPT),
            (CONF_PLAY_MEDIA_ACTION, CONF_PLAY_MEDIA_SCRIPT),
            (CONF_SEEK_ACTION, CONF_SEEK_SCRIPT),
        ):
            if action := mapped.get(yaml_key):
                if normalized := _normalize_action(action):
                    entry_data[entry_key] = normalized

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=entry_data,
            )
        )


# ---------------------------------------------------------------------------
# Config entry setup
# ---------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a config-entry-based template media player."""
    data = {**config_entry.data, **config_entry.options}
    entity = MediaPlayerTemplateEntry(hass, data, config_entry)
    async_add_entities([entity])


# ---------------------------------------------------------------------------
# Shared entity base
# ---------------------------------------------------------------------------


class _MediaPlayerTemplateBase(TemplateEntity, MediaPlayerEntity):
    """Base class for template media players."""

    _attr_should_poll = False
    _entity_id_format = ENTITY_ID_FORMAT

    # -----------------------------------------------------------------------
    # Template attribute setup – override in subclasses to bind template keys
    # -----------------------------------------------------------------------

    def _bind_optional_template(
        self,
        template_obj: Template | None,
        attr: str,
        updater: Any,
    ) -> None:
        if template_obj is not None:
            self.add_template_attribute(
                attr,
                template_obj,
                None,
                updater,
                none_on_template_error=True,
            )

    def _async_setup_templates(self) -> None:
        """Hook called by TemplateEntity after added to hass."""
        super()._async_setup_templates()

    # -----------------------------------------------------------------------
    # Common state update callbacks
    # -----------------------------------------------------------------------

    @callback
    def _update_state(self, result: Any) -> None:
        super()._update_state(result)
        if isinstance(result, TemplateError) or result is None:
            self._attr_state = None
            return
        result = vol.Coerce(str)(result).lower()
        try:
            if result == "true":
                self._attr_state = MediaPlayerState.ON
            elif result == "false":
                self._attr_state = MediaPlayerState.OFF
            else:
                self._attr_state = MediaPlayerState(result)
        except ValueError:
            _LOGGER.error(
                "Entity %s: invalid state %r", self.entity_id, result
            )
            self._attr_state = None

    @callback
    def _update_title(self, result: Any) -> None:
        self._attr_media_title = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )

    @callback
    def _update_artist(self, result: Any) -> None:
        self._attr_media_artist = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )

    @callback
    def _update_album(self, result: Any) -> None:
        self._attr_media_album_name = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )

    @callback
    def _update_image_url(self, result: Any) -> None:
        self._attr_media_image_url = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )

    @callback
    def _update_volume(self, result: Any) -> None:
        if isinstance(result, TemplateError) or result is None:
            self._attr_volume_level = None
            return
        try:
            self._attr_volume_level = vol.All(
                vol.Coerce(float), vol.Range(min=0, max=1)
            )(result)
        except vol.Invalid:
            _LOGGER.error(
                "Entity %s: invalid volume %r", self.entity_id, result
            )
            self._attr_volume_level = None

    @callback
    def _update_muted(self, result: Any) -> None:
        if isinstance(result, TemplateError) or result is None:
            self._attr_is_volume_muted = None
            return
        try:
            self._attr_is_volume_muted = cv.boolean(result)
        except vol.Invalid:
            _LOGGER.error(
                "Entity %s: invalid mute value %r", self.entity_id, result
            )
            self._attr_is_volume_muted = None

    @callback
    def _update_source(self, result: Any) -> None:
        self._attr_source = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )

    @callback
    def _update_sound_mode(self, result: Any) -> None:
        self._attr_sound_mode = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )

    @callback
    def _update_position(self, result: Any) -> None:
        if isinstance(result, TemplateError) or result is None:
            self._attr_media_position = None
            self._attr_media_position_updated_at = None
            return
        try:
            self._attr_media_position = cv.positive_int(result)
            self._attr_media_position_updated_at = dt_util.utcnow()
        except vol.Invalid:
            self._attr_media_position = None
            self._attr_media_position_updated_at = None

    @callback
    def _update_duration(self, result: Any) -> None:
        if isinstance(result, TemplateError) or result is None:
            self._attr_media_duration = None
            return
        try:
            self._attr_media_duration = cv.positive_int(result)
        except vol.Invalid:
            self._attr_media_duration = None

    @callback
    def _update_media_content_type(self, result: Any) -> None:
        if isinstance(result, TemplateError) or result is None:
            self._attr_media_content_type = None
            return
        result = vol.Coerce(str)(result).lower()
        try:
            self._attr_media_content_type = MediaType(result)
        except ValueError:
            _LOGGER.error(
                "Entity %s: invalid media_content_type %r", self.entity_id, result
            )
            self._attr_media_content_type = None

    @callback
    def _update_media_album_artist(self, result: Any) -> None:
        self._attr_media_album_artist = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )

    @callback
    def _update_media_episode(self, result: Any) -> None:
        self._attr_media_episode = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )

    @callback
    def _update_media_season(self, result: Any) -> None:
        self._attr_media_season = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )

    @callback
    def _update_media_series_title(self, result: Any) -> None:
        self._attr_media_series_title = (
            None if isinstance(result, TemplateError) or result is None
            else vol.Coerce(str)(result)
        )


# ---------------------------------------------------------------------------
# YAML-based entity (legacy schema, unchanged runtime behaviour)
# ---------------------------------------------------------------------------


class MediaPlayerTemplate(_MediaPlayerTemplateBase):
    """Template media player created from YAML configuration."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: ConfigType,
        unique_id: str | None,
    ) -> None:
        super().__init__(hass, config, unique_id)

        self._attr_device_class = config.get(CONF_DEVICE_CLASS)
        self._template = config[CONF_STATE]

        self._attr_supported_features = MediaPlayerEntityFeature(0)
        for action_id, feature in (
            (CONF_ON_ACTION, MediaPlayerEntityFeature.TURN_ON),
            (CONF_OFF_ACTION, MediaPlayerEntityFeature.TURN_OFF),
            (CONF_PLAY_ACTION, MediaPlayerEntityFeature.PLAY),
            (CONF_STOP_ACTION, MediaPlayerEntityFeature.STOP),
            (CONF_PAUSE_ACTION, MediaPlayerEntityFeature.PAUSE),
            (CONF_NEXT_ACTION, MediaPlayerEntityFeature.NEXT_TRACK),
            (CONF_PREVIOUS_ACTION, MediaPlayerEntityFeature.PREVIOUS_TRACK),
            (CONF_VOLUME_UP_ACTION, MediaPlayerEntityFeature.VOLUME_STEP),
            (CONF_VOLUME_DOWN_ACTION, MediaPlayerEntityFeature.VOLUME_STEP),
            (CONF_MUTE_ACTION, MediaPlayerEntityFeature.VOLUME_MUTE),
            (CONF_SET_VOLUME_ACTION, MediaPlayerEntityFeature.VOLUME_SET),
            (CONF_PLAY_MEDIA_ACTION, MediaPlayerEntityFeature.PLAY_MEDIA),
            (CONF_SEEK_ACTION, MediaPlayerEntityFeature.SEEK),
        ):
            if (action_cfg := config.get(action_id)) is not None:
                self.add_script(action_id, action_cfg, self._attr_name, TEMPLATE_DOMAIN)
                self._attr_supported_features |= feature

        for source, source_cfg in config.get(CONF_INPUTS, {}).items():
            self._add_source(source, source_cfg)

        for mode, mode_cfg in config.get(CONF_SOUND_MODES, {}).items():
            self._add_sound_mode(mode, mode_cfg)

        self._current_source_template = config.get(CONF_CURRENT_SOURCE_TEMPLATE)
        self._legacy_title_template = config.get(CONF_TITLE_TEMPLATE_LEGACY)
        self._legacy_artist_template = config.get("artist_template")
        self._legacy_album_template = config.get(CONF_ALBUM_TEMPLATE)
        self._current_volume_template = config.get(CONF_CURRENT_VOLUME_TEMPLATE)
        self._current_is_muted_template = config.get(CONF_CURRENT_IS_MUTED_TEMPLATE)
        self._current_sound_mode_template = config.get(CONF_CURRENT_SOUND_MODE_TEMPLATE)
        self._media_image_url_template = config.get(CONF_MEDIA_IMAGE_URL_TEMPLATE)
        self._media_content_type_template = config.get(CONF_MEDIA_CONTENT_TYPE_TEMPLATE)
        self._media_episode_template = config.get(CONF_MEDIA_EPISODE_TEMPLATE)
        self._media_season_template = config.get(CONF_MEDIA_SEASON_TEMPLATE)
        self._media_series_title_template = config.get(CONF_MEDIA_SERIES_TITLE_TEMPLATE)
        self._media_album_artist_template = config.get(CONF_MEDIA_ALBUM_ARTIST_TEMPLATE)
        self._current_position_template = config.get(CONF_CURRENT_POSITION_TEMPLATE)
        self._media_duration_template = config.get(CONF_MEDIA_DURATION_TEMPLATE)

        self._attr_media_image_remotely_accessible = config.get(
            CONF_MEDIA_IMAGE_URL_REMOTELY_ACCESSIBLE, False
        )

    @property
    def device_info(self) -> DeviceInfo | None:
        if self._attr_unique_id is None:
            return None
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name or self.entity_id,
            manufacturer="Media Player Template",
            model="YAML",
        )

    def _async_setup_templates(self) -> None:
        self.add_template_attribute(
            "_attr_state",
            self._template,
            None,
            self._update_state,
            none_on_template_error=True,
        )
        for tmpl, attr, updater in (
            (self._current_source_template, "_attr_source", self._update_source),
            (self._legacy_title_template, "_attr_media_title", self._update_title),
            (self._legacy_artist_template, "_attr_media_artist", self._update_artist),
            (self._legacy_album_template, "_attr_media_album_name", self._update_album),
            (self._current_volume_template, "_attr_volume_level", self._update_volume),
            (self._current_is_muted_template, "_attr_is_volume_muted", self._update_muted),
            (self._media_content_type_template, "_attr_media_content_type", self._update_media_content_type),
            (self._media_image_url_template, "_attr_media_image_url", self._update_image_url),
            (self._media_episode_template, "_attr_media_episode", self._update_media_episode),
            (self._media_season_template, "_attr_media_season", self._update_media_season),
            (self._media_series_title_template, "_attr_media_series_title", self._update_media_series_title),
            (self._media_album_artist_template, "_attr_media_album_artist", self._update_media_album_artist),
            (self._current_position_template, "_attr_media_position", self._update_position),
            (self._media_duration_template, "_attr_media_duration", self._update_duration),
            (self._current_sound_mode_template, "_attr_sound_mode", self._update_sound_mode),
        ):
            if tmpl is not None:
                self.add_template_attribute(
                    attr, tmpl, None, updater, none_on_template_error=True
                )
        super()._async_setup_templates()

    def _add_source(self, source: str, config: ConfigType | None = None) -> None:
        if config:
            self.add_script(f"input_{source}", config, self._attr_name, TEMPLATE_DOMAIN)
        self._attr_supported_features |= MediaPlayerEntityFeature.SELECT_SOURCE
        if self._attr_source_list is None:
            self._attr_source_list = []
        self._attr_source_list.append(source)

    def _add_sound_mode(self, mode: str, config: ConfigType | None = None) -> None:
        if config:
            self.add_script(f"sound_mode_{mode}", config, self._attr_name, TEMPLATE_DOMAIN)
        self._attr_supported_features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE
        if self._attr_sound_mode_list is None:
            self._attr_sound_mode_list = []
        self._attr_sound_mode_list.append(mode)

    @callback
    def _update_source(self, result: Any) -> None:
        if isinstance(result, TemplateError) or result is None:
            self._attr_source = None
            return
        if self._attr_source_list and result not in self._attr_source_list:
            self._add_source(result)
        self._attr_source = result

    @callback
    def _update_sound_mode(self, result: Any) -> None:
        if isinstance(result, TemplateError) or result is None:
            self._attr_sound_mode = None
            return
        if self._attr_sound_mode_list and result not in self._attr_sound_mode_list:
            self._add_sound_mode(result)
        self._attr_sound_mode = result

    # --- Actions (YAML) ---

    async def async_turn_on(self) -> None:
        if s := self._action_scripts.get(CONF_ON_ACTION):
            await self.async_run_script(s, context=self._context)

    async def async_turn_off(self) -> None:
        if s := self._action_scripts.get(CONF_OFF_ACTION):
            await self.async_run_script(s, context=self._context)

    async def async_volume_up(self) -> None:
        if s := self._action_scripts.get(CONF_VOLUME_UP_ACTION):
            await self.async_run_script(s, context=self._context)

    async def async_volume_down(self) -> None:
        if s := self._action_scripts.get(CONF_VOLUME_DOWN_ACTION):
            await self.async_run_script(s, context=self._context)

    async def async_mute_volume(self, mute: bool) -> None:
        if self._current_is_muted_template is None:
            self._attr_is_volume_muted = mute
            self.async_write_ha_state()
        if s := self._action_scripts.get(CONF_MUTE_ACTION):
            await self.async_run_script(
                s, run_variables={"is_muted": mute}, context=self._context
            )

    async def async_media_play(self) -> None:
        if s := self._action_scripts.get(CONF_PLAY_ACTION):
            await self.async_run_script(s, context=self._context)

    async def async_media_stop(self) -> None:
        if s := self._action_scripts.get(CONF_STOP_ACTION):
            await self.async_run_script(s, context=self._context)

    async def async_media_pause(self) -> None:
        if s := self._action_scripts.get(CONF_PAUSE_ACTION):
            await self.async_run_script(s, context=self._context)

    async def async_media_next_track(self) -> None:
        if s := self._action_scripts.get(CONF_NEXT_ACTION):
            await self.async_run_script(s, context=self._context)

    async def async_media_previous_track(self) -> None:
        if s := self._action_scripts.get(CONF_PREVIOUS_ACTION):
            await self.async_run_script(s, context=self._context)

    async def async_set_volume_level(self, volume: float) -> None:
        if self._current_volume_template is None:
            self._attr_volume_level = volume
            self.async_write_ha_state()
        if s := self._action_scripts.get(CONF_SET_VOLUME_ACTION):
            await self.async_run_script(
                s, run_variables={"volume": volume}, context=self._context
            )

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        if s := self._action_scripts.get(CONF_PLAY_MEDIA_ACTION):
            await self.async_run_script(
                s,
                run_variables={"media_type": media_type, "media_id": media_id},
                context=self._context,
            )

    async def async_media_seek(self, position: float) -> None:
        if s := self._action_scripts.get(CONF_SEEK_ACTION):
            await self.async_run_script(
                s, run_variables={"position": position}, context=self._context
            )

    async def async_select_source(self, source: str) -> None:
        if s := self._action_scripts.get(f"input_{source}"):
            if self._current_source_template is None:
                self._attr_source = source
                self.async_write_ha_state()
            await self.async_run_script(s, context=self._context)

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        if s := self._action_scripts.get(f"sound_mode_{sound_mode}"):
            if self._current_sound_mode_template is None:
                self._attr_sound_mode = sound_mode
                self.async_write_ha_state()
            await self.async_run_script(s, context=self._context)


# ---------------------------------------------------------------------------
# Config-entry-based entity
# ---------------------------------------------------------------------------


def _make_template(hass: HomeAssistant, value: str | None) -> Template | None:
    if not value:
        return None
    t = Template(value, hass)
    return t


def _feature_if(script_val: str | None, feature: MediaPlayerEntityFeature) -> MediaPlayerEntityFeature:
    return feature if script_val else MediaPlayerEntityFeature(0)


class MediaPlayerTemplateEntry(MediaPlayerEntity):
    """Template media player backed by a config entry.

    Uses raw Template objects and async_track_template_result for reactivity
    instead of TemplateEntity (which requires complex legacy-config dicts).
    """

    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        data: dict[str, Any],
        entry: ConfigEntry,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._data = data

        raw_name = data.get("name", entry.title)
        # Defensive: fix mangled "Template<template=(...) renders=0>" stored by
        # earlier imports that forgot to call .template on Template objects.
        if isinstance(raw_name, str) and raw_name.startswith("Template<"):
            m = re.search(r"Template<template=\((.+?)\)", raw_name)
            raw_name = m.group(1) if m else raw_name
        name = raw_name
        self._attr_name = name
        self._attr_unique_id = data.get(CONF_UNIQUE_ID) or entry.entry_id

        # Build template objects
        self._state_tpl = Template(data[CONF_STATE_TEMPLATE], hass)
        self._title_tpl = _make_template(hass, data.get(CONF_TITLE_TEMPLATE))
        self._artist_tpl = _make_template(hass, data.get(CONF_ARTIST_TEMPLATE))
        self._album_tpl = _make_template(hass, data.get(CONF_ALBUM_TEMPLATE))
        self._thumbnail_tpl = _make_template(hass, data.get(CONF_THUMBNAIL_TEMPLATE))
        self._volume_tpl = _make_template(hass, data.get(CONF_VOLUME_TEMPLATE))
        self._muted_tpl = _make_template(hass, data.get(CONF_MUTED_TEMPLATE))
        self._source_tpl = _make_template(hass, data.get(CONF_SOURCE_TEMPLATE))
        self._sound_mode_tpl = _make_template(hass, data.get(CONF_SOUND_MODE_TEMPLATE))
        self._position_tpl = _make_template(hass, data.get(CONF_POSITION_TEMPLATE))
        self._duration_tpl = _make_template(hass, data.get(CONF_DURATION_TEMPLATE))
        self._media_type_tpl = _make_template(hass, data.get(CONF_MEDIA_TYPE_TEMPLATE))

        # Action: str (script entity-id) or dict {service, data} — both are valid
        self._play_action = data.get(CONF_PLAY_SCRIPT)
        self._pause_action = data.get(CONF_PAUSE_SCRIPT)
        self._stop_action = data.get(CONF_STOP_SCRIPT)
        self._next_action = data.get(CONF_NEXT_SCRIPT)
        self._previous_action = data.get(CONF_PREVIOUS_SCRIPT)
        self._vol_up_action = data.get(CONF_VOLUME_UP_SCRIPT)
        self._vol_down_action = data.get(CONF_VOLUME_DOWN_SCRIPT)
        self._set_volume_action = data.get(CONF_SET_VOLUME_SCRIPT)
        self._mute_action = data.get(CONF_MUTE_SCRIPT)
        self._turn_on_action = data.get(CONF_TURN_ON_SCRIPT)
        self._turn_off_action = data.get(CONF_TURN_OFF_SCRIPT)
        self._play_media_action = data.get(CONF_PLAY_MEDIA_SCRIPT)
        self._seek_action = data.get(CONF_SEEK_SCRIPT)
        self._select_source_action = data.get(CONF_SELECT_SOURCE_SCRIPT)
        self._select_sound_mode_action = data.get(CONF_SELECT_SOUND_MODE_SCRIPT)

        # Supported features
        feats = MediaPlayerEntityFeature(0)
        feats |= _feature_if(self._play_action, MediaPlayerEntityFeature.PLAY)
        feats |= _feature_if(self._pause_action, MediaPlayerEntityFeature.PAUSE)
        feats |= _feature_if(self._stop_action, MediaPlayerEntityFeature.STOP)
        feats |= _feature_if(self._next_action, MediaPlayerEntityFeature.NEXT_TRACK)
        feats |= _feature_if(self._previous_action, MediaPlayerEntityFeature.PREVIOUS_TRACK)
        feats |= _feature_if(self._vol_up_action, MediaPlayerEntityFeature.VOLUME_STEP)
        feats |= _feature_if(self._vol_down_action, MediaPlayerEntityFeature.VOLUME_STEP)
        feats |= _feature_if(self._set_volume_action, MediaPlayerEntityFeature.VOLUME_SET)
        feats |= _feature_if(self._mute_action, MediaPlayerEntityFeature.VOLUME_MUTE)
        feats |= _feature_if(self._turn_on_action, MediaPlayerEntityFeature.TURN_ON)
        feats |= _feature_if(self._turn_off_action, MediaPlayerEntityFeature.TURN_OFF)
        feats |= _feature_if(self._play_media_action, MediaPlayerEntityFeature.PLAY_MEDIA)
        feats |= _feature_if(self._seek_action, MediaPlayerEntityFeature.SEEK)
        feats |= _feature_if(self._select_source_action, MediaPlayerEntityFeature.SELECT_SOURCE)
        feats |= _feature_if(self._select_sound_mode_action, MediaPlayerEntityFeature.SELECT_SOUND_MODE)
        self._attr_supported_features = feats

        # Mutable state
        self._attr_state: MediaPlayerState | None = None
        self._attr_media_title: str | None = None
        self._attr_media_artist: str | None = None
        self._attr_media_album_name: str | None = None
        self._attr_media_image_url: str | None = None
        self._attr_volume_level: float | None = None
        self._attr_is_volume_muted: bool | None = None
        self._attr_source: str | None = None
        self._attr_sound_mode: str | None = None
        self._attr_media_position: int | None = None
        self._attr_media_position_updated_at = None
        self._attr_media_duration: int | None = None
        self._attr_media_content_type: MediaType | None = None
        self._unsub: list[Any] = []

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name,
            manufacturer="Media Player Template",
            model="Config Entry",
        )

    async def async_added_to_hass(self) -> None:
        """Start tracking templates."""
        # Self-heal: if config entry stored a mangled Template string, fix it now.
        if self._entry.data.get("name") != self._attr_name:
            self.hass.config_entries.async_update_entry(
                self._entry,
                title=self._attr_name,
                data={**self._entry.data, "name": self._attr_name},
            )

        templates: list[tuple[Template, Any]] = [
            (self._state_tpl, self._handle_state),
        ]
        for tpl, handler in (
            (self._title_tpl, self._handle_title),
            (self._artist_tpl, self._handle_artist),
            (self._album_tpl, self._handle_album),
            (self._thumbnail_tpl, self._handle_thumbnail),
            (self._volume_tpl, self._handle_volume),
            (self._muted_tpl, self._handle_muted),
            (self._source_tpl, self._handle_source),
            (self._sound_mode_tpl, self._handle_sound_mode),
            (self._position_tpl, self._handle_position),
            (self._duration_tpl, self._handle_duration),
            (self._media_type_tpl, self._handle_media_type),
        ):
            if tpl is not None:
                templates.append((tpl, handler))

        for tpl, handler in templates:
            def _make_listener(h):
                @callback
                def listener(event, updates):
                    result = updates[-1].result
                    h(result)
                    self.async_write_ha_state()
                return listener

            unsub = async_track_template_result(
                self.hass,
                [TrackTemplate(tpl, None)],
                _make_listener(handler),
            )
            self._unsub.append(unsub)

        # Force initial evaluation
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_will_remove_from_hass(self) -> None:
        for tracker in self._unsub:
            tracker.async_remove()
        self._unsub.clear()

    async def async_update(self) -> None:
        """Evaluate all templates once."""
        for tpl, handler in (
            (self._state_tpl, self._handle_state),
            (self._title_tpl, self._handle_title),
            (self._artist_tpl, self._handle_artist),
            (self._album_tpl, self._handle_album),
            (self._thumbnail_tpl, self._handle_thumbnail),
            (self._volume_tpl, self._handle_volume),
            (self._muted_tpl, self._handle_muted),
            (self._source_tpl, self._handle_source),
            (self._sound_mode_tpl, self._handle_sound_mode),
            (self._position_tpl, self._handle_position),
            (self._duration_tpl, self._handle_duration),
            (self._media_type_tpl, self._handle_media_type),
        ):
            if tpl is None:
                continue
            try:
                result = tpl.async_render(parse_result=False)
                handler(result)
            except TemplateError as err:
                _LOGGER.warning("Template error for %s: %s", self.entity_id, err)
                handler(err)

    # --- Template result handlers ---

    def _handle_state(self, result: Any) -> None:
        if isinstance(result, TemplateError) or result is None:
            self._attr_state = None
            return
        val = str(result).lower()
        try:
            if val == "true":
                self._attr_state = MediaPlayerState.ON
            elif val == "false":
                self._attr_state = MediaPlayerState.OFF
            else:
                self._attr_state = MediaPlayerState(val)
        except ValueError:
            _LOGGER.error("Entity %s: invalid state %r", self.entity_id, val)
            self._attr_state = None

    def _handle_title(self, result: Any) -> None:
        self._attr_media_title = (
            None if not result or isinstance(result, TemplateError)
            else str(result)
        )

    def _handle_artist(self, result: Any) -> None:
        self._attr_media_artist = (
            None if not result or isinstance(result, TemplateError)
            else str(result)
        )

    def _handle_album(self, result: Any) -> None:
        self._attr_media_album_name = (
            None if not result or isinstance(result, TemplateError)
            else str(result)
        )

    def _handle_thumbnail(self, result: Any) -> None:
        self._attr_media_image_url = (
            None if not result or isinstance(result, TemplateError)
            else str(result)
        )

    def _handle_volume(self, result: Any) -> None:
        if result is None or result == "" or isinstance(result, TemplateError):
            self._attr_volume_level = None
            return
        try:
            self._attr_volume_level = max(0.0, min(1.0, float(result)))
        except (TypeError, ValueError):
            self._attr_volume_level = None

    def _handle_muted(self, result: Any) -> None:
        if result is None or isinstance(result, TemplateError):
            self._attr_is_volume_muted = None
            return
        try:
            self._attr_is_volume_muted = cv.boolean(result)
        except vol.Invalid:
            self._attr_is_volume_muted = None

    def _handle_source(self, result: Any) -> None:
        self._attr_source = (
            None if not result or isinstance(result, TemplateError)
            else str(result)
        )

    def _handle_sound_mode(self, result: Any) -> None:
        self._attr_sound_mode = (
            None if not result or isinstance(result, TemplateError)
            else str(result)
        )

    def _handle_position(self, result: Any) -> None:
        if result is None or result == "" or isinstance(result, TemplateError):
            self._attr_media_position = None
            self._attr_media_position_updated_at = None
            return
        try:
            self._attr_media_position = int(float(result))
            self._attr_media_position_updated_at = dt_util.utcnow()
        except (TypeError, ValueError):
            self._attr_media_position = None
            self._attr_media_position_updated_at = None

    def _handle_duration(self, result: Any) -> None:
        if result is None or result == "" or isinstance(result, TemplateError):
            self._attr_media_duration = None
            return
        try:
            self._attr_media_duration = int(float(result))
        except (TypeError, ValueError):
            self._attr_media_duration = None

    def _handle_media_type(self, result: Any) -> None:
        if not result or isinstance(result, TemplateError):
            self._attr_media_content_type = None
            return
        try:
            self._attr_media_content_type = MediaType(str(result).lower())
        except ValueError:
            self._attr_media_content_type = None

    # --- Action helpers ---

    async def _call_action(
        self, action: str | dict | None, variables: dict | None = None
    ) -> None:
        if not action:
            return
        if isinstance(action, str):
            # Simple script entity-id (UI-created entry)
            await self.hass.services.async_call(
                "script", "turn_on", {"entity_id": action}, context=self._context
            )
            return
        service_str = action.get("service") or action.get("action", "")
        if not service_str:
            return
        if "." not in service_str:
            _LOGGER.error(
                "Invalid service %r for %s (expected domain.service)",
                service_str,
                self.entity_id,
            )
            return
        domain, service_name = service_str.split(".", 1)
        svc_data: dict[str, Any] = {}
        for k, v in action.get("data", {}).items():
            if isinstance(v, str) and ("{{" in v or "{%" in v):
                try:
                    svc_data[k] = Template(v, self.hass).async_render(
                        variables or {}, parse_result=False
                    )
                except TemplateError as err:
                    _LOGGER.error("Template error in action %r key %r: %s", service_str, k, err)
                    svc_data[k] = v
            else:
                svc_data[k] = v
        await self.hass.services.async_call(domain, service_name, svc_data, context=self._context)

    # --- Actions ---

    async def async_turn_on(self) -> None:
        await self._call_action(self._turn_on_action)

    async def async_turn_off(self) -> None:
        await self._call_action(self._turn_off_action)

    async def async_media_play(self) -> None:
        await self._call_action(self._play_action)

    async def async_media_pause(self) -> None:
        await self._call_action(self._pause_action)

    async def async_media_stop(self) -> None:
        await self._call_action(self._stop_action)

    async def async_media_next_track(self) -> None:
        await self._call_action(self._next_action)

    async def async_media_previous_track(self) -> None:
        await self._call_action(self._previous_action)

    async def async_volume_up(self) -> None:
        await self._call_action(self._vol_up_action)

    async def async_volume_down(self) -> None:
        await self._call_action(self._vol_down_action)

    async def async_mute_volume(self, mute: bool) -> None:
        if self._muted_tpl is None:
            self._attr_is_volume_muted = mute
            self.async_write_ha_state()
        await self._call_action(self._mute_action, {"is_muted": mute})

    async def async_set_volume_level(self, volume: float) -> None:
        if self._volume_tpl is None:
            self._attr_volume_level = volume
            self.async_write_ha_state()
        await self._call_action(self._set_volume_action, {"volume": volume})

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        await self._call_action(
            self._play_media_action,
            {"media_type": media_type, "media_id": media_id},
        )

    async def async_media_seek(self, position: float) -> None:
        await self._call_action(self._seek_action, {"position": position})

    async def async_select_source(self, source: str) -> None:
        if self._source_tpl is None:
            self._attr_source = source
            self.async_write_ha_state()
        await self._call_action(self._select_source_action, {"source": source})

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        if self._sound_mode_tpl is None:
            self._attr_sound_mode = sound_mode
            self.async_write_ha_state()
        await self._call_action(self._select_sound_mode_action, {"sound_mode": sound_mode})
