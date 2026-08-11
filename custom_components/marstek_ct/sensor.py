"""Sensor platform for Marstek BLE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricPotential,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MarstekRuntimeData
from .const import CT_MODEL, DOMAIN, VENUS_MODEL


@dataclass(frozen=True, kw_only=True)
class MarstekCtSensorDescription(SensorEntityDescription):
    """CT sensor description."""


CT_SENSORS: tuple[MarstekCtSensorDescription, ...] = (
    MarstekCtSensorDescription(
        key="total_power",
        translation_key="total_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MarstekCtSensorDescription(
        key="phase_a_power",
        translation_key="phase_a_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MarstekCtSensorDescription(
        key="phase_b_power",
        translation_key="phase_b_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MarstekCtSensorDescription(
        key="phase_c_power",
        translation_key="phase_c_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MarstekCtSensorDescription(
        key="voltage_a",
        translation_key="voltage_a",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MarstekCtSensorDescription(
        key="voltage_b",
        translation_key="voltage_b",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MarstekCtSensorDescription(
        key="voltage_c",
        translation_key="voltage_c",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MarstekCtSensorDescription(
        key="ble_rssi",
        translation_key="ble_rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MarstekCtSensorDescription(
        key="device_version",
        translation_key="device_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek BLE sensors."""
    runtime: MarstekRuntimeData = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        MarstekCtSensor(runtime.ct_coordinator, description, entry)
        for description in CT_SENSORS
    ]

    if runtime.venus_coordinator is not None:
        for device in runtime.venus_devices:
            entities.append(
                MarstekVenusSensor(
                    runtime.venus_coordinator,
                    device.address,
                    device.name,
                    "soc",
                )
            )
            entities.append(
                MarstekVenusSensor(
                    runtime.venus_coordinator,
                    device.address,
                    device.name,
                    "ble_rssi",
                )
            )

    async_add_entities(entities)


class MarstekCtSensor(CoordinatorEntity, SensorEntity):
    """One CT002 sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, description, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        ct_mac = str(entry.data["ct_mac"])
        normalized = ct_mac.replace(":", "").replace("-", "").lower()
        legacy_battery_mac = entry.data.get("battery_mac")

        if legacy_battery_mac:
            # Preserve the exact legacy ConfigEntry value because the former
            # integration used it verbatim in CT unique IDs/device identifiers.
            legacy_battery = str(legacy_battery_mac)
            self._attr_unique_id = f"{normalized}_{legacy_battery}_{description.key}"
            device_identifier = f"{normalized}_{legacy_battery}"
        else:
            self._attr_unique_id = f"{normalized}_{description.key}"
            device_identifier = normalized

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_identifier)},
            "name": f"Marstek CT002 {normalized[-4:]}",
            "manufacturer": "Marstek",
            "model": CT_MODEL,
        }

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        return data.get(self.entity_description.key)


class MarstekVenusSensor(CoordinatorEntity, SensorEntity):
    """One verified Venus BLE sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, address: str, name: str, key: str) -> None:
        super().__init__(coordinator)
        self._device_key = address.replace(":", "").lower()
        self._value_key = key

        if key == "soc":
            self._attr_translation_key = "venus_soc"
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            suffix = "soc"
        else:
            self._attr_translation_key = "venus_ble_rssi"
            self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
            self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = False
            suffix = "ble_rssi"

        # Preserve the existing SOC unique-id shape from the live installation.
        self._attr_unique_id = f"marstek_venus_{self._device_key}_{suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"marstek_venus_{self._device_key}")},
            "name": name,
            "manufacturer": "Marstek",
            "model": VENUS_MODEL,
        }

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        device_data = data.get(self._device_key) or {}
        return device_data.get(self._value_key)
