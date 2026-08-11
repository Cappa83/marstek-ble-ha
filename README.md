# Marstek BLE for Home Assistant

Lokale, read-only Bluetooth-Integration für **Marstek CT002** und **Marstek Venus E V3** in Home Assistant.

---

## Deutsch

### Warum Marstek BLE?

Die Integration liest CT002 und Venus E V3 **direkt per Bluetooth** über den nativen Bluetooth-Stack von Home Assistant aus. Unterstützte Home-Assistant-Bluetooth-Proxys werden transparent mitgenutzt.

Der wesentliche Vorteil gegenüber WLAN-basierten Abfragen ist der deutlich kürzere Datenpfad: Für die hier bereitgestellten Messwerte werden weder WLAN-Verbindung des Marstek-Geräts noch IP-Adresse, DHCP, Router-Erreichbarkeit, Hersteller-Web-API oder Cloud benötigt. Damit entfallen mehrere typische Fehlerquellen von WLAN-/API-Lösungen wie Reconnects, wechselnde IP-Zustände und Netzwerk- oder API-Timeouts.

Bluetooth ist natürlich nicht grundsätzlich störungsfrei. Reichweite und Funkumgebung bleiben relevant. Die Integration ist deshalb bewusst defensiv aufgebaut:

- **CT002:** persistente BLE-Verbindung, solange sie verfügbar ist
- **Venus:** kurze, sequenzielle Verbindungen pro Abfrage
- keine unmittelbaren Retry-Schleifen bei einem fehlgeschlagenen Poll
- letzte gültige Venus-Werte bleiben bei einzelnen Aussetzern erhalten
- aggressive CT002-Abfrageintervalle werden nicht empfohlen
- ausschließlich lesender Zugriff, keine Steuerbefehle an Speicher oder EMS

Ziel ist ein möglichst stabiler, nachvollziehbarer lokaler Datenpfad ohne zusätzliche Netzwerkabhängigkeiten.

### Unterstützte Geräte

#### Marstek CT002

Der CT002 ist **optional**. Die Integration funktioniert auch ausschließlich mit Venus-Geräten.

Bereitgestellte Werte:

- Gesamtleistung
- Phase A / B / C Leistung
- Phase A / B / C Spannung
- BLE-Signalstärke
- Geräteversion

Spannungen, BLE-RSSI und Geräteversion sind standardmäßig als Diagnose-Entitäten deaktiviert.

#### Marstek Venus E V3

Bereitgestellte Werte:

- Ladezustand (SOC)
- Gesundheitszustand (SOH)
- Batteriespannung
- Batteriestrom
- Batterietemperatur
- minimale Zellspannung
- maximale Zellspannung
- Zellspannungsdifferenz
- Designkapazität
- MOSFET-Temperatur
- Fehlercode
- Warncode
- BLE-Signalstärke
- Zellspannung 1 bis 16

Alle Venus-BMS-Werte stammen aus derselben read-only BMS-Antwort `0x14`. Das Aktivieren zusätzlicher Sensoren erzeugt **keine zusätzlichen BLE-Abfragen**.

Bei Venus E V3 wurde für SOH auf ansonsten gesunden/neuen Geräten ein Rohwert `0` beobachtet. Dieser Wert wird deshalb als **nicht verfügbar** behandelt. Gültige Werte von `1` bis `100` bleiben unverändert.

### Unterstützte Konfigurationen

Mindestens ein unterstütztes Gerät muss ausgewählt werden. Möglich sind:

- nur CT002
- eine oder mehrere Venus E V3
- CT002 zusammen mit einer oder mehreren Venus E V3

Der Config Flow durchsucht die aktuell bekannten connectable BLE-Geräte von Home Assistant einschließlich Bluetooth-Proxys.

Erkannt werden derzeit:

- CT002 mit Namen `MST-TPM_…`
- Venus E V3 mit Namen `MST_VNSE3_…`

MAC-Adressen können bei Bedarf weiterhin manuell eingetragen werden. Jede Venus kann in der Einrichtung individuell benannt werden.

### Polling

#### CT002

- Standard: **5 Sekunden**
- Empfehlung: **5 Sekunden oder langsamer**
- einstellbar: **1 bis 300 Sekunden**
- Werte unter 5 Sekunden müssen ausdrücklich bestätigt werden
- unter 5 Sekunden wird zusätzlich eine Warnung im Home-Assistant-Log erzeugt
- ohne konfigurierten CT002 werden CT-Polling-Einstellungen ignoriert

Der CT002 hat sich bei zu aggressivem BLE-Traffic als empfindlich gezeigt. Kürzere Intervalle sind deshalb möglich, aber bewusst nicht die Standardeinstellung.

#### Venus E V3

- Standard: **150 Sekunden**
- einstellbar: **30 bis 3600 Sekunden**
- mehrere Venus werden nacheinander abgefragt
- pro Gerät wird eine BMS-Abfrage ausgeführt und die Verbindung anschließend beendet
- keine sofortige Retry-Schleife bei Fehlern

### Installation mit HACS

Bis das Repository im Standard-HACS-Verzeichnis gelistet ist, wird es als benutzerdefiniertes Repository hinzugefügt:

- Repository: `Cappa83/marstek-ble-ha`
- Typ: `Integration`

Danach **Marstek BLE** über HACS installieren und Home Assistant neu starten.

### Bestehende `marstek_ct`-Installationen

Die Domain bleibt absichtlich `marstek_ct`, damit bestehende Home-Assistant-Installationen sauber migriert werden können.

Die Migration erhält vorhandene Identitäten soweit technisch erforderlich, insbesondere für bereits bestehende CT- und Venus-Entitäten. Ältere UDP-spezifische Felder und Entitäten werden nicht weiter verwendet. Der CT002 ist ab Config-Entry-Version 4 nicht mehr zwingend erforderlich.

Der alte UDP-Runtime-Code ist nicht Bestandteil dieses Repositories.

### Versionsmodell

Ab Version **1.0.0** wird das Projekt als stabile Integration versioniert:

- `1.0.1`: kompatibler Bugfix
- `1.1.0`: kompatible Funktionserweiterung
- `2.0.0`: inkompatible Änderung
- `1.1.0b1` / `1.1.0rc1`: Vorabversionen

`main` ist der Entwicklungsbranch. Veröffentlichungen erfolgen ausschließlich als unveränderliche GitHub Releases/Tags. Eine Änderung der Version in `manifest.json` löst nach erfolgreicher Validierung und den Regressionstests automatisch die Veröffentlichung des zugehörigen Releases aus.

---

## English

Local, read-only Bluetooth integration for **Marstek CT002** and **Marstek Venus E V3** in Home Assistant.

### Why Marstek BLE?

The integration reads CT002 and Venus E V3 **directly over Bluetooth** using Home Assistant's native Bluetooth stack. Compatible Home Assistant Bluetooth proxies are supported transparently.

Compared with Wi-Fi based polling, the telemetry path is significantly shorter: the values exposed by this integration do not depend on the Marstek device's Wi-Fi connection, IP address, DHCP state, router reachability, vendor web API, or cloud service. This removes several common failure modes of Wi-Fi/API based solutions, including reconnects, changing network state, and network or API timeouts.

Bluetooth is not inherently immune to interference. Range and RF conditions still matter. The integration therefore uses a deliberately conservative connection strategy:

- **CT002:** persistent BLE connection while available
- **Venus:** short sequential connections per polling cycle
- no immediate retry loops after a failed poll
- last valid Venus values are retained across isolated failures
- aggressive CT002 polling is discouraged
- read-only operation, with no control commands sent to storage devices or the EMS

The goal is a stable and transparent local telemetry path with as few additional network dependencies as possible.

### Supported devices

#### Marstek CT002

CT002 is **optional**. The integration can also be used with Venus devices only.

Available values:

- total power
- phase A / B / C power
- phase A / B / C voltage
- BLE signal strength
- device version

Voltage, BLE RSSI, and device version entities are disabled by default as diagnostic entities.

#### Marstek Venus E V3

Available values:

- state of charge (SOC)
- state of health (SOH)
- battery voltage
- battery current
- battery temperature
- minimum cell voltage
- maximum cell voltage
- cell voltage delta
- design capacity
- MOSFET temperature
- error code
- warning code
- BLE signal strength
- cell voltage 1 through 16

All Venus BMS values come from the same read-only BMS `0x14` response. Enabling additional sensors does **not** generate additional BLE requests.

A raw SOH value of `0` has been observed on otherwise healthy/new Venus E V3 units. It is therefore treated as **unavailable**. Valid values from `1` through `100` remain unchanged.

### Supported configurations

At least one supported device must be selected. Valid setups are:

- CT002 only
- one or more Venus E V3 devices
- CT002 plus one or more Venus E V3 devices

The config flow scans connectable BLE devices currently known to Home Assistant, including Bluetooth proxies.

Currently detected names:

- CT002: `MST-TPM_…`
- Venus E V3: `MST_VNSE3_…`

Bluetooth MAC addresses can still be entered manually when required. Each selected Venus device can be named individually during setup.

### Polling

#### CT002

- default: **5 seconds**
- recommended: **5 seconds or slower**
- configurable: **1 to 300 seconds**
- intervals below 5 seconds require explicit confirmation
- intervals below 5 seconds also create a Home Assistant log warning
- CT polling settings are ignored when no CT002 is configured

CT002 units have shown sensitivity to overly aggressive BLE traffic. Faster polling remains available, but it is intentionally not the default.

#### Venus E V3

- default: **150 seconds**
- configurable: **30 to 3600 seconds**
- multiple Venus devices are queried sequentially
- each device receives one BMS request and is disconnected afterwards
- no immediate retry loop after failures

### Installation with HACS

Until the repository is listed in the default HACS store, add it as a custom repository:

- Repository: `Cappa83/marstek-ble-ha`
- Type: `Integration`

Then install **Marstek BLE** through HACS and restart Home Assistant.

### Existing `marstek_ct` installations

The domain intentionally remains `marstek_ct` so existing Home Assistant installations can be migrated cleanly.

Migration preserves existing identities where required for entity continuity, including existing CT and Venus entities. Legacy UDP-only configuration fields and entities are no longer used. From config-entry version 4 onward, CT002 is no longer mandatory.

The old UDP runtime code is not part of this repository.

### Versioning

Starting with **1.0.0**, the project uses stable semantic-style releases:

- `1.0.1`: compatible bug fix
- `1.1.0`: compatible feature addition
- `2.0.0`: incompatible change
- `1.1.0b1` / `1.1.0rc1`: pre-release versions

`main` is the development branch. Distribution is done through immutable GitHub Releases/tags. Changing the version in `manifest.json` automatically triggers validation, regression tests, and publication of the corresponding release when all checks pass.

---

## License

Apache License 2.0.

This is an independent community project and is not affiliated with or endorsed by Marstek.
