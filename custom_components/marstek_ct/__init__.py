"""Marstek BLE integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .ble_api import MarstekCtBleApi
from .const import (
    CONF_CT_MAC,
    CONF_CT_POLL_INTERVAL,
    CONF_VENUS_DEVICES,
    CONF_VENUS_POLL_INTERVAL,
    DEFAULT_CT_POLL_INTERVAL,
    DEFAULT_VENUS_POLL_INTERVAL,
    DOMAIN,
    LEGACY_CT_SENSOR_KEYS,
    RECOMMENDED_MIN_CT_POLL_INTERVAL,
)
from .coordinator import MarstekCtCoordinator, MarstekVenusCoordinator
from .helpers import normalize_mac, parse_venus_devices
from .models import VenusDevice
from .venus_api import MarstekVenusBleApi

_LOGGER = logging.getLogger(__name__)

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

    if ct_poll_interval < RECOMMENDED_MIN_CT_POLL_INTERVAL:
        _LOGGER.warning(
            "CT002 polling interval is %ss; values below the recommended %ss may "
            "increase BLE/device load and can destabilize some CT002 units",
            ct_poll_interval,
            RECOMMENDED_MIN_CT_POLL_INTERVAL,
        )

    ct_api = MarstekCtBleApi(hass, ct_mac)
    ct_coordinator = MarstekCtCoordinator(hass, entry, ct_api, ct_poll_interval)

    venus_coordinator: MarstekVenusCoordinator | None = None
    if venus_devices:
        venus_api = MarstekVenusBleApi(hass, venus_devices)
        venus_coordinator = MarstekVenusCoordinator(
            hass, entry, venus_api, venus_poll_interval
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


def _remove_legacy_ct_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove obsolete UDP-era CT entities while preserving current BLE entities."""
    registry = er.async_get(hass)
    legacy_suffixes = tuple(f"_{key}" for key in LEGACY_CT_SENSOR_KEYS)

    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if registry_entry.platform != DOMAIN:
            continue
        if not registry_entry.entity_id.startswith(f"{Platform.SENSOR.value}."):
            continue
        if not registry_entry.unique_id.endswith(legacy_suffixes):
            continue
        registry.async_remove(registry_entry.entity_id)
        _LOGGER.info("Removed obsolete Marstek CT entity %s", registry_entry.entity_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate entries created by older Marstek CT integration versions."""
    if entry.version > 3:
        return False

    data: dict[str, Any] = dict(entry.data)

    if entry.version < 2:
        if CONF_CT_MAC not in data:
            return False
        data[CONF_CT_MAC] = normalize_mac(str(data[CONF_CT_MAC]))
        data.pop("host", None)

    if entry.version < 3:
        if CONF_CT_MAC not in data:
            return False
        data[CONF_CT_MAC] = normalize_mac(str(data[CONF_CT_MAC]))
        _remove_legacy_ct_entities(hass, entry)
        data.pop("ct_type", None)
        data.pop("device_type", None)

    ct_mac = str(data[CONF_CT_MAC])
    hass.config_entries.async_update_entry(
        entry,
        data=data,
        title=f"Marstek BLE CT002 {ct_mac[-5:].replace(':', '')}",
        unique_id=ct_mac.replace(":", "").lower(),
        version=3,
    )

    return True
