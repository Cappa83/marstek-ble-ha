"""Protocol tests that can run without Home Assistant installed."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_PROTOCOL_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "marstek_ct"
    / "protocol.py"
)
_SPEC = spec_from_file_location("marstek_protocol", _PROTOCOL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
protocol = module_from_spec(_SPEC)
_SPEC.loader.exec_module(protocol)


def _frame(command: int, payload: bytes) -> bytes:
    raw = bytearray([0x73, len(payload) + 5, 0x23, command])
    raw.extend(payload)
    checksum = 0
    for byte in raw:
        checksum ^= byte
    raw.append(checksum)
    return bytes(raw)


def test_runtime_request_checksum() -> None:
    assert protocol.xor_checksum(protocol.RUNTIME_REQUEST) == 0


def test_bms_soc_request_checksum() -> None:
    assert protocol.xor_checksum(protocol.BMS_SOC_REQUEST) == 0


def test_parse_ct_runtime_signed_power() -> None:
    payload = bytearray()
    payload.append(124)
    payload.extend((231).to_bytes(2, "little"))
    payload.extend((232).to_bytes(2, "little"))
    payload.extend((233).to_bytes(2, "little"))
    payload.extend((-125).to_bytes(2, "little", signed=True))
    payload.extend((640).to_bytes(2, "little", signed=True))
    payload.extend((-15).to_bytes(2, "little", signed=True))
    payload.extend((500).to_bytes(2, "little", signed=True))
    payload.extend(b"\xaa\xbb")

    data = protocol.parse_ct_runtime(_frame(0x03, bytes(payload)))

    assert data == {
        "device_version": 124,
        "voltage_a": 231,
        "voltage_b": 232,
        "voltage_c": 233,
        "phase_a_power": -125,
        "phase_b_power": 640,
        "phase_c_power": -15,
        "total_power": 500,
    }


def test_parse_venus_soc_compatibility() -> None:
    payload = bytearray(10)
    payload[8:10] = (73).to_bytes(2, "little")
    assert protocol.parse_venus_soc(_frame(0x14, bytes(payload))) == 73


def test_parse_live_venus_bms_frame() -> None:
    raw = bytes.fromhex(
        "73 55 23 14 "
        "71 00 40 02 e8 03 e8 03 2c 00 00 00 00 14 c7 14 "
        "56 00 1a 00 03 00 e5 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 67 01 52 01 08 01 f7 00 fa 00 02 01 "
        "fa 0c fd 0c fc 0c fc 0c fb 0c fe 0c fc 0c fb 0c "
        "fb 0c fe 0c fc 0c fc 0c fb 0c fc 0c fb 0c fb 0c "
        "56"
    )

    data = protocol.parse_venus_bms(raw)

    assert data["soc"] == 44
    assert data["soh"] is None
    assert data["design_capacity"] == 5120
    assert data["battery_voltage"] == 53.19
    assert data["battery_current"] == 8.6
    assert data["battery_temperature"] == 26.0
    assert data["error_code"] == 0
    assert data["warning_code"] == 0
    assert data["mosfet_temperature"] == 33.8

    assert data["cell_voltage_1"] == 3.322
    assert data["cell_voltage_16"] == 3.323
    assert data["cell_voltage_min"] == 3.322
    assert data["cell_voltage_max"] == 3.326
    assert data["cell_voltage_delta"] == 0.004


def test_parse_venus_bms_preserves_real_soh_percentage() -> None:
    payload = bytearray(48)
    payload[8:10] = (62).to_bytes(2, "little")
    payload[10:12] = (98).to_bytes(2, "little")

    data = protocol.parse_venus_bms(_frame(0x14, bytes(payload)))

    assert data["soc"] == 62
    assert data["soh"] == 98
