"""Data coordinators for Marstek BLE."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble_api import MarstekCtBleApi
from .const import HARD_FAILURE_AFTER
from .venus_api import MarstekVenusBleApi

_LOGGER = logging.getLogger(__name__)


class MarstekCtCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the CT002 while tolerating short BLE interruptions."""

    def __init__(
        self, hass: HomeAssistant, api: MarstekCtBleApi, poll_interval: int
    ) -> None:
        self.api = api
        self._consecutive_failures = 0
        self._last_good_data: dict[str, Any] | None = None
        super().__init__(
            hass,
            _LOGGER,
            name="marstek_ct002",
            update_interval=timedelta(seconds=poll_interval),
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.async_fetch_data()
        except Exception as err:
            self._consecutive_failures += 1
            if (
                self._last_good_data is not None
                and self._consecutive_failures < HARD_FAILURE_AFTER
            ):
                _LOGGER.debug(
                    "Marstek CT BLE poll failed (%d/%d): %s; keeping last valid data",
                    self._consecutive_failures,
                    HARD_FAILURE_AFTER,
                    err,
                )
                return self._last_good_data
            raise UpdateFailed(
                "Marstek CT BLE communication failed after "
                f"{self._consecutive_failures} consecutive poll(s): {err}"
            ) from err

        if self._consecutive_failures:
            _LOGGER.info(
                "Marstek CT BLE communication recovered after %d failed poll(s)",
                self._consecutive_failures,
            )
        self._consecutive_failures = 0
        self._last_good_data = data
        return data


class MarstekVenusCoordinator(
    DataUpdateCoordinator[dict[str, dict[str, int | None]]]
):
    """Poll configured Venus devices at a deliberately slower interval."""

    def __init__(
        self, hass: HomeAssistant, api: MarstekVenusBleApi, poll_interval: int
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="marstek_venus",
            update_interval=timedelta(seconds=poll_interval),
            update_method=api.async_fetch_all,
        )
