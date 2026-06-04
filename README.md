# Media Player Template for Home Assistant

A custom integration that lets you define media player entities using Jinja2 templates and optional action scripts. Supports both YAML configuration (with hot reload) and UI-driven setup via the Home Assistant config flow.

## Features

- **Template-driven state** — define playing/paused/idle/etc. from any sensor, binary sensor, or arbitrary template
- **Rich metadata** — title, artist, album, thumbnail, position, duration, volume, mute, source, sound mode
- **Full action support** — play, pause, stop, next/previous, volume, seek, play media, and more
- **Config entry + UI** — add and configure players from the HA UI without editing YAML
- **Hot reload** — YAML-configured players reload without restarting HA (`Developer Tools → YAML → Reload`)
- **Device registry** — each player appears as a proper HA device
- **HACS compatible**

## Installation

### HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/pschmitt/homeassistant-media-player-template` as an **Integration**
3. Install **Media Player Template** and restart HA

### Manual

Copy `custom_components/media_player_template/` into your HA config directory and restart.

## YAML configuration

```yaml
media_player:
  - platform: media_player_template
    media_players:
      my_desktop:
        friendly_name: "My Desktop"
        unique_id: my-desktop-playerctl
        value_template: >-
          {% set state = state_attr("binary_sensor.desktop_media", "state") %}
          {% if state in ["playing", "paused"] %}
            {{ state }}
          {% elif is_state("binary_sensor.desktop_media", "on") %}
            playing
          {% else %}
            idle
          {% endif %}
        title_template: '{{ state_attr("binary_sensor.desktop_media", "title") }}'
        artist_template: '{{ state_attr("binary_sensor.desktop_media", "artist") }}'
        album_template: '{{ state_attr("binary_sensor.desktop_media", "album") }}'
        current_volume_template: '{{ states("sensor.desktop_volume") | float }}'
        current_is_muted_template: '{{ is_state("binary_sensor.desktop_mute", "on") }}'
        pause:
          service: script.pause_desktop
        play:
          service: script.resume_desktop
        next:
          service: script.desktop_next_track
        previous:
          service: script.desktop_prev_track
        volume_up:
          service: script.desktop_vol_up
        volume_down:
          service: script.desktop_vol_down
```

To hot-reload after changing YAML: **Developer Tools → YAML → Reload** (select your domain or use `homeassistant.reload_custom_component`).

## UI / config flow

Go to **Settings → Integrations → Add Integration → Media Player Template**.

1. Enter a **name** and a **state template** (required)
2. Optionally add metadata templates (title, artist, album, thumbnail, volume, mute, source, …)
3. Optionally add action scripts (scripts to call for play, pause, stop, etc.)

After creation you can edit all settings under **Configure** in the integration card.

## State template values

The state template should render one of:

| Value | Meaning |
|-------|---------|
| `playing` | Currently playing |
| `paused` | Paused |
| `idle` | Idle / stopped |
| `on` / `true` | On |
| `off` / `false` | Off |
| `standby` | Standby |
| `buffering` | Buffering |

## Action script variables

| Action | Available variables |
|--------|-------------------|
| `set_volume` | `{{ volume }}` — float 0.0–1.0 |
| `mute` | `{{ is_muted }}` — boolean |
| `play_media` | `{{ media_id }}`, `{{ media_type }}` |
| `seek` | `{{ position }}` — seconds |
| `select_source` | `{{ source }}` — string |
| `select_sound_mode` | `{{ sound_mode }}` — string |

## Credits

Originally by [@Sennevds](https://github.com/Sennevds/media_player.template).
Forked and modernised by [@pschmitt](https://github.com/pschmitt):
- Fixed compatibility with Home Assistant 2026.6+
- Added config entry / UI support
- Added device registry support
- Added hot reload for YAML configuration
