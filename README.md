# Marstek BLE for Home Assistant

Read-only, local Bluetooth integration for Home Assistant.

Current verified support:

- **Marstek CT002**
  - optional: the integration also works with Venus devices only
  - total power
  - phase A/B/C power
  - phase A/B/C voltage (diagnostic, disabled by default)
  - BLE RSSI (diagnostic, disabled by default)
  - raw device version byte (diagnostic, disabled by default)
- **Marstek Venus E V3**
  - state of charge (SOC)
  - state of health (SOH); a raw value of `0` is treated as unavailable because Venus E V3 units have been observed reporting `0` on otherwise healthy/new batteries
  - battery voltage and signed battery current
  - battery temperature
  - minimum, maximum and delta cell voltage
  - design capacity (diagnostic, disabled by default)
  - MOSFET temperature (diagnostic, disabled by default)
  - BMS error and warning codes (diagnostic, disabled by default)
  - 16 individual cell voltages (diagnostic, disabled by default)
  - BLE RSSI (diagnostic, disabled by default)

All Venus BMS values above come from the same read-only `0x14` response that is already used for SOC. Enabling the additional sensors does **not** add BLE requests or increase the Venus polling frequency.

The integration uses Home Assistant's native Bluetooth stack, so compatible Home Assistant Bluetooth proxies can be used transparently.

## Important design limits

This integration is **read-only**. It does not control charging, discharging, or the Marstek EMS.

Only protocol fields that were verified against live devices and the community-documented Marstek HM BLE layout are exposed. Unknown bytes are deliberately left uninterpreted until their meaning has been independently verified.

### Polling

- CT002 default and recommended interval: **5 seconds**
- CT002 configurable range: **1 to 300 seconds**
- intervals below **5 seconds** require explicit confirmation and also generate a warning in the Home Assistant log
- CT002 polling settings are ignored when no CT002 is configured
- Venus default: **150 seconds**
- Venus configurable range: **30 to 3600 seconds**
- one connection attempt per polling cycle; no immediate retry loop
- CT002 uses one persistent BLE connection while available
- Venus devices are queried sequentially and disconnected after each read
- one Venus poll sends one BMS `0x14` request and updates all Venus BMS sensors from that response

The CT002 has shown sensitivity to aggressive BLE traffic in real-world use. Faster polling is therefore available for users who want to test it, but individual devices may become less stable below the recommended 5-second interval.

## Configuration

Add **Marstek BLE** from Home Assistant's integrations UI.

The config flow requests a fresh Home Assistant Bluetooth scan and offers detected Marstek devices from all registered scanners, including Bluetooth proxies:

- CT002 advertisements named `MST-TPM_…`
- Venus E V3 advertisements named `MST_VNSE3_…`

CT002 and Venus devices are independent. A valid configuration contains at least one of them:

- CT002 only
- one or more Venus devices only
- CT002 plus one or more Venus devices

Each selected Venus is named individually. Manual Bluetooth MAC entry remains available as a fallback.

Polling intervals and both the CT002 and Venus device selection can be changed later under **Configure**. Already configured devices remain selectable even if they are temporarily not visible during a scan. Saving the options reloads the integration automatically.

Internally the existing `Name=Bluetooth-MAC` Venus representation is retained. Existing v3 entries migrate to config-entry version 4 without changing the historic CT entity/device identities.

## Existing `marstek_ct` installations

The Home Assistant domain remains `marstek_ct` intentionally. Migration keeps the existing CT total-power entity identity intact, removes obsolete UDP-era entities, preserves legacy identifiers that are still required for entity continuity, and moves the configurable CT002 selection into options so it can be added or removed without making CT002 mandatory.

The old UDP runtime code is not part of this repository.

## Installation with HACS

Until this repository is added to the default HACS store, add it as a custom integration repository and install **Marstek BLE**.

Repository: `Cappa83/marstek-ble-ha`

GitHub pre-releases can be installed through HACS when pre-releases are enabled for this repository.

## Versioning and releases

The project uses semantic-style versions:

- patch release, for example `0.3.1`: compatible bug fix
- minor release, for example `0.4.0`: compatible feature addition
- beta/RC, for example `0.3.0b1` or `0.3.0rc1`: test release before the corresponding stable version

`main` is the development branch. HACS distribution is done through immutable GitHub Releases/tags, not through release branches.

Publishing is handled by the **Publish release** GitHub Action. It accepts the version from `manifest.json`, compiles the integration, validates JSON, runs the regression tests, and only then creates `v<version>`. Versions containing `a`, `b`, or `rc` are published as GitHub pre-releases.

## License

Apache License 2.0.

This is an independent community project and is not affiliated with or endorsed by Marstek.
