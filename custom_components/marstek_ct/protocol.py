"""Verified Marstek BLE protocol parsing used by the integration."""

from __future__ import annotations

from typing import Any

RUNTIME_REQUEST = bytes.fromhex("73 05 23 03 56")
BMS_SOC_REQUEST = bytes.fromhex("73 05 23 14 41")


def xor_checksum(data: bytes) -> int:
    """Return XOR checksum over all bytes."""
    value = 0
    for byte in data:
        value ^= byte
    return value


def validate_frame(raw: bytes) -> None:
    """Validate the common Marstek BLE frame envelope."""
    if len(raw) < 5:
        raise ValueError(f"BLE response too short: {len(raw)} bytes")
    if raw[0] != 0x73:
        raise ValueError(f"Invalid start byte: 0x{raw[0]:02x}")
    if raw[1] != len(raw):
        raise ValueError(
            f"BLE frame length mismatch: declared={raw[1]} actual={len(raw)}"
        )
    if raw[2] != 0x23:
        raise ValueError(f"Invalid protocol byte: 0x{raw[2]:02x}")
    checksum = xor_checksum(raw)
    if checksum != 0:
        raise ValueError(f"Invalid BLE XOR checksum: 0x{checksum:02x}")


def parse_ct_runtime(raw: bytes) -> dict[str, Any]:
    """Decode the verified CT002 Runtime Info (command 0x03) fields."""
    validate_frame(raw)
    if raw[3] != 0x03:
        raise ValueError(f"Unexpected BLE command response: 0x{raw[3]:02x}")

    payload = raw[4:-1]

    # Observed and validated CT002 HME-4 v124 layout:
    # 00      uint8      device version
    # 01..02  uint16 LE  phase A voltage
    # 03..04  uint16 LE  phase B voltage
    # 05..06  uint16 LE  phase C voltage
    # 07..08  int16 LE   phase A power
    # 09..10  int16 LE   phase B power
    # 11..12  int16 LE   phase C power
    # 13..14  int16 LE   total power
    # Bytes from offset 15 onward intentionally remain uninterpreted.
    if len(payload) < 15:
        raise ValueError(f"CT002 Runtime Info payload too short: {len(payload)} bytes")

    return {
        "device_version": payload[0],
        "voltage_a": int.from_bytes(payload[1:3], "little", signed=False),
        "voltage_b": int.from_bytes(payload[3:5], "little", signed=False),
        "voltage_c": int.from_bytes(payload[5:7], "little", signed=False),
        "phase_a_power": int.from_bytes(payload[7:9], "little", signed=True),
        "phase_b_power": int.from_bytes(payload[9:11], "little", signed=True),
        "phase_c_power": int.from_bytes(payload[11:13], "little", signed=True),
        "total_power": int.from_bytes(payload[13:15], "little", signed=True),
    }


def _normalize_bms_temperature(raw: int) -> float:
    """Normalize Marstek BMS temperature values to degrees Celsius."""
    return raw / 10 if raw > 100 else float(raw)


def parse_venus_bms(raw: bytes) -> dict[str, Any]:
    """Decode verified Venus BMS Data fields from command 0x14.

    The same 0x14 response already used for SOC also contains SOH, capacity,
    voltage/current, temperatures, status codes and per-cell voltages.
    No additional BLE request is required.
    """
    validate_frame(raw)
    if raw[3] != 0x14:
        raise ValueError(f"Unexpected response command: 0x{raw[3]:02x}")

    payload = raw[4:-1]
    if len(payload) < 48:
        raise ValueError(f"BMS payload too short: {len(payload)}")

    soc = int.from_bytes(payload[8:10], "little", signed=False)
    if not 0 <= soc <= 100:
        raise ValueError(f"Invalid SOC value: {soc}")

    # Venus E V3 units have been observed returning 0 for SOH even on new,
    # otherwise healthy batteries. Treat 0 as an unavailable/sentinel value;
    # real percentage values remain 1..100.
    soh_raw = int.from_bytes(payload[10:12], "little", signed=False)
    soh: int | None = soh_raw if 1 <= soh_raw <= 100 else None

    result: dict[str, Any] = {
        "soc": soc,
        "soh": soh,
        "design_capacity": int.from_bytes(payload[12:14], "little", signed=False),
        "battery_voltage": int.from_bytes(payload[14:16], "little", signed=False) / 100,
        "battery_current": int.from_bytes(payload[16:18], "little", signed=True) / 10,
        "battery_temperature": _normalize_bms_temperature(
            int.from_bytes(payload[18:20], "little", signed=False)
        ),
        "error_code": int.from_bytes(payload[26:28], "little", signed=False),
        "warning_code": int.from_bytes(payload[28:32], "little", signed=False),
        "mosfet_temperature": _normalize_bms_temperature(
            int.from_bytes(payload[38:40], "little", signed=False)
        ),
    }

    cells: list[float] = []
    for offset in range(48, min(len(payload), 82) - 1, 2):
        millivolts = int.from_bytes(payload[offset : offset + 2], "little")
        if 0 < millivolts < 5000:
            cells.append(millivolts / 1000)

    for index, voltage in enumerate(cells, start=1):
        result[f"cell_voltage_{index}"] = voltage

    if cells:
        result["cell_voltage_min"] = min(cells)
        result["cell_voltage_max"] = max(cells)
        result["cell_voltage_delta"] = round(max(cells) - min(cells), 3)

    return result


def parse_venus_soc(raw: bytes) -> int:
    """Decode the verified Venus SOC field from command 0x14."""
    validate_frame(raw)
    if raw[3] != 0x14:
        raise ValueError(f"Unexpected response command: 0x{raw[3]:02x}")

    payload = raw[4:-1]
    if len(payload) < 10:
        raise ValueError(f"BMS payload too short: {len(payload)}")

    soc = int.from_bytes(payload[8:10], "little", signed=False)
    if not 0 <= soc <= 100:
        raise ValueError(f"Invalid SOC value: {soc}")
    return soc
