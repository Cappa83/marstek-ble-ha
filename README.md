# Marstek BLE for Home Assistant

**Stabile, schnelle und vollständig lokale BLE-Integration für Marstek CT Smart Meter / CT002 und Marstek Venus E V3 in Home Assistant.**

Marstek BLE liest die unterstützten Geräte direkt über den nativen Bluetooth-Stack von Home Assistant aus. Home-Assistant-Bluetooth-Proxys werden unterstützt. Für die bereitgestellten Messwerte sind weder WLAN noch IP-Adresse, DHCP, UDP, Hersteller-Web-API oder Cloud-Zugriff des Marstek-Geräts erforderlich.

---

## Deutsch

### Highlights

- vollständig lokale BLE-Kommunikation
- **automatische Geräteerkennung über den Home-Assistant Config Flow**
- Discovery über lokale Bluetooth-Adapter und Home-Assistant-Bluetooth-Proxys
- CT002 optional: CT-only, Venus-only oder gemischter Betrieb
- CT002 standardmäßig alle **5 Sekunden**
- persistente BLE-Verbindung zum CT002
- sequenzielle, kurze Venus-Abfragen
- eine einzige Venus-BMS-Abfrage aktualisiert alle unterstützten BMS-Sensoren
- keine zusätzlichen BLE-Abfragen durch das Aktivieren weiterer Venus-Sensoren
- read-only: keine Steuerbefehle an Speicher oder EMS

### Automatische Erkennung / Config Flow

Die Einrichtung erfolgt vollständig über den Home-Assistant **Config Flow**.

Beim Öffnen der Integration fordert Marstek BLE einen aktuellen Bluetooth-Scan von Home Assistant an und nutzt dessen zentrale Bluetooth-Discovery. Dadurch werden Geräte nicht nur über einen lokalen Bluetooth-Adapter gefunden, sondern auch über registrierte **Home-Assistant-Bluetooth-Proxys**.

Automatisch erkannt werden derzeit:

- **CT002 / CT Smart Meter:** Gerätenamen `MST-TPM_…`
- **Venus E V3:** Gerätenamen `MST_VNSE3_…`

Gefundene Geräte können direkt ausgewählt werden. Mehrere Venus-Geräte werden gemeinsam erkannt und anschließend einzeln benannt.

Falls ein Gerät während der Einrichtung nicht sichtbar ist, kann die Bluetooth-MAC-Adresse weiterhin manuell eingetragen werden. Bereits konfigurierte Geräte bleiben in den Optionen erhalten, auch wenn sie bei einem späteren Scan vorübergehend nicht sichtbar sind.

### Warum BLE statt WLAN / UDP?

Der Datenpfad ist kurz und lokal. Für die hier bereitgestellten Messwerte kommuniziert Home Assistant direkt per BLE mit CT002 und Venus E V3.

Dadurch entfallen zusätzliche Abhängigkeiten wie:

- WLAN-Verbindung des Marstek-Geräts
- DHCP und IP-Adresse
- Router-Erreichbarkeit
- UDP-Kommunikation
- Hersteller-Web-API
- Cloud-Dienste

Das reduziert die Zahl möglicher Fehlerstellen und ermöglicht insbesondere beim CT002 kurze, regelmäßige Aktualisierungsintervalle. Bluetooth bleibt Funkkommunikation: Reichweite, Störungen und die Position von Bluetooth-Adapter oder Proxy sind weiterhin relevant.

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
| Verhalten bei Einzel-Aussetzern | keine unmittelbare Retry-Schleife, letzte gültige Venus-Werte bleiben erhalten | implementierungsabhängig |

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

### Polling

#### CT002

- Standard: **5 Sekunden**
- Empfehlung: **5 Sekunden oder langsamer**
- einstellbar: **1 bis 300 Sekunden**
- Werte unter 5 Sekunden müssen ausdrücklich bestätigt werden
- unter 5 Sekunden wird zusätzlich eine Warnung im Home-Assistant-Log erzeugt
- ohne konfigurierten CT002 werden CT-Polling-Einstellungen ignoriert

Kürzere Intervalle erhöhen die BLE-Last und sind deshalb bewusst nicht die Standardeinstellung.

#### Venus E V3

- Standard: **150 Sekunden**
- einstellbar: **30 bis 3600 Sekunden**
- mehrere Venus werden nacheinander abgefragt
- pro Gerät wird eine BMS-Abfrage ausgeführt und die Verbindung anschließend beendet
- keine sofortige Retry-Schleife bei Fehlern
- letzte gültige Werte bleiben bei einzelnen fehlgeschlagenen Abfragen erhalten

### Installation mit HACS

Bis das Repository im Standard-HACS-Verzeichnis gelistet ist, wird es als benutzerdefiniertes Repository hinzugefügt:

- Repository: `Cappa83/marstek-ble-ha`
- Typ: `Integration`

Danach **Marstek BLE** über HACS installieren, Home Assistant neu starten und die Integration unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen. Der Config Flow übernimmt anschließend die Bluetooth-Erkennung.

### Versionsmodell

Ab Version **1.0.0** wird das Projekt als stabile Integration versioniert:

- `1.0.1`: kompatibler Bugfix
- `1.1.0`: kompatible Funktionserweiterung
- `2.0.0`: inkompatible Änderung
- `1.1.0b1` / `1.1.0rc1`: Vorabversionen

`main` ist der Entwicklungsbranch. Veröffentlichungen erfolgen als GitHub Releases/Tags nach Validierung und Regressionstests.

---

## English

**Stable, fast and fully local BLE integration for Marstek CT Smart Meter / CT002 and Marstek Venus E V3 in Home Assistant.**

Marstek BLE reads supported devices directly through Home Assistant's native Bluetooth stack. Home Assistant Bluetooth proxies are supported. The exposed telemetry does not require the Marstek device's Wi-Fi connection, IP address, DHCP, UDP, vendor web API or cloud access.

### Highlights

- fully local BLE communication
- **automatic device discovery through the Home Assistant Config Flow**
- discovery through local Bluetooth adapters and Home Assistant Bluetooth proxies
- optional CT002: CT-only, Venus-only or mixed setups
- CT002 defaults to **5-second** polling
- persistent BLE connection to CT002
- short sequential Venus connections
- one Venus BMS request updates all supported BMS sensors
- enabling additional Venus sensors does not create additional BLE requests
- read-only operation with no control commands sent to storage devices or the EMS

### Automatic discovery / Config Flow

Setup is handled entirely through the Home Assistant **Config Flow**.

When the integration is opened, Marstek BLE requests a fresh Bluetooth scan from Home Assistant and uses Home Assistant's central Bluetooth discovery. Devices can therefore be discovered through both local Bluetooth adapters and registered **Home Assistant Bluetooth proxies**.

Currently discovered automatically:

- **CT002 / CT Smart Meter:** device names `MST-TPM_…`
- **Venus E V3:** device names `MST_VNSE3_…`

Discovered devices can be selected directly. Multiple Venus devices are discovered together and can then be named individually.

If a device is not visible during setup, its Bluetooth MAC address can still be entered manually. Already configured devices remain available in the options even if they are temporarily not visible during a later scan.

### Why BLE instead of Wi-Fi / UDP?

The telemetry path is short and local. Home Assistant communicates directly with CT002 and Venus E V3 over BLE for the values exposed by this integration.

This removes additional dependencies such as:

- the Marstek device's Wi-Fi connection
- DHCP and IP addressing
- router reachability
- UDP communication
- vendor web APIs
- cloud services

This reduces the number of possible failure points and allows short, regular update intervals, especially for CT002. Bluetooth is still radio communication: range, interference, and Bluetooth adapter or proxy placement remain relevant.

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
| Isolated failure handling | no immediate retry loop, last valid Venus values retained | implementation-dependent |

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

### Polling

#### CT002

- default: **5 seconds**
- recommended: **5 seconds or slower**
- configurable: **1 to 300 seconds**
- intervals below 5 seconds require explicit confirmation
- intervals below 5 seconds also create a Home Assistant log warning
- CT polling settings are ignored when no CT002 is configured

Shorter intervals increase BLE traffic and are intentionally not the default.

#### Venus E V3

- default: **150 seconds**
- configurable: **30 to 3600 seconds**
- multiple Venus devices are queried sequentially
- each device receives one BMS request and is disconnected afterwards
- no immediate retry loop after failures
- last valid values are retained across isolated failed polls

### Installation with HACS

Until the repository is listed in the default HACS store, add it as a custom repository:

- Repository: `Cappa83/marstek-ble-ha`
- Type: `Integration`

Then install **Marstek BLE** through HACS, restart Home Assistant and open the integration under **Settings → Devices & services → Add integration**. The Config Flow then handles Bluetooth discovery.

### Versioning

Starting with **1.0.0**, the project uses stable semantic-style releases:

- `1.0.1`: compatible bug fix
- `1.1.0`: compatible feature addition
- `2.0.0`: incompatible change
- `1.1.0b1` / `1.1.0rc1`: pre-release versions

`main` is the development branch. Releases are published as GitHub Releases/tags after validation and regression testing.

---

## License

Apache License 2.0.

This is an independent community project and is not affiliated with or endorsed by Marstek.
