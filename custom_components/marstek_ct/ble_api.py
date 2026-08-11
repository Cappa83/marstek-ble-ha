"""Native Home Assistant BLE API for the Marstek CT002."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakClient
from bleak_retry_connector import establish_connection

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_last_service_info,
)
from homeassistant.core import HomeAssistant

from .helpers import normalize_mac
from .protocol import RUNTIME_REQUEST, parse_ct_runtime, validate_frame

_LOGGER = logging.getLogger(__name__)

SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
TX_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"
RX_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"
RESPONSE_TIMEOUT = 3.0


class MarstekCtBleApi:
    """Persistent read-only BLE connection to a Marstek CT002."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        self._hass = hass
        self._address = normalize_mac(address)
        self._client: BleakClient | None = None
        self._tx_char: Any | None = None
        self._rx_char: Any | None = None
        self._connect_lock = asyncio.Lock()
        self._request_lock = asyncio.Lock()
        self._response_future: asyncio.Future[bytes] | None = None
        self._closing = False

    @property
    def address(self) -> str:
        """Return the normalized BLE address."""
        return self._address

    def _fresh_device(self):
        return async_ble_device_from_address(
            self._hass, self._address, connectable=True
        )

    def _disconnected(self, client: BleakClient) -> None:
        if client is self._client:
            self._client = None
            self._tx_char = None
            self._rx_char = None

        future = self._response_future
        if future is not None and not future.done():
            future.set_exception(
                ConnectionError(f"CT002 {self._address} disconnected during request")
            )

        if not self._closing:
            _LOGGER.warning("Marstek CT BLE disconnected: %s", self._address)

    def _notification(self, _sender: Any, data: bytearray) -> None:
        raw = bytes(data)
        try:
            validate_frame(raw)
        except Exception as err:
            _LOGGER.warning(
                "Ignoring invalid Marstek CT BLE frame: %s; raw=%s",
                err,
                raw.hex(" "),
            )
            return

        if raw[3] != 0x03:
            _LOGGER.debug(
                "Ignoring unrelated Marstek CT BLE response cmd=0x%02x", raw[3]
            )
            return

        future = self._response_future
        if future is None or future.done():
            _LOGGER.debug("Ignoring unsolicited Marstek CT Runtime Info response")
            return
        future.set_result(raw)

    async def _drop_connection(self) -> None:
        client = self._client
        self._client = None
        self._tx_char = None
        self._rx_char = None
        if client is None or not client.is_connected:
            return

        self._closing = True
        try:
            await client.disconnect()
        except Exception as err:
            _LOGGER.debug("Error while disconnecting Marstek CT BLE: %s", err)
        finally:
            self._closing = False

    async def _ensure_connected(self) -> None:
        if (
            self._client is not None
            and self._client.is_connected
            and self._tx_char is not None
            and self._rx_char is not None
        ):
            return

        async with self._connect_lock:
            if (
                self._client is not None
                and self._client.is_connected
                and self._tx_char is not None
                and self._rx_char is not None
            ):
                return

            device = self._fresh_device()
            if device is None:
                raise ConnectionError(
                    f"CT002 {self._address} is not currently known as connectable "
                    "by Home Assistant"
                )

            info = async_last_service_info(
                self._hass, self._address, connectable=True
            )
            name = (
                getattr(info, "name", None)
                or getattr(device, "name", None)
                or f"Marstek CT {self._address}"
            )

            _LOGGER.info(
                "Connecting to Marstek CT via Home Assistant BLE: %s (%s)",
                name,
                self._address,
            )

            client = await establish_connection(
                BleakClient,
                device,
                name,
                disconnected_callback=self._disconnected,
                max_attempts=1,
                use_services_cache=False,
                ble_device_callback=self._fresh_device,
            )

            try:
                service = client.services.get_service(SERVICE_UUID)
                if service is None:
                    raise ConnectionError(f"Service {SERVICE_UUID} not found")

                tx_char = service.get_characteristic(TX_UUID)
                rx_char = service.get_characteristic(RX_UUID)
                if tx_char is None:
                    raise ConnectionError(f"TX characteristic {TX_UUID} not found")
                if rx_char is None:
                    raise ConnectionError(f"RX characteristic {RX_UUID} not found")

                self._client = client
                self._tx_char = tx_char
                self._rx_char = rx_char
                await client.start_notify(rx_char, self._notification)
            except Exception:
                self._client = None
                self._tx_char = None
                self._rx_char = None
                if client.is_connected:
                    try:
                        await client.disconnect()
                    except Exception:
                        pass
                raise

            _LOGGER.info("Marstek CT BLE connected and FF02 notifications active")

    async def async_fetch_data(self) -> dict[str, Any]:
        """Fetch one Runtime Info dataset over the persistent BLE link."""
        async with self._request_lock:
            await self._ensure_connected()

            client = self._client
            tx_char = self._tx_char
            if client is None or tx_char is None or not client.is_connected:
                raise ConnectionError(
                    "Marstek CT BLE connection vanished before request"
                )

            future: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()
            self._response_future = future
            try:
                await client.write_gatt_char(tx_char, RUNTIME_REQUEST, response=False)
                raw = await asyncio.wait_for(future, timeout=RESPONSE_TIMEOUT)
                data = parse_ct_runtime(raw)
                info = async_last_service_info(
                    self._hass, self._address, connectable=True
                )
                data["ble_rssi"] = getattr(info, "rssi", None)
                return data
            finally:
                if self._response_future is future:
                    self._response_future = None

    async def async_disconnect(self) -> None:
        """Disconnect cleanly when the config entry unloads."""
        future = self._response_future
        if future is not None and not future.done():
            future.cancel()
        self._response_future = None
        await self._drop_connection()
