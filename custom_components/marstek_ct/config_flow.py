"""Config flow for Marstek BLE."""

from __future__ import annotations

from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
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
from .helpers import canonicalize_venus_devices, normalize_mac

_TEXT = selector.TextSelector(selector.TextSelectorConfig())
_MULTILINE = selector.TextSelector(selector.TextSelectorConfig(multiline=True))
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

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CT_MAC): _TEXT,
        vol.Optional(CONF_VENUS_DEVICES, default=""): _MULTILINE,
        vol.Required(CONF_CT_POLL_INTERVAL, default=DEFAULT_CT_POLL_INTERVAL): _CT_INTERVAL,
        vol.Required(
            CONF_VENUS_POLL_INTERVAL, default=DEFAULT_VENUS_POLL_INTERVAL
        ): _VENUS_INTERVAL,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CT_POLL_INTERVAL): _CT_INTERVAL,
        vol.Required(CONF_VENUS_POLL_INTERVAL): _VENUS_INTERVAL,
        vol.Optional(CONF_VENUS_DEVICES): _MULTILINE,
    }
)


def _fast_poll_requested(data: dict[str, Any]) -> bool:
    """Return whether CT polling is below the recommended interval."""
    return int(data[CONF_CT_POLL_INTERVAL]) < RECOMMENDED_MIN_CT_POLL_INTERVAL


class MarstekConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle Marstek BLE setup."""

    VERSION = 3

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> MarstekOptionsFlow:
        return MarstekOptionsFlow()

    async def _async_create_marstek_entry(
        self, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create a validated Marstek BLE config entry."""
        ct_mac = str(user_input[CONF_CT_MAC])
        await self.async_set_unique_id(ct_mac.replace(":", "").lower())
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Marstek BLE CT002 {ct_mac[-5:].replace(':', '')}",
            data={CONF_CT_MAC: ct_mac},
            options={
                CONF_CT_POLL_INTERVAL: int(user_input[CONF_CT_POLL_INTERVAL]),
                CONF_VENUS_POLL_INTERVAL: int(user_input[CONF_VENUS_POLL_INTERVAL]),
                CONF_VENUS_DEVICES: str(user_input[CONF_VENUS_DEVICES]),
            },
        )

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                ct_mac = normalize_mac(str(user_input[CONF_CT_MAC]))
                venus_devices = canonicalize_venus_devices(
                    str(user_input.get(CONF_VENUS_DEVICES, ""))
                )
            except ValueError:
                errors["base"] = "invalid_mac"
            else:
                validated = {
                    CONF_CT_MAC: ct_mac,
                    CONF_CT_POLL_INTERVAL: int(user_input[CONF_CT_POLL_INTERVAL]),
                    CONF_VENUS_POLL_INTERVAL: int(
                        user_input[CONF_VENUS_POLL_INTERVAL]
                    ),
                    CONF_VENUS_DEVICES: venus_devices,
                }
                if _fast_poll_requested(validated):
                    self._pending_user_data = validated
                    return await self.async_step_confirm_fast_poll()
                return await self._async_create_marstek_entry(validated)

        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
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
    """Manage Marstek BLE polling and Venus devices."""

    @override
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                venus_devices = canonicalize_venus_devices(
                    str(user_input.get(CONF_VENUS_DEVICES, ""))
                )
            except ValueError:
                errors[CONF_VENUS_DEVICES] = "invalid_mac"
            else:
                options = {
                    CONF_CT_POLL_INTERVAL: int(user_input[CONF_CT_POLL_INTERVAL]),
                    CONF_VENUS_POLL_INTERVAL: int(
                        user_input[CONF_VENUS_POLL_INTERVAL]
                    ),
                    CONF_VENUS_DEVICES: venus_devices,
                }
                if _fast_poll_requested(options):
                    self._pending_options = options
                    return await self.async_step_confirm_fast_poll()
                return self.async_create_entry(data=options)

        current = {
            CONF_CT_POLL_INTERVAL: self.config_entry.options.get(
                CONF_CT_POLL_INTERVAL, DEFAULT_CT_POLL_INTERVAL
            ),
            CONF_VENUS_POLL_INTERVAL: self.config_entry.options.get(
                CONF_VENUS_POLL_INTERVAL, DEFAULT_VENUS_POLL_INTERVAL
            ),
            CONF_VENUS_DEVICES: self.config_entry.options.get(
                CONF_VENUS_DEVICES,
                self.config_entry.data.get(CONF_VENUS_DEVICES, ""),
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(OPTIONS_SCHEMA, current),
            errors=errors,
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
