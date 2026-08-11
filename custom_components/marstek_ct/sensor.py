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
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MarstekRuntimeData
from .const import CT_MODEL, DOMAIN, VENUS_MODEL


@dataclass(frozen=True, kw_only=True)
class MarstekCtSensorDescription(SensorEntityDescription):
    """CT sensor description."""


@dataclass(frozen=True, kw_only=True)
class MarstekVenusSensorDescription(SensorEntityDescription):
    """Venus sensor description."""


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


VENUS_SENSORS: tuple[MarstekVenusSensorDescription, ...] = (
    MarstekVenusSensorDescription(
        key="soc",
        translation_key="venus_soc",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MarstekVenusSensorDescription(
        key="soh",
        translation_key="venus_soh",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MarstekVenusSensorDescription(
        key="battery_voltage",
        translation_key="venus_battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    MarstekVenusSensorDescription(
        key="battery_current",
        translation_key="venus_battery_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    MarstekVenusSensorDescription(
        key="battery_temperature",
        translation_key="venus_battery_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    MarstekVenusSensorDescription(
        key="cell_voltage_min",
        translation_key="venus_cell_voltage_min",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MarstekVenusSensorDescription(
        key="cell_voltage_max",
        translation_key="venus_cell_voltage_max",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MarstekVenusSensorDescription(
        key="cell_voltage_delta",
        translation_key="venus_cell_voltage_delta",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MarstekVenusSensorDescription(
        key="design_capacity",
        translation_key="venus_design_capacity",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MarstekVenusSensorDescription(
        key="mosfet_temperature",
        translation_key="venus_mosfet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MarstekVenusSensorDescription(
        key="error_code",
        translation_key="venus_error_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MarstekVenusSensorDescription(
        key="warning_code",
        translation_key="venus_warning_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    MarstekVenusSensorDescription(
        key="ble_rssi",
        translation_key="venus_ble_rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
) + tuple(
    MarstekVenusSensorDescription(
        key=f"cell_voltage_{cell}",
        translation_key="venus_cell_voltage",
        translation_placeholders={"cell": str(cell)},
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )
    for cell in range(1, 17)
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek BLE sensors."""
    runtime: MarstekRuntimeData = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    if runtime.ct_coordinator is not None and runtime.ct_mac is not None:
        entities.extend(
            MarstekCtSensor(
                runtime.ct_coordinator,
                description,
                entry,
                runtime.ct_mac,
            )
            for description in CT_SENSORS
        )

    if runtime.venus_coordinator is not None:
        for device in runtime.venus_devices:
            entities.extend(
                MarstekVenusSensor(
                    runtime.venus_coordinator,
                    device.address,
                    device.name,
                    description,
                )
                for description in VENUS_SENSORS
            )

    async_add_entities(entities)


class MarstekCtSensor(CoordinatorEntity, SensorEntity):
    """One CT002 sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: MarstekCtSensorDescription,
        entry: ConfigEntry,
        ct_mac: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

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
    """One Venus BLE sensor sourced from the shared BMS poll."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        address: str,
        name: str,
        description: MarstekVenusSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._device_key = address.replace(":", "").lower()

        # Preserve the existing SOC and BLE-RSSI unique-id shapes while using
        # the same deterministic suffix pattern for all new BMS sensors.
        self._attr_unique_id = f"marstek_venus_{self._device_key}_{description.key}"
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
        return device_data.get(self.entity_description.key)
