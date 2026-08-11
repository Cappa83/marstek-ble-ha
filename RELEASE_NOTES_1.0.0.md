# Marstek BLE 1.0.0

## Deutsch

Erstes stabiles Release von **Marstek BLE** für Home Assistant.

### Enthalten

- lokale, read-only BLE-Anbindung für **Marstek CT002**
- lokale, read-only BLE-Anbindung für **Marstek Venus E V3**
- CT002 optional: Venus-only, CT-only und kombinierte Setups werden unterstützt
- native Home-Assistant-Bluetooth-Unterstützung einschließlich kompatibler Bluetooth-Proxys
- CT002 mit persistenter BLE-Verbindung
- Venus-Geräte mit kurzen, sequenziellen Verbindungen pro Poll
- keine unmittelbaren Retry-Schleifen bei fehlgeschlagenen Abfragen
- vollständige Venus-BMS-Auswertung aus der vorhandenen `0x14`-Antwort ohne zusätzliche BLE-Abfragen
- SOC, SOH, Spannung, Strom, Temperatur, Zellspannungen, Zellspannungsdifferenz sowie Diagnosewerte
- SOH-Rohwert `0` wird bei Venus E V3 als nicht verfügbar behandelt
- bestehende `marstek_ct`-Installationen können unter Beibehaltung wichtiger Entity-Identitäten migriert werden
- HACS-kompatible Installation und Release-Verteilung

### Stabilität und Architektur

Die Messwerte werden direkt per BLE ausgelesen. Für diesen Datenpfad werden weder WLAN-Verbindung des Marstek-Geräts noch IP-Adresse, DHCP, Hersteller-Web-API oder Cloud benötigt. Dadurch entfallen mehrere typische Fehlerquellen WLAN-/API-basierter Telemetrie.

Bluetooth-Reichweite und Funkumgebung bleiben weiterhin relevant. Die Integration verwendet deshalb konservative Polling- und Verbindungsstrategien und sendet ausschließlich lesende Anfragen.

## English

First stable release of **Marstek BLE** for Home Assistant.

### Included

- local, read-only BLE support for **Marstek CT002**
- local, read-only BLE support for **Marstek Venus E V3**
- CT002 is optional: Venus-only, CT-only, and combined setups are supported
- native Home Assistant Bluetooth support, including compatible Bluetooth proxies
- persistent BLE connection for CT002
- short sequential connections for Venus devices per polling cycle
- no immediate retry loops after failed polls
- complete Venus BMS decoding from the existing `0x14` response without additional BLE requests
- SOC, SOH, voltage, current, temperature, cell voltages, cell delta, and diagnostic values
- Venus E V3 SOH raw value `0` is treated as unavailable
- existing `marstek_ct` installations can migrate while preserving important entity identities
- HACS-compatible installation and release distribution

### Stability and architecture

Telemetry is read directly over BLE. This data path does not depend on the Marstek device's Wi-Fi connection, IP address, DHCP state, vendor web API, or cloud service, removing several common failure modes of Wi-Fi/API based telemetry.

Bluetooth range and RF conditions still matter. The integration therefore uses conservative polling and connection strategies and sends read-only requests only.
