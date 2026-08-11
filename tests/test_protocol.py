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
    payload.extend(b"\xaa\xbb")  # unverified runtime tail must be ignored

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


def test_parse_venus_soc() -> None:
    payload = bytearray(10)
    payload[8:10] = (73).to_bytes(2, "little")
    assert protocol.parse_venus_soc(_frame(0x14, bytes(payload))) == 73
