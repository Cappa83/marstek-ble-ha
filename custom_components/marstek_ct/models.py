"""Data models for Marstek BLE."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VenusDevice:
    """Configured Marstek Venus BLE device."""

    address: str
    name: str

    @property
    def key(self) -> str:
        """Return a stable lower-case MAC key without separators."""
        return self.address.replace(":", "").lower()

    @property
    def suffix(self) -> str:
        """Return the last four MAC characters."""
        return self.key[-4:]
