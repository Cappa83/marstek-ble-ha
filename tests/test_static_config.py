"""Static integration configuration regression tests without Home Assistant."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_CONST_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "marstek_ct"
    / "const.py"
)
_SPEC = spec_from_file_location("marstek_const", _CONST_PATH)
assert _SPEC is not None and _SPEC.loader is not None
const = module_from_spec(_SPEC)
_SPEC.loader.exec_module(const)


def test_ct_polling_defaults_and_limits() -> None:
    assert const.DEFAULT_CT_POLL_INTERVAL == 5
    assert const.RECOMMENDED_MIN_CT_POLL_INTERVAL == 5
    assert const.MIN_CT_POLL_INTERVAL == 1
    assert const.MAX_CT_POLL_INTERVAL == 300


def test_legacy_cleanup_preserves_total_power() -> None:
    assert "total_power" not in const.LEGACY_CT_SENSOR_KEYS
    assert "wifi_rssi" in const.LEGACY_CT_SENSOR_KEYS
    assert "ABC_chrg_power" in const.LEGACY_CT_SENSOR_KEYS
    assert "ABC_dchrg_power" in const.LEGACY_CT_SENSOR_KEYS
