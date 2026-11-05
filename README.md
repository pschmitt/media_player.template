<p align="center">
  <img src="custom_components/media_player_template/brand/logo.png" width="128" alt="Media Player Template logo">
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/marketplace_repository/?owner=pschmitt&amp;repository=media_player.template&amp;category=integration"><img src="https://my.home-assistant.io/badges/marketplace_repository.svg" alt="Open this integration in Home Assistant Marketplace"></a>
</p>

<h1 align="center">Media Player Template</h1>

<p align="center">Build Home Assistant media players from Jinja2 state templates and action scripts.</p>

Based on the original integration by
[Sennevds](https://github.com/Sennevds/media_player.template).

## Features

- **Template-driven state:** Derive playback state and metadata from other Home Assistant entities. See [Configuration](docs/configuration.md).
- **Playback actions:** Attach scripts for play, pause, seek, volume, media, repeat, shuffle and more.
- **UI or YAML:** Create players through a config flow or import them from YAML with hot reload.
- **Device registry:** Represent each configured player as a Home Assistant device.

## Install

Use the Marketplace badge above on Home Assistant 2026.11 or later to add this
repository as a custom integration. On older versions, add it as a HACS
custom repository of type **Integration**. Install and restart Home Assistant.
The badge does not imply a public catalog listing. For manual installation,
copy `custom_components/media_player_template/` into Home Assistant's
`custom_components/` directory and restart.

## Quick start

1. Add **Media Player Template** under **Settings → Devices & services → Add integration**.
2. Enter a player name and state template such as `{{ states('media_player.example') }}`.
3. Optionally add metadata templates and action scripts, then inspect the new media player.

## Documentation

| Topic | Description |
|-------|-------------|
| [Configuration](docs/configuration.md) | YAML example, supported state values and action variables |

## License

[MIT](LICENSE).
