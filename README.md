[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?style=flat&logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat&logo=hacs&logoColor=white)](https://hacs.xyz/)
[![Version](https://img.shields.io/github/v/release/Q14siX/strato_dyndns_service?style=flat&color=41BDF5&label=Version)](https://github.com/Q14siX/strato_dyndns_service/releases/latest)
[![Maintained](https://img.shields.io/badge/Maintained%3F-yes-41BDF5?style=flat)](#)
[![Stars](https://img.shields.io/github/stars/Q14siX/strato_dyndns_service?style=flat&logo=github&color=41BDF5&label=Stars)](https://github.com/Q14siX/strato_dyndns_service/stargazers)
[![Languages](https://img.shields.io/badge/Languages-DE%20%7C%20EN-41BDF5?style=flat&logo=translate&logoColor=white)](#english)
[![License](https://img.shields.io/github/license/Q14siX/strato_dyndns_service?style=flat&color=41BDF5&label=License)](https://github.com/Q14siX/strato_dyndns_service/blob/main/LICENSE)
[![Downloads](https://img.shields.io/github/downloads/Q14siX/strato_dyndns_service/total?style=flat&color=41BDF5&label=Downloads)](https://github.com/Q14siX/strato_dyndns_service/releases/latest)
[![Issues](https://img.shields.io/github/issues/Q14siX/strato_dyndns_service?style=flat&color=41BDF5&label=Issues)](https://github.com/Q14siX/strato_dyndns_service/issues)

# STRATO DynDNS Service

<p align="center">
  <img src="https://raw.githubusercontent.com/Q14siX/strato_dyndns_service/main/custom_components/strato_dyndns_service/brand/icon.png" alt="STRATO DynDNS Service icon" width="128">
</p>

[English version](#english)

STRATO DynDNS Service ist eine benutzerdefinierte Home-Assistant-Integration für den STRATO-DynDNS-Dienst. Sie wurde dafür entwickelt, mehrere STRATO-Domains und Subdomains komfortabel direkt in Home Assistant zu verwalten, gezielt oder gesammelt zu aktualisieren, per Webhook durch einen Router wie eine FRITZ!Box anzustoßen und die Ergebnisse nachvollziehbar in Geräten, Sensoren, Schaltern, Tastern, Services und Blueprints abzubilden.

## Inhalt

- [Validierung und Veröffentlichung](#validierung-und-veröffentlichung)
- [Warum diese Integration?](#warum-diese-integration)
- [Funktionsumfang](#funktionsumfang)
- [Besondere Merkmale](#besondere-merkmale)
- [Voraussetzungen](#voraussetzungen)
- [Installation über HACS](#installation-über-hacs)
- [Manuelle Installation](#manuelle-installation)
- [Ersteinrichtung](#ersteinrichtung)
- [Nachträgliche Bearbeitung](#nachträgliche-bearbeitung)
- [Mehrere Instanzen](#mehrere-instanzen)
- [Geräte, Entitäten und Schalter](#geräte-entitäten-und-schalter)
- [Service-Aktion](#service-aktion)
- [Webhook und Router-Anbindung](#webhook-und-router-anbindung)
- [FRITZ!Box-Hinweise](#fritzbox-hinweise)
- [Antwortcodes und Bedeutungen](#antwortcodes-und-bedeutungen)
- [Blueprints](#blueprints)
- [Persistenz nach Neustarts](#persistenz-nach-neustarts)
- [Fehlersuche](#fehlersuche)
- [Repository-Struktur](#repository-struktur)
- [Lizenz](#lizenz)
- [English](#english)

## Warum diese Integration?

STRATO stellt DynDNS für Domains und Subdomains bereit. In vielen Setups wird der Update-Aufruf direkt vom Router ausgelöst. Das funktioniert grundsätzlich, ist aber oft unübersichtlich, wenn mehrere Domains, verschiedene Update-Modi oder zusätzliche Diagnoseinformationen benötigt werden.

Diese Integration verlagert die Steuerung nach Home Assistant und ergänzt den reinen STRATO-Update-Aufruf um eine saubere Home-Assistant-Modellierung:

- geführter Einrichtungsassistent
- eigener Neukonfigurations-Wizard
- mehrere Domains oder Subdomains pro Instanz
- mehrere Instanzen im selben Home-Assistant-System
- pro Domain eigene IPv4- und IPv6-Schalter
- Standardvorgabe IPv4 und IPv6 für jede neue Domain
- deutlich kürzerer Einrichtungsablauf ohne Einzelabfrage je Domain
- gruppierte Aktualisierung über Taster, Service oder Webhook
- große Domainmengen werden für STRATO automatisch in 10er-Pakete aufgeteilt
- Rückmeldung der Serverantwort pro Domain
- Wiederherstellung des letzten Zustands nach Neustarts
- deutscher und englischer Sprachumfang für Integration und Blueprint

## Funktionsumfang

Die Integration unterstützt unter anderem:

- Verwaltung mehrerer STRATO-Domains und Subdomains
- getrennte Steuerung pro Domain über IPv4- und IPv6-Schalter
- nur IPv4, nur IPv6, IPv4 und IPv6 oder vollständig deaktiviert
- mehrere Instanzen der Integration parallel
- pro Domain ein eigenes Gerät
- pro Instanz ein eigenes Hauptgerät
- pro Domain zwei eigene Schalter für IPv4 und IPv6
- pro Domain ein Hauptsensor mit der letzten STRATO-Antwort
- pro Domain zusätzliche Diagnose-Sensoren
- pro Instanz globale Diagnose-Sensoren
- pro Instanz globale IPv4- und IPv6-Taster
- pro Domain immer ein IPv4- und ein IPv6-Taster, jeweils passend zur aktiven Adressfamilie verfügbar
- Service-Aktion zur gezielten Aktualisierung ausgewählter Domain-Geräte
- Webhook-Endpunkt je Instanz
- strukturierte Verarbeitung von Sammelantworten des STRATO-Servers
- automatische Batch-Verarbeitung in 10er-Gruppen für große Domainlisten
- Zusammenfassung der schwerwiegendsten Antwort für Router-Aufrufer
- automatische Aufteilung großer Webhook-Updates in mehrere 10er-Requests an STRATO mit gemeinsamer Endauswertung
- Persistenz der letzten bekannten Werte über Neustarts

## Besondere Merkmale

### 1. Mehrere Instanzen

Die Integration kann mehrfach zu Home Assistant hinzugefügt werden. Jede Instanz besitzt:

- einen eigenen Config Entry
- ein eigenes Hauptgerät
- eine eigene Webhook-ID
- eine eigene Webhook-URL
- ihre eigenen Domain-Geräte
- ihre eigenen Zugangsdaten

Damit lassen sich beispielsweise private Domains, Testumgebungen oder verschiedene STRATO-Zugänge sauber trennen.

### 2. Einheitlicher Name des Hauptgeräts

Jede Instanz verwendet für das Hauptgerät bewusst denselben Anzeigenamen:

**STRATO DynDNS Service**

Die interne Eindeutigkeit erfolgt über die Geräte-Identifikatoren. So bleibt die Darstellung sauber und konsistent, auch wenn mehrere Instanzen vorhanden sind.

### 3. Zwei direkte Schalter pro Domain

Jede konfigurierte Domain besitzt zwei eigene Schalter: einen für **IPv4** und einen für **IPv6**. Dadurch entscheidet der Nutzer direkt am Domain-Gerät, welche Adressfamilie aktualisiert werden soll. Sind beide Schalter aktiv, werden beide Adressfamilien aktualisiert. Ist nur einer aktiv, wird ausschließlich diese Adressfamilie aktualisiert. Sind beide deaktiviert, bleibt die Domain zwar konfiguriert, wird aber übersprungen.

### 4. Saubere Trennung von Hauptgerät und Domain-Geräten

Das Hauptgerät zeigt instanzweite Informationen, technische URLs und globale Taster. Die Domain-Geräte zeigen dagegen den fachlichen Zustand der jeweiligen Domain.

## Voraussetzungen

- Home Assistant ab der in `manifest.json` angegebenen Mindestversion
- STRATO-DynDNS-Benutzername
- STRATO-DynDNS-Passwort
- mindestens eine bei STRATO für DynDNS aktivierte Domain oder Subdomain
- für externe Router-Aufrufe eine erreichbare Home-Assistant-URL

## Installation über HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Q14siX&repository=strato_dyndns_service&category=integration)

### Schritte

1. HACS öffnen.
2. **Benutzerdefinierte Repositories** öffnen.
3. `https://github.com/Q14siX/strato_dyndns_service` als Repository vom Typ **Integration** hinzufügen.
4. **STRATO DynDNS Service** installieren.
5. Home Assistant neu starten.
6. Die Integration unter **Einstellungen → Geräte & Dienste** hinzufügen.

## Manuelle Installation

1. Den Ordner `custom_components/strato_dyndns_service` nach `config/custom_components/` kopieren.
2. Home Assistant neu starten.
3. Die Integration unter **Einstellungen → Geräte & Dienste** hinzufügen.

## Ersteinrichtung

Die Ersteinrichtung ist bewusst kompakt gehalten.

### Schritt 1: STRATO-Zugangsdaten

Hier werden Benutzername und Passwort hinterlegt.

### Schritt 2: Domains und Subdomains

Auf einer eigenen Wizard-Seite werden alle Domains oder Subdomains gesammelt hinzugefügt. Dieses Feld unterstützt mehrere Einträge direkt in derselben Ansicht.

Danach ist die Einrichtung bereits abgeschlossen. Für jede neu hinzugefügte Domain sind **IPv4 und IPv6 standardmäßig aktiviert**. Welche Adressfamilie tatsächlich aktualisiert werden soll, wird anschließend direkt über die beiden Domain-Schalter festgelegt.

## Nachträgliche Bearbeitung

Die Integration unterstützt eine spätere Bearbeitung über **Neukonfiguration**. Dabei können Sie:

- Zugangsdaten bearbeiten
- die Domainliste ändern
- neue Domains mit standardmäßig aktiviertem IPv4 und IPv6 hinzufügen
- bestehende Domains beibehalten, ohne deren IPv4-/IPv6-Schalterstellung zu verlieren

Die eigentliche Steuerung erfolgt danach direkt über die Domain-Schalter für IPv4 und IPv6. Ein separater Aktivierungs-Schalter pro Domain ist nicht mehr erforderlich.

## Mehrere Instanzen

Mehrere Instanzen sind ausdrücklich unterstützt. Beispiele:

- eine Instanz für private Domains
- eine Instanz für Vereins- oder Projekt-Domains
- eine Instanz für Testzwecke
- getrennte Instanzen für unterschiedliche STRATO-Zugänge

Wichtig:

- jede Instanz hat einen eigenen Webhook
- jede Instanz besitzt eigene Domain-Geräte
- die Service-Aktion kann Domain-Geräte aus mehreren Instanzen gleichzeitig verarbeiten

## Geräte, Entitäten und Schalter

## Hauptgerät der Instanz

Das Hauptgerät heißt immer **STRATO DynDNS Service**.

### Diagnose-Sensoren am Hauptgerät

- Webhook-URL
- FRITZ!Box-Update-URL
- Letzte Webhook-Antwort
- Aktuelle IPv4
- Aktuelle IPv6
- Letzte Aktualisierung
- Anfrage von

### Taster am Hauptgerät

- IPv4 aktualisieren
- IPv6 aktualisieren

Diese Taster aktualisieren alle Domains der Instanz, bei denen die jeweilige Adressfamilie per Domain-Schalter aktiviert ist.

Sind sehr viele Domains konfiguriert, teilt die Integration die STRATO-Aufrufe automatisch in 10er-Pakete auf, sammelt zunächst alle Einzelantworten und meldet anschließend die schwerwiegendste Gesamtrückmeldung zurück. Dieses Verhalten gilt identisch für manuelle Hauptaktualisierungen, Services und Webhook-Aufrufe.

## Domain-Gerät

Jede konfigurierte Domain oder Subdomain wird als eigenes Gerät angelegt.

### Primärer Sensor pro Domain

Der primäre Sensor trägt den Domainnamen als Entitätsnamen. Sein Zustand entspricht der letzten normalisierten STRATO-Antwort, zum Beispiel:

- `good`
- `nochg`
- `badauth`
- `911`
- `dnserr`

### Diagnose-Sensoren pro Domain

- Status
- Aktualisierungsmodus
- Aktuelle IPv4
- Aktuelle IPv6
- Letzte Aktualisierung
- Letzte Serverantwort

### Schalter pro Domain

Jede Domain besitzt zwei Schalter:

- **IPv4**
- **IPv6**

Damit lässt sich pro Domain direkt festlegen, welche Adressfamilie aktualisiert werden soll. Sind beide Schalter deaktiviert, gilt die Domain praktisch als pausiert.

### Taster pro Domain

Jede Domain besitzt immer beide Taster:

- **IPv4 aktualisieren**
- **IPv6 aktualisieren**

Ein Taster ist nur dann verfügbar, wenn die jeweilige Adressfamilie für die Domain aktiviert ist.

## Service-Aktion

Die Integration stellt die Action `strato_dyndns_service.update_domains` bereit.

### Auswahl

Die Action erwartet **Domain-Geräte**, nicht beliebige Entitäten. Damit ist die Auswahl im Service-Dialog deutlich sauberer.

### Felder

- `device_id`: ein oder mehrere Domain-Geräte
- `ip_version`: `auto`, `ipv4` oder `ipv6`

### Verhalten

- `auto` verwendet die pro Domain aktiven IPv4-/IPv6-Schalter
- `ipv4` erzwingt IPv4-Updates für die ausgewählten Domains, sofern IPv4 dort aktiviert ist
- `ipv6` erzwingt IPv6-Updates für die ausgewählten Domains, sofern IPv6 dort aktiviert ist

### Rückgabe

Die Action liefert eine strukturierte Rückgabe mit:

- Gesamtantwort
- Ergebnissen pro Instanz
- Ergebnissen pro Domain
- zugeordneten IP-Werten
- jeweiliger Serverantwort

## Webhook und Router-Anbindung

Jede Instanz besitzt einen eigenen Webhook. Der Aufruf benötigt keine Domainliste. Stattdessen entscheidet die Integration selbst, welche Domains dieser Instanz aktualisiert werden sollen.

### Interne Gruppierung

Die Integration bildet pro Lauf zunächst bis zu drei logische Gruppen:

1. alle Domains mit **nur IPv4**
2. alle Domains mit **nur IPv6**
3. alle Domains mit **IPv4 und IPv6**

Wenn eine Gruppe leer ist, wird sie übersprungen. Enthält eine Gruppe mehr als **10 Domains**, wird sie automatisch in mehrere STRATO-Anfragen mit jeweils höchstens 10 Domains zerlegt.

Dadurch können bei einem einzelnen Webhook-Lauf mehr als drei STRATO-Anfragen entstehen. Die fachliche Gruppierung bleibt jedoch trotzdem eindeutig nach IPv4-only, IPv6-only und Dual-Stack getrennt.

### Antwortverarbeitung

STRATO kann bei jeder Sammelanfrage mehrere Antwortzeilen zurückgeben. Die Integration ordnet diese Antworten den jeweiligen Domains zu, speichert die passende Einzelantwort pro Domain und wartet anschließend, bis **alle** Teilanfragen eines Laufs abgeschlossen sind. Erst danach wird daraus eine einzige **schwerwiegendste** Gesamtantwort für den Webhook-Aufrufer ermittelt.

Damit erhält ein Router nur eine kompakte Rückmeldung, während Home Assistant die Detailinformationen pro Domain speichert. Das gleiche Auswertungsverhalten gilt auch für die globale Aktualisierung über das Hauptgerät.

## FRITZ!Box-Hinweise

Am Hauptgerät steht eine FRITZ!Box-Update-URL als Diagnose-Sensor zur Verfügung. Diese URL ist als Vorlage gedacht, damit die FRITZ!Box den Webhook der jeweiligen Instanz ansprechen kann.

Die Domainauswahl muss nicht im Router erfolgen. Die Integration übernimmt selbst:

- bei welchen Domains IPv4 aktiviert ist
- bei welchen Domains IPv6 aktiviert ist
- welche Domains zur IPv4-only-Gruppe gehören
- welche Domains zur IPv6-only-Gruppe gehören
- welche Domains mit beiden Adressfamilien aktualisiert werden

Dadurch bleibt die Router-Konfiguration schlank.

## Antwortcodes und Bedeutungen

Die Integration übersetzt die bekannten STRATO-Antwortcodes in Deutsch und Englisch. Dazu zählen unter anderem:

- `good`
- `nochg`
- `badauth`
- `badagent`
- `dnserr`
- `nohost`
- `notfqdn`
- `numhost`
- `911`
- `abuse`
- `!donator`
- `timeout`
- `unknown`

Zusätzlich führt die Integration interne Statuswerte wie:

- `idle`
- `updated`
- `unchanged`
- `disabled`
- `skipped`
- `error`

## Blueprints

Die Integration enthält lokalisierte Blueprints in Deutsch und Englisch.

### Deutscher Blueprint

[![Blueprint importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fstrato_dyndns_service%2Fmain%2Fblueprints%2Fautomation%2Fstrato_dyndns_service%2Fde%2Fupdate_selected_domains.yaml)

### English blueprint

[![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fstrato_dyndns_service%2Fmain%2Fblueprints%2Fautomation%2Fstrato_dyndns_service%2Fen%2Fupdate_selected_domains.yaml)

### Zweck der Blueprints

Die Blueprints erlauben es, ausgewählte Domain-Geräte dieser Integration über reguläre Home-Assistant-Trigger zu aktualisieren, zum Beispiel:

- nach einem festen Zeitplan
- nach dem Start von Home Assistant
- nach einem Netzwerk- oder Router-Ereignis
- nach einem manuellen Helfer oder Schalter

## Persistenz nach Neustarts

Die Integration stellt den letzten bekannten Zustand der relevanten Sensoren nach einem Neustart wieder her. Dadurch bleiben insbesondere folgende Informationen sichtbar, bis ein neuer echter Lauf erfolgt:

- letzte STRATO-Antwort pro Domain
- letzte bekannte IPs
- letzter Zeitstempel
- letzte Webhook-Antwort
- Anfragequelle

## Fehlersuche

### Webhook liefert `nochg`

`nochg` bedeutet, dass STRATO keinen Änderungsbedarf erkannt hat. Die Domain war also bereits mit der gewünschten IP hinterlegt.

### Domain wird nicht aktualisiert

Mögliche Ursachen:

- sowohl IPv4 als auch IPv6 sind für die Domain deaktiviert
- die angeforderte IP-Familie ist für diese Domain nicht aktiviert
- falsche STRATO-Zugangsdaten
- Domain ist bei STRATO nicht korrekt für DynDNS aktiviert
- Home Assistant ist von außen nicht erreichbar

### Entitäten zeigen nach Änderungen alte Texte

Nach Updates der Integration oder der Übersetzungen empfiehlt sich:

- Home Assistant komplett neu starten
- Browser hart neu laden

## Repository-Struktur

```text
.
├── LICENSE
├── README.md
├── hacs.json
├── blueprints/
│   └── automation/
│       └── strato_dyndns_service/
│           ├── de/
│           │   └── update_selected_domains.yaml
│           └── en/
│               └── update_selected_domains.yaml
└── custom_components/
    └── strato_dyndns_service/
        ├── __init__.py
        ├── brand/
        │   ├── icon.png
        │   └── logo.png
        ├── button.py
        ├── config_flow.py
        ├── const.py
        ├── coordinator.py
        ├── entity.py
        ├── helpers.py
        ├── http.py
        ├── manifest.json
        ├── models.py
        ├── sensor.py
        ├── services.yaml
        ├── switch.py
        └── translations/
            ├── de.json
            └── en.json
```

## Validierung und Veröffentlichung

Das Repository enthält zwei GitHub-Workflows für die automatisierte Prüfung:

- **HACS-Validierung** über `.github/workflows/validate.yml`
- **Hassfest-Validierung** über `.github/workflows/hassfest.yaml`

Diese Workflows laufen bei Push, Pull Request, zeitgesteuert und manuell über `workflow_dispatch`.

Wichtig für eine Veröffentlichung über HACS:

- Das Repository muss **öffentlich** sein.
- Das Repository sollte eine **Beschreibung** besitzen.
- **Issues** müssen aktiviert sein.
- Es sollten **Topics** gesetzt sein.
- Für eine Aufnahme in die standardmäßige HACS-Liste ist mindestens ein **GitHub Release** sinnvoll bzw. im Prüfprozess relevant.

Die automatischen Workflows helfen dabei, typische Struktur- und Manifestfehler früh zu erkennen.

## Lizenz

Dieses Repository enthält eine Lizenzdatei im Projektstamm. Bitte beachte die dort hinterlegten Lizenzbedingungen für Nutzung, Weitergabe und Änderungen.

---

# English

[Zur deutschen Version](#strato-dyndns-service)

STRATO DynDNS Service is a custom Home Assistant integration for the STRATO DynDNS service. It is designed to manage multiple STRATO domains and subdomains directly inside Home Assistant, trigger updates manually or in grouped form, accept router-driven webhook calls, and expose the result through devices, sensors, switches, buttons, services, and blueprints.

## Table of contents

- [Why this integration?](#why-this-integration)
- [Feature set](#feature-set)
- [Special characteristics](#special-characteristics)
- [Requirements](#requirements)
- [Installation via HACS](#installation-via-hacs)
- [Manual installation](#manual-installation)
- [Initial setup](#initial-setup)
- [Reconfiguration](#reconfiguration)
- [Multiple instances](#multiple-instances)
- [Devices, entities, and switches](#devices-entities-and-switches)
- [Service action](#service-action)
- [Webhook and router integration](#webhook-and-router-integration)
- [FRITZ!Box notes](#fritzbox-notes)
- [Response codes and meanings](#response-codes-and-meanings)
- [Blueprints](#blueprints-1)
- [State restoration after restart](#state-restoration-after-restart)
- [Troubleshooting](#troubleshooting)
- [Repository structure](#repository-structure)
- [License](#license-1)

## Why this integration?

STRATO provides DynDNS for domains and subdomains. In many environments, the update request is triggered directly by the router. That works, but it quickly becomes hard to manage when multiple domains, different IP modes, or proper diagnostics are required.

This integration moves the orchestration into Home Assistant and adds a clean Home Assistant model on top of the raw STRATO DynDNS request:

- guided setup wizard
- dedicated reconfigure wizard
- multiple domains or subdomains per instance
- multiple instances within the same Home Assistant system
- dedicated IPv4 and IPv6 switches per domain
- IPv4 and IPv6 enabled by default for every new domain
- much shorter setup flow without a separate domain-by-domain wizard
- grouped updates via buttons, service, or webhook
- per-domain server response tracking
- restored state after Home Assistant restarts
- full German and English localization for the integration and blueprint

## Feature set

The integration includes:

- management of multiple STRATO domains and subdomains
- separate per-domain control through IPv4 and IPv6 switches
- IPv4 only, IPv6 only, IPv4 and IPv6, or fully disabled
- multiple parallel integration instances
- one dedicated device per domain
- one main device per integration instance
- two dedicated switches per domain for IPv4 and IPv6
- one primary sensor per domain with the last STRATO response
- additional diagnostic sensors per domain
- global diagnostic sensors per instance
- global IPv4 and IPv6 buttons per instance
- both domain buttons are always present and become available according to the active IP family
- a service action to update selected domain devices
- one webhook endpoint per instance
- structured parsing of grouped STRATO server responses
- aggregation of the worst response for router callers
- restoration of the last known values after restart

## Special characteristics

### 1. Multiple instances

The integration can be added more than once. Each instance has:

- its own config entry
- its own main device
- its own webhook ID
- its own webhook URL
- its own domain devices
- its own credentials

This makes it possible to separate private domains, lab setups, project environments, or entirely different STRATO accounts.

### 2. Uniform main device name

Every instance intentionally uses the same display name for the main device:

**STRATO DynDNS Service**

The internal uniqueness is handled through device identifiers, so the visible name can stay clean and consistent.

### 3. Two direct switches per domain

Each configured domain has two dedicated switches: one for **IPv4** and one for **IPv6**. This lets the user decide directly on the domain device which address family should be updated. If both switches are on, both address families are updated. If only one switch is on, only that address family is updated. If both are off, the domain stays configured but is skipped.

### 4. Clean separation between the main device and domain devices

The main device exposes instance-wide information, technical URLs, and global buttons. The domain devices expose the functional state of each configured domain.

## Requirements

- Home Assistant version at or above the minimum version declared in `manifest.json`
- STRATO DynDNS username
- STRATO DynDNS password
- at least one STRATO DynDNS-enabled domain or subdomain
- a reachable Home Assistant URL for external router/webhook calls

## Installation via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Q14siX&repository=strato_dyndns_service&category=integration)

### Steps

1. Open HACS.
2. Open **Custom repositories**.
3. Add `https://github.com/Q14siX/strato_dyndns_service` as an **Integration** repository.
4. Install **STRATO DynDNS Service**.
5. Restart Home Assistant.
6. Add the integration in **Settings → Devices & Services**.

## Manual installation

1. Copy `custom_components/strato_dyndns_service` into `config/custom_components/`.
2. Restart Home Assistant.
3. Add the integration in **Settings → Devices & Services**.

## Initial setup

The setup is intentionally compact.

### Step 1: STRATO credentials

Enter the DynDNS username and password.

### Step 2: Domains and subdomains

A dedicated wizard page collects all domains or subdomains together. The field supports multiple entries within the same view.

After that, the setup is already finished. For every newly added domain, **IPv4 and IPv6 are enabled by default**. The effective behavior is then adjusted directly through the two per-domain switches.

## Reconfiguration

The integration supports later editing via **Reconfigure**. You can:

- change credentials
- change the domain list
- add new domains with IPv4 and IPv6 enabled by default
- keep existing domains without losing their IPv4/IPv6 switch state

The effective control then happens directly through the IPv4 and IPv6 switches on each domain. A separate enable/disable switch is no longer required.

## Multiple instances

Multiple instances are explicitly supported. Examples:

- one instance for private domains
- one instance for club or project domains
- one instance for testing
- separate instances for different STRATO accounts

Important details:

- each instance has its own webhook
- each instance owns its own domain devices
- the service action can process domain devices from multiple instances at once

## Devices, entities, and switches

## Main device of an instance

The main device is always called **STRATO DynDNS Service**.

### Diagnostic sensors on the main device

- Webhook URL
- FRITZ!Box update URL
- Last webhook response
- Current IPv4
- Current IPv6
- Last update
- Request from

### Buttons on the main device

- Update IPv4
- Update IPv6

These buttons update all domains of that instance for which the selected IP family is enabled via the per-domain switches.

## Domain device

Each configured domain or subdomain becomes its own device.

### Primary sensor per domain

The primary sensor uses the domain name as the entity name. Its state is the last normalized STRATO response, for example:

- `good`
- `nochg`
- `badauth`
- `911`
- `dnserr`

### Diagnostic sensors per domain

- Status
- Update mode
- Current IPv4
- Current IPv6
- Last update
- Last server response

### Switches per domain

Each domain has two switches:

- **IPv4**
- **IPv6**

This makes it possible to decide directly per domain which address family should be updated. If both switches are off, the domain is effectively paused.

### Buttons per domain

Each domain always has both buttons:

- **Update IPv4**
- **Update IPv6**

A button is only available when the corresponding address family is enabled for that domain.

## Service action

The integration provides the `strato_dyndns_service.update_domains` action.

### Selection

The action expects **domain devices**, not arbitrary entities. That keeps the service dialog clean and easier to use.

### Fields

- `device_id`: one or more domain devices
- `ip_version`: `auto`, `ipv4`, or `ipv6`

### Behavior

- `auto` uses the active IPv4/IPv6 switches of each domain
- `ipv4` forces IPv4 updates for the selected domains if IPv4 is enabled there
- `ipv6` forces IPv6 updates for the selected domains if IPv6 is enabled there

### Return value

The action returns a structured response containing:

- an overall response
- per-instance results
- per-domain results
- associated IP values
- the server response for each processed domain

## Webhook and router integration

Each instance has its own webhook. The webhook call does not need a domain list. Instead, the integration decides by itself which domains of that instance must be updated.

### Internal grouping

For each run, the integration first builds up to three logical groups:

1. all domains with **IPv4 only**
2. all domains with **IPv6 only**
3. all domains with **IPv4 and IPv6**

If a group is empty, it is skipped. If a group contains more than **10 domains**, it is automatically split into multiple STRATO requests with at most 10 domains each.

Because of that, a single webhook run can produce more than three STRATO requests. The logical grouping still remains clearly separated into IPv4-only, IPv6-only, and dual-stack updates.

### Response handling

STRATO may return multiple response lines for each grouped request. The integration assigns those responses back to the correct domains, stores the matching per-domain result, and then waits until **all** partial requests of the run have finished. Only after that does it compute one single **worst** overall response for the webhook caller.

That means a router receives one compact reply, while Home Assistant still stores the details per domain. The same aggregation behavior also applies to the global update triggered on the main device.

## FRITZ!Box notes

A FRITZ!Box update URL template is exposed as a diagnostic sensor on the main device. It is intended as a convenience template so the FRITZ!Box can call the webhook of the corresponding instance.

The router does not need to decide which domains should be updated. The integration handles:

- for which domains IPv4 is enabled
- for which domains IPv6 is enabled
- which domains belong to the IPv4-only group
- which domains belong to the IPv6-only group
- which domains should be updated with both address families

This keeps the router-side setup minimal.

## Response codes and meanings

The integration translates the known STRATO response codes in German and English, including:

- `good`
- `nochg`
- `badauth`
- `badagent`
- `dnserr`
- `nohost`
- `notfqdn`
- `numhost`
- `911`
- `abuse`
- `!donator`
- `timeout`
- `unknown`

The integration also uses internal runtime states such as:

- `idle`
- `updated`
- `unchanged`
- `disabled`
- `skipped`
- `error`

## Blueprints

The repository contains localized blueprints in German and English.

### German blueprint

[![Blueprint importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fstrato_dyndns_service%2Fmain%2Fblueprints%2Fautomation%2Fstrato_dyndns_service%2Fde%2Fupdate_selected_domains.yaml)

### English blueprint

[![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fstrato_dyndns_service%2Fmain%2Fblueprints%2Fautomation%2Fstrato_dyndns_service%2Fen%2Fupdate_selected_domains.yaml)

### Blueprint purpose

The blueprints allow selected domain devices of this integration to be updated through regular Home Assistant triggers, for example:

- on a fixed schedule
- after Home Assistant startup
- after a network or router event
- after a helper or manual switch changes state

## State restoration after restart

The relevant sensors restore their last known values after Home Assistant restarts. This keeps useful information visible until a fresh update run occurs, especially:

- the last STRATO response per domain
- the last known IP addresses
- the last timestamp
- the last webhook response
- the request source

## Troubleshooting

### The webhook returns `nochg`

`nochg` means STRATO did not detect any required change. The domain was already set to the requested IP address.

### A domain is not updated

Possible reasons:

- both IPv4 and IPv6 are disabled for the domain
- the requested IP family is not enabled for that domain
- wrong STRATO credentials
- the domain is not correctly enabled for DynDNS at STRATO
- Home Assistant is not reachable from the outside

### Old texts remain visible after updating the integration

After changing the integration or the translations, it is recommended to:

- fully restart Home Assistant
- hard-reload the browser

## Repository structure

```text
.
├── LICENSE
├── README.md
├── hacs.json
├── blueprints/
│   └── automation/
│       └── strato_dyndns_service/
│           ├── de/
│           │   └── update_selected_domains.yaml
│           └── en/
│               └── update_selected_domains.yaml
└── custom_components/
    └── strato_dyndns_service/
        ├── __init__.py
        ├── brand/
        │   ├── icon.png
        │   └── logo.png
        ├── button.py
        ├── config_flow.py
        ├── const.py
        ├── coordinator.py
        ├── entity.py
        ├── helpers.py
        ├── http.py
        ├── manifest.json
        ├── models.py
        ├── sensor.py
        ├── services.yaml
        ├── switch.py
        └── translations/
            ├── de.json
            └── en.json
```

## Validation and publishing

The repository now includes two GitHub workflows for automated checks:

- **HACS validation** via `.github/workflows/validate.yml`
- **Hassfest validation** via `.github/workflows/hassfest.yaml`

These workflows run on push, pull request, on a schedule, and manually via `workflow_dispatch`.

Important for publishing through HACS:

- The repository must be **public**.
- The repository should have a **description**.
- **Issues** must be enabled.
- The repository should have **topics**.
- For inclusion in the default HACS list, at least one **GitHub Release** is advisable and relevant during review.

The automated workflows help catch common structure and manifest issues early.

## License

This repository contains a license file in the project root. Please review that license for the terms that apply to usage, redistribution, and modifications.
