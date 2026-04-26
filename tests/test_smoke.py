"""Smoke tests for the Fami Laundry integration.

These tests cover the dataclass + pure helpers; they don't require the full
Home Assistant test scaffolding. Run with:

    python -m pytest tests/ -v
"""
from __future__ import annotations

from custom_components.familaundry.api import FamiLaundryApiError
from custom_components.familaundry.const import DOMAIN
from custom_components.familaundry.coordinator import MachineData, _to_machine
from custom_components.familaundry.entity import (
    device_id_for,
    stable_entity_id,
    stable_object_id,
)


def test_domain_constant() -> None:
    assert DOMAIN == "familaundry"


def test_to_machine_normalizes_raw_payload() -> None:
    """The API returns mixed casing and string-only fields — _to_machine must normalize."""
    raw = {
        "id": "M001",
        "name": "洗+烘",
        "seq": "01",
        "status": "1",
        "FINISH_TIME": "23",
    }
    m = _to_machine(raw)
    assert isinstance(m, MachineData)
    assert m.id == "M001"
    assert m.finish_time == "23"


def test_machine_state_busy_when_running_with_remaining_time() -> None:
    m = MachineData(id="M001", name="洗+烘", seq="01", status="1", finish_time="15")
    assert m.state == "busy"
    assert m.remaining_minutes == 15


def test_machine_state_finish_when_running_with_zero_time() -> None:
    """status=1 + finish_time=0 means cycle done, waiting for pickup."""
    m = MachineData(id="M001", name="洗+烘", seq="01", status="1", finish_time="0")
    assert m.state == "finish"


def test_machine_state_idle_and_offline() -> None:
    assert MachineData("a", "x", "1", "0", "0").state == "idle"
    assert MachineData("a", "x", "1", "2", "0").state == "offline"


def test_machine_state_unknown_for_unexpected_status() -> None:
    """Defensive: unexpected status codes shouldn't crash the entity."""
    assert MachineData("a", "x", "1", "9", "0").state == "unknown"


def test_remaining_minutes_handles_invalid_finish_time() -> None:
    """The API sometimes returns empty strings; entity must coerce safely."""
    assert MachineData("a", "x", "1", "1", "").remaining_minutes == 0
    assert MachineData("a", "x", "1", "1", "abc").remaining_minutes == 0


def test_device_id_for_combines_store_and_machine() -> None:
    assert device_id_for("STORE1", "M001") == "STORE1_M001"


def test_stable_object_id_avoids_pinyin() -> None:
    """object_id stays English-derived to avoid HA's automatic pinyin transform."""
    assert stable_object_id("STORE1", "M001", "status") == "familaundry_STORE1_M001_status"


def test_stable_entity_id_format() -> None:
    assert (
        stable_entity_id("sensor", "STORE1", "M001", "time_remaining")
        == "sensor.familaundry_STORE1_M001_time_remaining"
    )


def test_familaundry_api_error_is_exception() -> None:
    assert issubclass(FamiLaundryApiError, Exception)
    err = FamiLaundryApiError("boom")
    assert str(err) == "boom"
