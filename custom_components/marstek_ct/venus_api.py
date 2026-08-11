"""Read-only BLE polling for Marstek Venus E V3 batteries."""

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

from .models import VenusDevice
from .protocol import BMS_SOC_REQUEST, parse_venus_soc

_LOGGER = logging.getLogger(__name__)

SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
TX_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"
RX_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"
RESPONSE_TIMEOUT = 10.0


class MarstekVenusBleApi:
    """Fetch verified read-only values from configured Venus E V3 units."""

    def __init__(self, hass: HomeAssistant, devices: tuple[VenusDevice, ...]) -> None:
        self._hass = hass
        self._devices = devices
        self._last: dict[str, dict[str, int | None]] = {
            device.key: {"soc": None, "ble_rssi": None} for device in devices
        }

    async def _fetch_one(self, device_config: VenusDevice) -> tuple[int, int | None]:
        address = device_config.address
        name = device_config.name

        device = async_ble_device_from_address(
            self._hass, address, connectable=True
        )
        if device is None:
            raise ConnectionError(
                f"{name} ({address}) is not currently known as connectable "
                "by Home Assistant"
            )

        info = async_last_service_info(self._hass, address, connectable=True)
        rssi = getattr(info, "rssi", None)

        def fresh_device():
            return (
                async_ble_device_from_address(
                    self._hass, address, connectable=True
                )
                or device
            )

        client: BleakClient | None = None
        rx_char: Any | None = None
        notify_started = False
        response_future: asyncio.Future[bytes] = (
            asyncio.get_running_loop().create_future()
        )
        receive_buffer = bytearray()

        def process_buffer() -> None:
            while True:
                while receive_buffer and receive_buffer[0] != 0x73:
                    receive_buffer.pop(0)
                if len(receive_buffer) < 2:
                    return

                frame_length = receive_buffer[1]
                if frame_length < 5:
                    receive_buffer.pop(0)
                    continue
                if len(receive_buffer) < frame_length:
                    return

                raw = bytes(receive_buffer[:frame_length])
                del receive_buffer[:frame_length]
                if len(raw) < 4 or raw[3] != 0x14:
                    continue
                if not response_future.done():
                    response_future.set_result(raw)
                return

        def notification(_sender: Any, data: bytearray) -> None:
            receive_buffer.extend(bytes(data))
            process_buffer()

        try:
            client = await establish_connection(
                BleakClient,
                device,
                name,
                max_attempts=1,
                use_services_cache=False,
                ble_device_callback=fresh_device,
            )

            service = client.services.get_service(SERVICE_UUID)
            if service is None:
                raise ConnectionError(f"{name}: FF00 service not found")

            tx_char = service.get_characteristic(TX_UUID)
            rx_char = service.get_characteristic(RX_UUID)
            if tx_char is None:
                raise ConnectionError(f"{name}: FF01 characteristic not found")
            if rx_char is None:
                raise ConnectionError(f"{name}: FF02 characteristic not found")

            await client.start_notify(rx_char, notification)
            notify_started = True
            await client.write_gatt_char(tx_char, BMS_SOC_REQUEST, response=False)
            raw = await asyncio.wait_for(response_future, timeout=RESPONSE_TIMEOUT)
            return parse_venus_soc(raw), rssi
        finally:
            if (
                client is not None
                and notify_started
                and rx_char is not None
                and client.is_connected
            ):
                try:
                    await client.stop_notify(rx_char)
                except Exception:
                    pass
            if client is not None and client.is_connected:
                try:
                    await client.disconnect()
                except Exception:
                    pass

    async def async_fetch_all(self) -> dict[str, dict[str, int | None]]:
        """Read all configured Venus units sequentially, once per polling cycle."""
        for device in self._devices:
            try:
                soc, rssi = await self._fetch_one(device)
                self._last[device.key] = {"soc": soc, "ble_rssi": rssi}
                _LOGGER.debug(
                    "Marstek Venus %s: soc=%d%% rssi=%s",
                    device.address,
                    soc,
                    rssi,
                )
            except Exception as err:
                _LOGGER.warning(
                    "Marstek Venus %s poll failed: %s: %s; keeping last valid values",
                    device.address,
                    type(err).__name__,
                    err,
                )
        return {key: dict(value) for key, value in self._last.items()}
