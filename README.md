# Marstek BLE for Home Assistant

Read-only, local Bluetooth integration for Home Assistant.

Current verified support:

- **Marstek CT002**
  - total power
  - phase A/B/C power
  - phase A/B/C voltage (diagnostic, disabled by default)
  - BLE RSSI (diagnostic, disabled by default)
  - raw device version byte (diagnostic, disabled by default)
- **Marstek Venus E V3**
  - state of charge (SOC)
  - BLE RSSI (diagnostic, disabled by default)

The integration uses Home Assistant's native Bluetooth stack, so compatible Home Assistant Bluetooth proxies can be used transparently.

## Important design limits

This integration is **read-only**. It does not control charging, discharging, or the Marstek EMS.

Only protocol fields that were verified against live devices are exposed. Unknown bytes are deliberately left uninterpreted until their meaning has been independently verified.

### Polling

- CT002 default: **5 seconds**
- CT002 minimum: **5 seconds**
- Venus default: **150 seconds**
- Venus minimum: **30 seconds**
- one connection attempt per polling cycle; no immediate retry loop
- CT002 uses one persistent BLE connection while available
- Venus devices are queried sequentially and disconnected after each read

The CT002 has shown sensitivity to aggressive BLE traffic in real-world use. The integration therefore refuses CT polling intervals below 5 seconds.

## Configuration

Add **Marstek BLE** from Home Assistant's integrations UI.

Required:

- CT002 Bluetooth MAC address

Optional Venus devices can be entered one per line:

```text
Battery 1=00:11:22:33:44:55
Battery 2=66:77:88:99:AA:BB
```

A bare MAC address is also accepted; a display name will then be generated automatically.

Polling intervals and the Venus device list can be changed later under **Configure**. Saving the options reloads the integration automatically.

## Existing `marstek_ct` installations

The Home Assistant domain remains `marstek_ct` intentionally. Version 0.1.0 includes a migration path for older config entries that still contain the former UDP integration's `host`, `battery_mac`, `device_type`, or `ct_type` fields. Legacy identity fields are retained where needed so existing CT entity registry entries can keep their unique IDs.

The old UDP runtime code is not part of this repository.

## Installation with HACS

Until this repository is added to the default HACS store, add it as a custom integration repository and install **Marstek BLE**.

Repository: `Cappa83/marstek-ble-ha`

## License

Apache License 2.0.

This is an independent community project and is not affiliated with or endorsed by Marstek.
