# FamilyMart Laundry Home Assistant Integration

## Project Overview
This project is a Home Assistant custom integration for monitoring FamilyMart Laundry (Fami 自助洗衣) machine statuses in Taiwan. It fetches real-time data from the FamilyMart API and presents each machine as a separate device in Home Assistant.

### Main Technologies
- **Home Assistant Custom Integration**: Adheres to the standard structure for third-party HA components.
- **Python**: Core logic implemented in Python using `aiohttp` for asynchronous API requests.
- **DataUpdateCoordinator**: Uses the standard HA pattern to centralize data fetching and distribute updates to multiple entities efficiently.
- **Config Flow**: Provides a user-friendly, multi-step setup process within the Home Assistant UI.

### Architecture
- `custom_components/familaundry/`: Core integration directory.
  - `__init__.py`: Handles component setup and entry points.
  - `coordinator.py`: Implements the `FamiLaundryCoordinator` for centralized data fetching.
  - `sensor.py`: Defines sensor entities for machine status and time remaining.
  - `config_flow.py`: Implements the UI configuration logic (County > Store > Interval).
  - `const.py`: Stores constants such as API URLs and configuration keys.
  - `manifest.json`: Integration metadata and HACS requirements.
  - `translations/`: Localization files (currently supporting Traditional Chinese).
  - `brand/`: Visual assets for the integration.

## Building and Running
As a Python project for Home Assistant, there is no traditional build step.

### Installation
1. Copy the `custom_components/familaundry/` directory to your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.
3. Add the integration via the UI: **Settings** > **Devices & Services** > **Add Integration** > search for **FamilyMart Laundry**.

### Testing
- Manual verification within a Home Assistant instance is the primary testing method.
- TODO: Implement automated unit tests using `pytest` and `homeassistant.helpers.test`.

## Development Conventions
- **Entity Naming**: Entity IDs are explicitly set to follow the pattern `sensor.familaundry_[store_id]_[machine_id]_[suffix]` to ensure stable, English-only identifiers regardless of localized display names.
- **Localization**: All UI strings should be defined in `strings.json` and translated in `translations/`.
- **Machine States**: The integration maps API status codes to the following states:
  - `idle`: Machine is available.
  - `busy`: Machine is currently running.
  - `finish`: Machine has finished its cycle and is waiting for pickup.
  - `offline`: Machine is maintenance or disconnected.
- **Device Grouping**: Each physical machine is represented as a separate "Device" in Home Assistant, grouped under the specific FamilyMart store.
- **Icons**: Uses Material Design Icons (`mdi:washing-machine`, `mdi:tumble-dryer`, `mdi:basket-check`, `mdi:washing-machine-off`) to represent machine types and states.
