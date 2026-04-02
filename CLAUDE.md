# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Home Assistant custom integration for monitoring FamilyMart Laundry (Fami 自助洗衣) machine statuses in Taiwan. It polls the FamilyMart API and exposes each machine as a HA device with two sensor entities (status + time remaining).

## Development Workflow

There is no build step. To test changes:

1. Copy `custom_components/familaundry/` to your HA instance's `config/custom_components/` folder
2. Restart Home Assistant Core

Use the `ha-deploy` skill (`/ha-deploy`) to deploy and restart the test HA instance automatically.

No automated tests exist yet. Testing is manual within a running HA instance.

CI runs HACS structural validation on push to `main` via `.github/workflows/hacs.yml`.

## Architecture

The integration follows the standard HA DataUpdateCoordinator pattern:

- **`coordinator.py`** — `FamiLaundryCoordinator` fetches machine data from the API via `aiohttp` on a configurable interval (default 60s, min 30s). All sensor entities share one coordinator per config entry.
- **`config_flow.py`** — Three-step UI setup: County → Store → Update Interval. Each step makes live API calls to populate dropdowns.
- **`sensor.py`** — Two entity types per machine: status (`idle`/`busy`/`finish`/`offline`/`unknown`) and time remaining (minutes).
- **`__init__.py`** — Registers platforms and wires coordinator reload on options update.

## Key Conventions

**Entity IDs** are explicitly set to `sensor.familaundry_{store_id}_{machine_id}_{status|time_remaining}` — stable English-only identifiers that don't change when display names are localized.

**Machine state mapping** from API `status` field:
- `0` → `idle`
- `1` + `FINISH_TIME > 0` → `busy`
- `1` + `FINISH_TIME == 0` → `finish`
- `2` → `offline`

**Localization**: All UI strings live in `strings.json` (English base) and `translations/zh-Hant.json`. Never hardcode user-visible strings — always use translation keys.

**Icons**: Use `mdi:washing-machine`, `mdi:tumble-dryer`, `mdi:basket-check`, `mdi:washing-machine-off` for machine types and states.

**API base URL**: `https://familaundry.famigrp.com.tw/Wash/` (endpoints: `GetMachine`, `GetCountryList`, `GetAREAList`).
