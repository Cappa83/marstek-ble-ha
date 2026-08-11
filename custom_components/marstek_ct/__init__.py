"""Marstek BLE integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .ble_api import MarstekCtBleApi
from .const import (
    CONF_CT_MAC,
    CONF_CT_POLL_INTERVAL,
    CONF_VENUS_DEVICES,
    CONF_VENUS_POLL_INTERVAL,
    DEFAULT_CT_POLL_INTERVAL,
    DEFAULT_VENUS_POLL_INTERVAL,
    DOMAIN,
)
from .coordinator import MarstekCtCoordinator, MarstekVenusCoordinator
from .helpers import normalize_mac, parse_venus_devices
from .models import VenusDevice
from .venus_api import MarstekVenusBleApi

PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass(slots=True)
class MarstekRuntimeData:
    """Runtime objects for one config entry."""

    ct_coordinator: MarstekCtCoordinator
    ct_api: MarstekCtBleApi
    venus_coordinator: MarstekVenusCoordinator | None
    venus_devices: tuple[VenusDevice, ...]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Marstek BLE from a config entry without blocking HA startup."""
    ct_mac = normalize_mac(entry.data[CONF_CT_MAC])
    ct_poll_interval = int(
        entry.options.get(CONF_CT_POLL_INTERVAL, DEFAULT_CT_POLL_INTERVAL)
    )
    venus_poll_interval = int(
        entry.options.get(CONF_VENUS_POLL_INTERVAL, DEFAULT_VENUS_POLL_INTERVAL)
    )
    venus_devices = parse_venus_devices(
        entry.options.get(
            CONF_VENUS_DEVICES,
            entry.data.get(CONF_VENUS_DEVICES, ""),
        )
    )

    ct_api = MarstekCtBleApi(hass, ct_mac)
    ct_coordinator = MarstekCtCoordinator(hass, ct_api, ct_poll_interval)

    venus_coordinator: MarstekVenusCoordinator | None = None
    if venus_devices:
        venus_api = MarstekVenusBleApi(hass, venus_devices)
        venus_coordinator = MarstekVenusCoordinator(
            hass, venus_api, venus_poll_interval
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = MarstekRuntimeData(
        ct_coordinator=ct_coordinator,
        ct_api=ct_api,
        venus_coordinator=venus_coordinator,
        venus_devices=venus_devices,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_create_background_task(
        hass,
        ct_coordinator.async_refresh(),
        f"{DOMAIN}-{entry.entry_id}-initial-ct-refresh",
    )
    if venus_coordinator is not None:
        entry.async_create_background_task(
            hass,
            venus_coordinator.async_refresh(),
            f"{DOMAIN}-{entry.entry_id}-initial-venus-refresh",
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    runtime: MarstekRuntimeData | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    if runtime is not None:
        await runtime.ct_api.async_disconnect()
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate entries created by the former UDP-based integration."""
    if entry.version > 2:
        return False

    if entry.version < 2:
        data: dict[str, Any] = dict(entry.data)
        if CONF_CT_MAC not in data:
            return False
        data[CONF_CT_MAC] = normalize_mac(str(data[CONF_CT_MAC]))
        data.pop("host", None)

        hass.config_entries.async_update_entry(
            entry,
            data=data,
            title=f"Marstek BLE CT002 {data[CONF_CT_MAC][-5:].replace(':', '')}",
            version=2,
        )

    return True
