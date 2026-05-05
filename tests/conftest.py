"""Shared fixtures for the Fami Laundry integration tests."""
from __future__ import annotations

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make HA discover this custom integration in every test that uses hass."""
    yield
