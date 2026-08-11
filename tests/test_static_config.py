"""Static integration configuration regression tests without Home Assistant."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CONST_PATH = _ROOT / "custom_components" / "marstek_ct" / "const.py"
_CONFIG_FLOW_PATH = _ROOT / "custom_components" / "marstek_ct" / "config_flow.py"
_INIT_PATH = _ROOT / "custom_components" / "marstek_ct" / "__init__.py"
_SENSOR_PATH = _ROOT / "custom_components" / "marstek_ct" / "sensor.py"

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


def test_ct002_is_optional_in_config_flow() -> None:
    source = _CONFIG_FLOW_PATH.read_text()
    assert "VERSION = 4" in source
    assert "vol.Optional(CONF_CT_MAC)" in source
    assert "if ct_mac is None and not venus_addresses" in source
    assert 'errors["base"] = "no_devices"' in source


def test_runtime_supports_venus_without_ct002() -> None:
    init_source = _INIT_PATH.read_text()
    sensor_source = _SENSOR_PATH.read_text()

    assert "ct_coordinator: MarstekCtCoordinator | None" in init_source
    assert "ct_api: MarstekCtBleApi | None" in init_source
    assert "if ct_mac is not None:" in init_source
    assert "if ct_coordinator is not None:" in init_source
    assert "if runtime.ct_coordinator is not None and runtime.ct_mac is not None" in sensor_source
