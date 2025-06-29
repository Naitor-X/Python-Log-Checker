# Docker Monitoring App - Entwicklungsauftrag

Erstelle eine schlanke Docker-Anwendung für Server-Backup-Monitoring mit folgenden Anforderungen:

## Kernfunktionalitäten
- **Cron-Job Management**: Ausführung von geplanten Tasks über Cron
- **Python Script Execution**: Ausführung von Python-Dateien als Cron-Jobs
- **E-Mail Versand**: Integration für Mail-Versand direkt aus Python-Scripts
- **Externe Ordner-Zugriff**: Zugriff auf 1-2 gemappte externe Verzeichnisse

## Technische Spezifikationen
- **Base Image**: Schlankes Python-Image (z.B. python:3.11-slim)
- **Cron**: Integrierter Cron-Daemon für Job-Scheduling
- **Mail-Support**: SMTP-Konfiguration für E-Mail-Versand
- **Volume Mapping**: Unterstützung für externe Ordner-Mounts

## Konfiguration
Erstelle eine einfache, zentrale Konfigurationsdatei (YAML oder JSON) für:
- Cron-Job Definitionen (Zeitpläne und zu ausführende Python-Scripts)
- SMTP-Einstellungen (Server, Port, Authentifizierung)
- Pfade zu den gemappten externen Ordnern
- Logging-Konfiguration

## Verzeichnisstruktur
```
/app
├── config/          # Konfigurationsdateien
├── scripts/         # Python-Scripts (hier kommt mein Backup-Monitor rein)
├── logs/           # Anwendungs-Logs
└── data/           # Gemappte externe Ordner
```

## Docker Setup
- Multi-stage Build für optimale Image-Größe
- Non-root User für Sicherheit
- Proper Signal Handling für Container-Lifecycle
- Health Check Implementation

## Anwendungsfall
Die App überwacht Server-Backup-Logs auf mehreren Servern. Ein vorhandenes Python-Script prüft Log-Dateien auf Fehler und Vollständigkeit und versendet entsprechende Benachrichtigungen per E-Mail.

## Deliverables
1. Dockerfile mit Multi-stage Build
2. Docker-compose.yml für einfaches Deployment
3. Konfigurationsdatei-Template
4. Startup-Script für Cron-Daemon und Python-Environment
5. README mit Setup- und Verwendungsanleitung
6. Beispiel-Konfiguration für typische Monitoring-Szenarien

## Besondere Anforderungen
- Minimaler Ressourcenverbrauch
- Einfache Wartung und Updates
- Robust gegen Container-Neustarts
- Ausführliche Logging-Funktionen
- Fehlerbehandlung bei Mail-Versand und Script-Ausführung

Entwickle eine produktionsreife, wartbare Lösung die sich einfach auf verschiedenen Servern deployen lässt.