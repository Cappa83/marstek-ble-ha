"""Config flow for Marstek BLE."""

from __future__ import annotations

import logging
from typing import Any, override

import voluptuous as vol

from homeassistant.components.bluetooth import (
    async_discovered_service_info,
    async_request_active_scan,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_CT_MAC,
    CONF_CT_POLL_INTERVAL,
    CONF_VENUS_DEVICES,
    CONF_VENUS_POLL_INTERVAL,
    DEFAULT_CT_POLL_INTERVAL,
    DEFAULT_VENUS_POLL_INTERVAL,
    DOMAIN,
    MAX_CT_POLL_INTERVAL,
    MAX_VENUS_POLL_INTERVAL,
    MIN_CT_POLL_INTERVAL,
    MIN_VENUS_POLL_INTERVAL,
    RECOMMENDED_MIN_CT_POLL_INTERVAL,
)
from .helpers import normalize_mac, parse_venus_devices

_LOGGER = logging.getLogger(__name__)

CONF_VENUS_NAME = "venus_name"

CT_NAME_PREFIX = "MST-TPM_"
VENUS_NAME_PREFIX = "MST_VNSE3_"

_TEXT = selector.TextSelector(selector.TextSelectorConfig())
_CT_INTERVAL = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=MIN_CT_POLL_INTERVAL,
        max=MAX_CT_POLL_INTERVAL,
        step=1,
        unit_of_measurement="s",
        mode=selector.NumberSelectorMode.BOX,
    )
)
_VENUS_INTERVAL = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=MIN_VENUS_POLL_INTERVAL,
        max=MAX_VENUS_POLL_INTERVAL,
        step=1,
        unit_of_measurement="s",
        mode=selector.NumberSelectorMode.BOX,
    )
)


def _fast_poll_requested(data: dict[str, Any]) -> bool:
    """Return whether a configured CT002 uses sub-recommended polling."""
    return bool(data.get(CONF_CT_MAC)) and int(
        data[CONF_CT_POLL_INTERVAL]
    ) < RECOMMENDED_MIN_CT_POLL_INTERVAL


def _normalize_optional_mac(value: Any) -> str | None:
    """Normalize an optional Bluetooth address."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return normalize_mac(text)


def _normalize_selected(values: list[str] | tuple[str, ...]) -> list[str]:
    """Normalize and de-duplicate selected Bluetooth addresses."""
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        address = normalize_mac(str(value))
        if address in seen:
            continue
        seen.add(address)
        result.append(address)
    return result


def _configured_ct_mac(entry: ConfigEntry) -> str | None:
    """Return the configured CT002 address, including legacy entries."""
    if CONF_CT_MAC in entry.options:
        return _normalize_optional_mac(entry.options.get(CONF_CT_MAC))
    return _normalize_optional_mac(entry.data.get(CONF_CT_MAC))


def _discovered_marstek_devices(
    hass: HomeAssistant,
) -> tuple[dict[str, str], dict[str, str]]:
    """Return connectable CT002 and Venus advertisements known by HA."""
    ct_devices: dict[str, str] = {}
    venus_devices: dict[str, str] = {}

    for info in async_discovered_service_info(hass, connectable=True):
        name = (info.name or "").strip()
        if not name:
            continue

        try:
            address = normalize_mac(info.address)
        except ValueError:
            continue

        upper_name = name.upper()
        if upper_name.startswith(CT_NAME_PREFIX):
            ct_devices[address] = name
        elif upper_name.startswith(VENUS_NAME_PREFIX):
            venus_devices[address] = name

    return ct_devices, venus_devices


def _select_options(devices: dict[str, str]) -> list[dict[str, str]]:
    """Build selector options sorted by advertised/device name."""
    return [
        {"value": address, "label": f"{name} ({address})"}
        for address, name in sorted(devices.items(), key=lambda item: item[1].lower())
    ]


def _device_selector(
    options: list[dict[str, str]], *, multiple: bool
) -> selector.SelectSelector:
    """Build a scan-backed selector with manual MAC fallback."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=multiple,
            custom_value=True,
        )
    )


def _venus_config_string(addresses: list[str], names: dict[str, str]) -> str:
    """Build the persisted Venus device representation."""
    return "\n".join(f"{names[address]}={address}" for address in addresses)


async def _refresh_bluetooth_scan(hass: HomeAssistant) -> None:
    """Request one fresh config-flow scan without making GATT requests."""
    try:
        await async_request_active_scan(hass, duration=3.0)
    except Exception as err:  # Manual MAC entry remains available.
        _LOGGER.debug("Bluetooth config-flow scan failed: %s", err)


class MarstekConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle Marstek BLE setup."""

    VERSION = 4

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> MarstekOptionsFlow:
        return MarstekOptionsFlow()

    async def _async_create_marstek_entry(
        self, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create a validated Marstek BLE config entry."""
        ct_mac = _normalize_optional_mac(user_input.get(CONF_CT_MAC))
        venus_devices = parse_venus_devices(str(user_input[CONF_VENUS_DEVICES]))

        if ct_mac is not None:
            unique_id = ct_mac.replace(":", "").lower()
            title = f"Marstek BLE CT002 {ct_mac[-5:].replace(':', '')}"
        else:
            first_venus = venus_devices[0]
            venus_key = first_venus.address.replace(":", "").lower()
            unique_id = f"venus_{venus_key}"
            if len(venus_devices) == 1:
                title = f"Marstek BLE Venus {venus_key[-4:]}"
            else:
                title = f"Marstek BLE {len(venus_devices)} Venus"

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=title,
            data={},
            options={
                CONF_CT_MAC: ct_mac or "",
                CONF_CT_POLL_INTERVAL: int(user_input[CONF_CT_POLL_INTERVAL]),
                CONF_VENUS_POLL_INTERVAL: int(user_input[CONF_VENUS_POLL_INTERVAL]),
                CONF_VENUS_DEVICES: str(user_input[CONF_VENUS_DEVICES]),
            },
        )

    async def _async_finish_user_devices(self) -> ConfigFlowResult:
        """Finish Venus naming and continue to fast-poll confirmation/create."""
        validated = dict(self._pending_user_base)
        validated[CONF_VENUS_DEVICES] = _venus_config_string(
            self._pending_venus_addresses,
            self._pending_venus_names,
        )

        if _fast_poll_requested(validated):
            self._pending_user_data = validated
            return await self.async_step_confirm_fast_poll()
        return await self._async_create_marstek_entry(validated)

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select discovered devices and polling intervals."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                ct_mac = _normalize_optional_mac(user_input.get(CONF_CT_MAC))
                venus_addresses = _normalize_selected(
                    list(user_input.get(CONF_VENUS_DEVICES, []))
                )
            except ValueError:
                errors["base"] = "invalid_mac"
            else:
                if ct_mac is None and not venus_addresses:
                    errors["base"] = "no_devices"
                else:
                    self._pending_user_base = {
                        CONF_CT_MAC: ct_mac or "",
                        CONF_CT_POLL_INTERVAL: int(
                            user_input[CONF_CT_POLL_INTERVAL]
                        ),
                        CONF_VENUS_POLL_INTERVAL: int(
                            user_input[CONF_VENUS_POLL_INTERVAL]
                        ),
                    }
                    self._pending_venus_addresses = venus_addresses
                    self._pending_venus_names: dict[str, str] = {}
                    self._venus_name_index = 0

                    if venus_addresses:
                        return await self.async_step_venus_name()
                    return await self._async_finish_user_devices()

        if not getattr(self, "_scan_done", False):
            await _refresh_bluetooth_scan(self.hass)
            self._scan_done = True

        ct_devices, venus_devices = _discovered_marstek_devices(self.hass)
        schema = vol.Schema(
            {
                vol.Optional(CONF_CT_MAC): _device_selector(
                    _select_options(ct_devices), multiple=False
                ),
                vol.Optional(CONF_VENUS_DEVICES, default=[]): _device_selector(
                    _select_options(venus_devices), multiple=True
                ),
                vol.Required(
                    CONF_CT_POLL_INTERVAL, default=DEFAULT_CT_POLL_INTERVAL
                ): _CT_INTERVAL,
                vol.Required(
                    CONF_VENUS_POLL_INTERVAL, default=DEFAULT_VENUS_POLL_INTERVAL
                ): _VENUS_INTERVAL,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_venus_name(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Name each selected Venus device individually."""
        address = self._pending_venus_addresses[self._venus_name_index]
        _, discovered_venus = _discovered_marstek_devices(self.hass)
        default_name = discovered_venus.get(
            address, f"Marstek Venus {address.replace(':', '')[-4:].lower()}"
        )

        errors: dict[str, str] = {}
        if user_input is not None:
            name = str(user_input[CONF_VENUS_NAME]).strip()
            if not name:
                errors[CONF_VENUS_NAME] = "empty_name"
            else:
                self._pending_venus_names[address] = name
                self._venus_name_index += 1
                if self._venus_name_index < len(self._pending_venus_addresses):
                    return await self.async_step_venus_name()
                return await self._async_finish_user_devices()

        return self.async_show_form(
            step_id="venus_name",
            data_schema=vol.Schema(
                {vol.Required(CONF_VENUS_NAME, default=default_name): _TEXT}
            ),
            errors=errors,
            description_placeholders={
                "device": discovered_venus.get(address, address),
                "address": address,
                "number": str(self._venus_name_index + 1),
                "total": str(len(self._pending_venus_addresses)),
            },
        )

    async def async_step_confirm_fast_poll(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Require explicit confirmation for CT polling below five seconds."""
        pending = getattr(self, "_pending_user_data", None)
        if pending is None:
            return await self.async_step_user()

        if user_input is not None:
            return await self._async_create_marstek_entry(pending)

        return self.async_show_form(
            step_id="confirm_fast_poll",
            data_schema=vol.Schema({}),
            description_placeholders={
                "seconds": str(pending[CONF_CT_POLL_INTERVAL]),
                "recommended": str(RECOMMENDED_MIN_CT_POLL_INTERVAL),
            },
        )


class MarstekOptionsFlow(OptionsFlowWithReload):
    """Manage Marstek BLE devices and polling."""

    async def _async_finish_options_devices(self) -> ConfigFlowResult:
        """Finish Venus naming and save/confirm the options."""
        options = dict(self._pending_options_base)
        options[CONF_VENUS_DEVICES] = _venus_config_string(
            self._pending_venus_addresses,
            self._pending_venus_names,
        )

        if _fast_poll_requested(options):
            self._pending_options = options
            return await self.async_step_confirm_fast_poll()
        return self.async_create_entry(data=options)

    @override
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select CT002/Venus devices and configure polling."""
        errors: dict[str, str] = {}
        current_ct = _configured_ct_mac(self.config_entry)
        current_devices = parse_venus_devices(
            self.config_entry.options.get(
                CONF_VENUS_DEVICES,
                self.config_entry.data.get(CONF_VENUS_DEVICES, ""),
            )
        )
        current_names = {device.address: device.name for device in current_devices}

        if user_input is not None:
            try:
                ct_mac = _normalize_optional_mac(user_input.get(CONF_CT_MAC))
                venus_addresses = _normalize_selected(
                    list(user_input.get(CONF_VENUS_DEVICES, []))
                )
            except ValueError:
                errors["base"] = "invalid_mac"
            else:
                if ct_mac is None and not venus_addresses:
                    errors["base"] = "no_devices"
                else:
                    self._pending_options_base = {
                        CONF_CT_MAC: ct_mac or "",
                        CONF_CT_POLL_INTERVAL: int(
                            user_input[CONF_CT_POLL_INTERVAL]
                        ),
                        CONF_VENUS_POLL_INTERVAL: int(
                            user_input[CONF_VENUS_POLL_INTERVAL]
                        ),
                    }
                    self._pending_venus_addresses = venus_addresses
                    self._pending_venus_names = {
                        address: current_names[address]
                        for address in venus_addresses
                        if address in current_names
                    }
                    self._venus_name_index = 0

                    if venus_addresses:
                        return await self.async_step_venus_name()
                    return await self._async_finish_options_devices()

        if not getattr(self, "_scan_done", False):
            await _refresh_bluetooth_scan(self.hass)
            self._scan_done = True

        discovered_ct, discovered_venus = _discovered_marstek_devices(self.hass)
        if current_ct is not None:
            discovered_ct.setdefault(current_ct, f"CT002 {current_ct[-5:]}")
        for device in current_devices:
            discovered_venus.setdefault(device.address, device.name)

        if current_ct is not None:
            ct_field = vol.Optional(CONF_CT_MAC, default=current_ct)
        else:
            ct_field = vol.Optional(CONF_CT_MAC)

        schema = vol.Schema(
            {
                ct_field: _device_selector(
                    _select_options(discovered_ct), multiple=False
                ),
                vol.Optional(
                    CONF_VENUS_DEVICES,
                    default=[device.address for device in current_devices],
                ): _device_selector(
                    _select_options(discovered_venus), multiple=True
                ),
                vol.Required(
                    CONF_CT_POLL_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_CT_POLL_INTERVAL, DEFAULT_CT_POLL_INTERVAL
                    ),
                ): _CT_INTERVAL,
                vol.Required(
                    CONF_VENUS_POLL_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_VENUS_POLL_INTERVAL, DEFAULT_VENUS_POLL_INTERVAL
                    ),
                ): _VENUS_INTERVAL,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_venus_name(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Name each selected Venus device individually."""
        address = self._pending_venus_addresses[self._venus_name_index]
        _, discovered_venus = _discovered_marstek_devices(self.hass)

        default_name = self._pending_venus_names.get(
            address,
            discovered_venus.get(
                address, f"Marstek Venus {address.replace(':', '')[-4:].lower()}"
            ),
        )

        errors: dict[str, str] = {}
        if user_input is not None:
            name = str(user_input[CONF_VENUS_NAME]).strip()
            if not name:
                errors[CONF_VENUS_NAME] = "empty_name"
            else:
                self._pending_venus_names[address] = name
                self._venus_name_index += 1
                if self._venus_name_index < len(self._pending_venus_addresses):
                    return await self.async_step_venus_name()
                return await self._async_finish_options_devices()

        return self.async_show_form(
            step_id="venus_name",
            data_schema=vol.Schema(
                {vol.Required(CONF_VENUS_NAME, default=default_name): _TEXT}
            ),
            errors=errors,
            description_placeholders={
                "device": discovered_venus.get(address, address),
                "address": address,
                "number": str(self._venus_name_index + 1),
                "total": str(len(self._pending_venus_addresses)),
            },
        )

    async def async_step_confirm_fast_poll(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Require explicit confirmation for CT polling below five seconds."""
        pending = getattr(self, "_pending_options", None)
        if pending is None:
            return await self.async_step_init()

        if user_input is not None:
            return self.async_create_entry(data=pending)

        return self.async_show_form(
            step_id="confirm_fast_poll",
            data_schema=vol.Schema({}),
            description_placeholders={
                "seconds": str(pending[CONF_CT_POLL_INTERVAL]),
                "recommended": str(RECOMMENDED_MIN_CT_POLL_INTERVAL),
            },
        )
