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

- CT002 default and recommended interval: **5 seconds**
- CT002 configurable range: **1 to 300 seconds**
- intervals below **5 seconds** require explicit confirmation and also generate a warning in the Home Assistant log
- Venus default: **150 seconds**
- Venus configurable range: **30 to 3600 seconds**
- one connection attempt per polling cycle; no immediate retry loop
- CT002 uses one persistent BLE connection while available
- Venus devices are queried sequentially and disconnected after each read

The CT002 has shown sensitivity to aggressive BLE traffic in real-world use. Faster polling is therefore available for users who want to test it, but individual devices may become less stable below the recommended 5-second interval.

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

The Home Assistant domain remains `marstek_ct` intentionally. Migration keeps the existing CT total-power entity identity intact, removes obsolete UDP-era entities, converts the config-entry unique ID to the CT002 MAC, and drops UDP-only config fields that are no longer used. The legacy battery MAC is retained only where an existing CT entity/device identity still depends on it.

The old UDP runtime code is not part of this repository.

## Installation with HACS

Until this repository is added to the default HACS store, add it as a custom integration repository and install **Marstek BLE**.

Repository: `Cappa83/marstek-ble-ha`

## License

Apache License 2.0.

This is an independent community project and is not affiliated with or endorsed by Marstek.
