# Configuration

Create media players through the UI under **Settings → Devices & services → Add
integration → Media Player Template**. A name and state template are required.
Metadata templates (title, artist, album, thumbnail, position, duration,
volume, mute, source, sound mode, app, repeat, shuffle and entity picture) and
scripts for playback actions are optional. Edit them under **Configure** later.

Alternatively, define players in YAML:

```yaml
media_player:
  - platform: media_player_template
    media_players:
      my_desktop:
        friendly_name: My Desktop
        unique_id: my-desktop-playerctl
        value_template: >-
          {% if is_state('binary_sensor.desktop_media', 'on') %}
            playing
          {% else %}
            idle
          {% endif %}
        title_template: "{{ state_attr('binary_sensor.desktop_media', 'title') }}"
        artist_template: "{{ state_attr('binary_sensor.desktop_media', 'artist') }}"
        current_volume_template: "{{ states('sensor.desktop_volume') | float }}"
        current_is_muted_template: "{{ is_state('binary_sensor.desktop_mute', 'on') }}"
        pause:
          service: script.pause_desktop
        play:
          service: script.resume_desktop
        next:
          service: script.desktop_next_track
```

YAML players are imported into config entries on startup. Reload changed
YAML through **Developer Tools → YAML → Reload** or
`homeassistant.reload_custom_component` without restarting Home Assistant.

The state template should render `playing`, `paused`, `idle`, `on`, `true`,
`off`, `false`, `standby` or `buffering`. The action script receives variables
for supported actions:

| Action | Variable |
|--------|----------|
| `set_volume` | `volume` (0.0–1.0) |
| `mute` | `is_muted` (boolean) |
| `play_media` | `media_id`, `media_type` |
| `seek` | `position` (seconds) |
| `select_source` | `source` |
| `select_sound_mode` | `sound_mode` |
| `set_repeat` | `repeat` (`off`, `all`, `one`) |
| `set_shuffle` | `shuffle` (boolean) |

When an action is a script entity ID, its variables are passed to the script
as `variables`. Empty repeat/shuffle templates use the last value set through
an action as optimistic state, as do volume and mute.
