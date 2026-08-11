"""Validation and configuration helpers for Marstek BLE."""

from __future__ import annotations

import re

from .models import VenusDevice

_HEX_RE = re.compile(r"^[0-9A-Fa-f]{12}$")
_SPLIT_RE = re.compile(r"[\n,;]+")


def normalize_mac(value: str) -> str:
    """Normalize a Bluetooth MAC address to AA:BB:CC:DD:EE:FF."""
    compact = value.strip().replace(":", "").replace("-", "")
    if not _HEX_RE.fullmatch(compact):
        raise ValueError(f"Invalid Bluetooth MAC address: {value!r}")
    compact = compact.upper()
    return ":".join(compact[index : index + 2] for index in range(0, 12, 2))


def parse_venus_devices(value: str | None) -> tuple[VenusDevice, ...]:
    """Parse Venus devices from a multiline/comma-separated string.

    Accepted entries:
      AA:BB:CC:DD:EE:FF
      Name=AA:BB:CC:DD:EE:FF
    """
    if not value or not value.strip():
        return ()

    devices: list[VenusDevice] = []
    seen: set[str] = set()

    for raw_entry in _SPLIT_RE.split(value):
        entry = raw_entry.strip()
        if not entry:
            continue

        if "=" in entry:
            name, raw_address = entry.split("=", 1)
            name = name.strip()
            if not name:
                raise ValueError("Venus device name may not be empty")
        else:
            name = ""
            raw_address = entry

        address = normalize_mac(raw_address)
        key = address.replace(":", "").lower()

        if key in seen:
            raise ValueError(f"Duplicate Venus Bluetooth MAC: {address}")
        seen.add(key)

        if not name:
            name = f"Marstek Venus {key[-4:]}"

        devices.append(VenusDevice(address=address, name=name))

    return tuple(devices)


def canonicalize_venus_devices(value: str | None) -> str:
    """Return a canonical multiline representation of configured Venus devices."""
    return "\n".join(
        f"{device.name}={device.address}" for device in parse_venus_devices(value)
    )
