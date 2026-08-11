# Marstek BLE 0.2.1b1

Pre-release for testing the Venus E V3 SOH handling.

## Changed

- Treat Venus BMS SOH raw value `0` as unavailable instead of displaying `0 %`.
- Preserve real SOH values from `1` through `100` unchanged.
- No additional BLE request is introduced; the value continues to come from the existing BMS `0x14` response.

## Regression coverage

- The captured live Venus E V3 BMS frame with SOH raw `0` is expected to decode as unavailable.
- A synthetic SOH raw value of `98` is expected to decode as `98 %`.
