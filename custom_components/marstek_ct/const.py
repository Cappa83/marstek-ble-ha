"""Constants for Marstek BLE."""

DOMAIN = "marstek_ct"

CONF_CT_MAC = "ct_mac"
CONF_CT_POLL_INTERVAL = "ct_poll_interval"
CONF_VENUS_POLL_INTERVAL = "venus_poll_interval"
CONF_VENUS_DEVICES = "venus_devices"

DEFAULT_CT_POLL_INTERVAL = 5
RECOMMENDED_MIN_CT_POLL_INTERVAL = 5
MIN_CT_POLL_INTERVAL = 1
MAX_CT_POLL_INTERVAL = 300

DEFAULT_VENUS_POLL_INTERVAL = 150
MIN_VENUS_POLL_INTERVAL = 30
MAX_VENUS_POLL_INTERVAL = 3600

CT_MODEL = "CT002"
VENUS_MODEL = "Venus E V3"

HARD_FAILURE_AFTER = 4

# Entity keys exposed by the former UDP-based integration. ``total_power`` is
# intentionally absent because that entity is preserved across migration.
LEGACY_CT_SENSOR_KEYS = (
    "wifi_rssi",
    "A_phase_power",
    "B_phase_power",
    "C_phase_power",
    "meter_dev_type",
    "meter_mac_code",
    "hhm_dev_type",
    "hhm_mac_code",
    "info_idx",
    "A_chrg_nb",
    "B_chrg_nb",
    "C_chrg_nb",
    "ABC_chrg_nb",
    "x_chrg_power",
    "A_chrg_power",
    "B_chrg_power",
    "C_chrg_power",
    "ABC_chrg_power",
    "x_dchrg_power",
    "A_dchrg_power",
    "B_dchrg_power",
    "C_dchrg_power",
    "ABC_dchrg_power",
)
