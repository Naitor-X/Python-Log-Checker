# 🤖 Python Log Checker - Docker Monitoring App

Eine schlanke Docker-Anwendung für Server-Backup-Monitoring mit Cron-Job-Management, Python-Script-Ausführung und E-Mail-Benachrichtigungen.

## 📋 Überblick

Diese Docker-Anwendung überwacht Server-Backup-Logs automatisch durch geplante Python-Scripts und versendet E-Mail-Benachrichtigungen bei Problemen. Sie ist speziell für die Überwachung von Backup-Logs auf mehreren Servern entwickelt worden.

### Kernfunktionalitäten

- ⏰ **Cron-Job Management**: Automatische Ausführung von geplanten Tasks
- 🐍 **Python Script Execution**: Flexible Ausführung von Python-Monitoring-Scripts
- 📧 **E-Mail Versand**: SMTP-Integration für automatische Benachrichtigungen
- 📁 **Externe Ordner-Zugriff**: Zugriff auf gemappte Backup-Verzeichnisse
- 🏥 **Health Checks**: Umfassende Container-Gesundheitsprüfung
- 📊 **Detaillierte Berichte**: Strukturierte Analyse-Berichte mit Status-Übersicht

## 🚀 Schnellstart

### 1. Repository klonen
```bash
git clone <repository-url>
cd Python-Log-Checker
```

### 2. Konfiguration anpassen
```bash
# Kopiere und bearbeite die Konfiguration
cp app/config/config.yaml app/config/config.yaml.local
nano app/config/config.yaml.local
```

### 3. Docker-Container starten
```bash
# Mit Docker Compose
docker-compose up -d

# Oder mit Docker direkt
docker build -t python-log-checker .
docker run -d --name log-checker python-log-checker
```

### 4. Status prüfen
```bash
# Container-Status
docker-compose ps

# Logs anzeigen
docker-compose logs -f

# Health Check
docker exec log-checker python /app/healthcheck.py
```

## ⚙️ Konfiguration

### SMTP-Einstellungen

Bearbeite `app/config/config.yaml`:

```yaml
smtp:
  server: "smtp.gmail.com"
  port: 587
  use_tls: true
  username: "your-email@gmail.com"
  password: "your-app-password"
  from_email: "your-email@gmail.com"
  default_recipients:
    - "admin@example.com"
```

### Cron-Jobs konfigurieren

```yaml
cron_jobs:
  - name: "backup_log_check"
    schedule: "0 6 * * *"  # Täglich um 6:00 Uhr
    script: "backup_monitor.py"
    description: "Überprüft Backup-Logs auf Fehler"
    enabled: true
```

### Volume-Mappings anpassen

In `docker-compose.yml`:

```yaml
volumes:
  # Deine Backup-Log-Verzeichnisse
  - /var/log/backup:/app/data/backup:ro
  - /var/log/system:/app/data/system:ro
```

## 📁 Verzeichnisstruktur

```
/app
├── config/
│   └── config.yaml          # Hauptkonfiguration
├── scripts/
│   ├── backup_monitor.py    # Backup-Monitoring Script
│   ├── email_utils.py       # E-Mail-Utility
│   └── [weitere_scripts]    # Deine eigenen Scripts
├── logs/
│   └── *.log               # Anwendungs-Logs
└── data/
    ├── backup/             # Gemappte Backup-Logs
    └── system/             # Gemappte System-Logs
```

## 🔧 Entwicklung & Anpassung

### Eigene Monitoring-Scripts hinzufügen

1. Script in `app/scripts/` erstellen
2. E-Mail-Utility importieren:
```python
from email_utils import EmailSender

sender = EmailSender()
sender.send_error_notification("script_name", "Fehlermeldung")
```

3. Cron-Job in `config.yaml` hinzufügen

### Beispiel-Script-Struktur

```python
#!/usr/bin/env python3
import yaml
from email_utils import EmailSender

def main():
    # Konfiguration laden
    with open('/app/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Monitoring-Logik hier
    try:
        # Deine Monitoring-Logik
        pass
    except Exception as e:
        # Fehler-Benachrichtigung
        sender = EmailSender()
        sender.send_error_notification("mein_script", str(e))

if __name__ == "__main__":
    main()
```

## 🏥 Monitoring & Debugging

### Container-Gesundheit prüfen
```bash
# Health Check ausführen
docker exec log-checker python /app/healthcheck.py

# Detaillierte Status-Informationen
docker exec log-checker python /app/healthcheck.py --verbose
```

### Logs analysieren
```bash
# Container-Logs
docker-compose logs log-checker

# Anwendungs-Logs
docker exec log-checker tail -f /app/logs/log_checker.log

# Backup-Monitor Logs
docker exec log-checker tail -f /app/logs/backup_monitor.log
```

### Cron-Jobs überprüfen
```bash
# Aktive Cron-Jobs anzeigen
docker exec log-checker crontab -l

# Cron-Log überprüfen
docker exec log-checker tail -f /var/log/cron.log
```

## 🔐 Sicherheit

- Container läuft als **non-root User** (appuser)
- **Read-only** Volume-Mappings für externe Log-Verzeichnisse
- **Sichere SMTP-Authentifizierung** (TLS/SSL)
- **Eingabevalidierung** für Konfigurationsparameter
- **Ressourcen-Limits** in docker-compose.yml definiert

## 🚨 Fehlerbehebung

### Häufige Probleme

**Container startet nicht:**
```bash
# Logs prüfen
docker-compose logs log-checker

# Konfiguration validieren
docker run --rm -v $(pwd)/app/config:/app/config python:3.11-slim python -c "import yaml; print(yaml.safe_load(open('/app/config/config.yaml')))"
```

**E-Mails werden nicht gesendet:**
```bash
# E-Mail-Test
docker exec log-checker python /app/scripts/email_utils.py test

# SMTP-Konfiguration prüfen
docker exec log-checker python -c "
import yaml
with open('/app/config/config.yaml') as f:
    print(yaml.safe_load(f)['smtp'])
"
```

**Cron-Jobs laufen nicht:**
```bash
# Cron-Service Status
docker exec log-checker pgrep cron

# Crontab prüfen
docker exec log-checker crontab -l
```

## 🔄 Updates & Wartung

### Container aktualisieren
```bash
# Build und Neustart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Log-Rotation
Logs werden automatisch rotiert (konfigurierbar in `config.yaml`):
- Maximale Größe: 10 MB
- Backup-Count: 5 Dateien
- Komprimierung aktiviert

### Backup der Konfiguration
```bash
# Konfiguration sichern
cp app/config/config.yaml config-backup-$(date +%Y%m%d).yaml
```

## 📊 Metriken & Überwachung

Das System generiert detaillierte Berichte mit:
- ✅ Erfolgreiche/fehlgeschlagene Backups
- ⚠️ Warnungen und Fehler-Details
- 📈 Übertragene Datenmengen
- ⏱️ Backup-Ausführungszeiten
- 🗓️ Backup-Aktualität (Alter der Log-Dateien)

## 🤝 Support

Bei Problemen oder Fragen:
1. Prüfe die [Fehlerbehebung](#-fehlerbehebung)
2. Überprüfe die Container-Logs
3. Führe einen Health-Check durch
4. Kontaktiere den Administrator

## 📄 Lizenz

Dieses Projekt ist für den internen Gebrauch entwickelt worden.

---

**🤖 Entwickelt mit Claude Code - Bereit für den produktiven Einsatz!**