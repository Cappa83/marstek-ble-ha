# Marstek BLE for Home Assistant

**Stabile, schnelle und vollständig lokale BLE-Integration für Marstek CT Smart Meter / CT002 und Marstek Venus E V3 in Home Assistant.**

Unterstützt HACS, den nativen Home-Assistant-Bluetooth-Stack und Home-Assistant-Bluetooth-Proxys. Kein Cloud-Zwang, keine Hersteller-Web-API und für die bereitgestellten Messwerte keine WLAN-, IP-, DHCP- oder UDP-Abhängigkeit des Marstek-Geräts.

---

## Deutsch

### Warum Marstek BLE?

Marstek BLE liest **CT002 und Venus E V3 direkt per Bluetooth** über den nativen Bluetooth-Stack von Home Assistant aus. Unterstützte Bluetooth-Proxys werden transparent verwendet.

Der Datenpfad ist bewusst kurz und lokal. Für die hier bereitgestellten Messwerte sind weder das WLAN des Marstek-Geräts noch IP-Adresse, DHCP, Router-Erreichbarkeit, UDP-Kommunikation, Hersteller-Web-API oder Cloud erforderlich.

In der produktiven Referenzinstallation hat sich dieser BLE-Datenpfad gegenüber den zuvor getesteten WLAN-/UDP-Implementierungen als **stabiler und schneller** erwiesen. Das ist kein Versprechen, dass Bluetooth in jeder Funkumgebung störungsfrei ist. Reichweite, Störungen und Proxy-Position bleiben relevante physikalische Faktoren.

Die Integration ist deshalb defensiv aufgebaut:

- **CT002:** persistente BLE-Verbindung, solange sie verfügbar ist
- **Venus:** kurze, sequenzielle Verbindungen pro Abfrage
- keine unmittelbaren Retry-Schleifen nach einem fehlgeschlagenen Poll
- letzte gültige Venus-Werte bleiben bei einzelnen Aussetzern erhalten
- CT002-Polling standardmäßig alle **5 Sekunden**
- aggressivere CT002-Intervalle müssen ausdrücklich bestätigt werden
- ausschließlich lesender Zugriff, keine Steuerbefehle an Speicher oder EMS

### BLE gegenüber WLAN / UDP

| Eigenschaft | Marstek BLE | WLAN-/UDP-basierter Datenpfad |
|---|---|---|
| Transport | direktes lokales BLE | WLAN + IP/UDP |
| DHCP / IP-Adresse nötig | nein | typischerweise ja |
| Router-/WLAN-Erreichbarkeit des Marstek-Geräts nötig | nein | ja |
| Hersteller-Cloud / Web-API nötig | nein | je nach Implementierung |
| Home-Assistant-Bluetooth-Proxys | ja | nicht relevant |
| CT002 Standardintervall | 5 s | implementierungsabhängig |
| CT002 Verbindung | persistent | implementierungsabhängig |
| Venus-Abfragen | sequenziell, eine BMS-Anfrage pro Gerät | implementierungsabhängig |
| Verhalten bei Einzel-Aussetzern | keine Retry-Schleife, letzte gültige Venus-Werte bleiben erhalten | implementierungsabhängig |

### Unterstützte Geräte

#### Marstek CT002 / Marstek CT Smart Meter

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

### Versionsmodell

Ab Version **1.0.0** wird das Projekt als stabile Integration versioniert:

- `1.0.1`: kompatibler Bugfix
- `1.1.0`: kompatible Funktionserweiterung
- `2.0.0`: inkompatible Änderung
- `1.1.0b1` / `1.1.0rc1`: Vorabversionen

`main` ist der Entwicklungsbranch. Veröffentlichungen erfolgen ausschließlich als unveränderliche GitHub Releases/Tags. Eine Änderung der Version in `manifest.json` löst nach erfolgreicher Validierung und den Regressionstests automatisch die Veröffentlichung des zugehörigen Releases aus.

---

## English

**Stable, fast and fully local BLE integration for Marstek CT Smart Meter / CT002 and Marstek Venus E V3 in Home Assistant.**

Supports HACS, Home Assistant's native Bluetooth stack and Home Assistant Bluetooth proxies. No cloud dependency, no vendor web API, and no Wi-Fi, IP, DHCP or UDP dependency on the Marstek device for the exposed telemetry.

### Why Marstek BLE?

Marstek BLE reads **CT002 and Venus E V3 directly over Bluetooth** using Home Assistant's native Bluetooth stack. Compatible Bluetooth proxies are supported transparently.

The telemetry path is deliberately short and local. The values exposed by this integration do not depend on the Marstek device's Wi-Fi connection, IP address, DHCP state, router reachability, UDP communication, vendor web API or cloud service.

In the production reference installation, this BLE data path proved **more stable and faster** than the previously tested Wi-Fi/UDP implementations. This does not mean Bluetooth is immune to RF problems. Range, interference and proxy placement still matter.

The integration therefore uses a deliberately conservative connection strategy:

- **CT002:** persistent BLE connection while available
- **Venus:** short sequential connections per polling cycle
- no immediate retry loops after a failed poll
- last valid Venus values are retained across isolated failures
- CT002 polling defaults to **5 seconds**
- more aggressive CT002 intervals require explicit confirmation
- read-only operation, with no control commands sent to storage devices or the EMS

### BLE compared with Wi-Fi / UDP

| Property | Marstek BLE | Wi-Fi / UDP data path |
|---|---|---|
| Transport | direct local BLE | Wi-Fi + IP/UDP |
| DHCP / IP address required | no | typically yes |
| Marstek device router/Wi-Fi reachability required | no | yes |
| Vendor cloud / web API required | no | implementation-dependent |
| Home Assistant Bluetooth proxies | yes | not applicable |
| CT002 default interval | 5 s | implementation-dependent |
| CT002 connection | persistent | implementation-dependent |
| Venus polling | sequential, one BMS request per device | implementation-dependent |
| Isolated failure handling | no retry loop, last valid Venus values retained | implementation-dependent |

### Supported devices

#### Marstek CT002 / Marstek CT Smart Meter

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
