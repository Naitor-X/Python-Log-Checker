# 🤖 Python Log Checker - Docker Monitoring App

Eine schlanke Docker-Anwendung für Server-Backup-Monitoring mit **erweiterter checkbackup-Integration**. Unterstützt zeitbasierte Log-Verzeichnisse (YYYY-MM-DD), spezifische Dateien-Checks und Schlüsselwort-basierte Fehlersuche - **100% kompatibel mit bestehenden Unraid checkbackup-Setups**.

## 📋 Überblick

Diese Docker-Anwendung überwacht Server-Backup-Logs automatisch durch geplante Python-Scripts und versendet E-Mail-Benachrichtigungen bei Problemen. Sie ist speziell für die Überwachung von Backup-Logs auf mehreren Servern entwickelt worden.

### Kernfunktionalitäten

- ⏰ **Cron-Job Management**: Automatische Ausführung von geplanten Tasks
- 🐍 **Python Script Execution**: Flexible Ausführung von Python-Monitoring-Scripts
- 📧 **E-Mail Versand**: SMTP-Integration für automatische Benachrichtigungen
- 📁 **Externe Ordner-Zugriff**: Zugriff auf gemappte Backup-Verzeichnisse
- 🏥 **Health Checks**: Umfassende Container-Gesundheitsprüfung
- 📊 **Detaillierte Berichte**: Strukturierte Analyse-Berichte mit Status-Übersicht

### 🚀 **NEU: Erweiterte checkbackup-Integration**

- 📅 **Zeitbasierte Log-Verzeichnisse**: Automatische Prüfung von YYYY-MM-DD strukturierten Logs
- 📋 **Konfigurierbare Dateilisten**: Flexible Definition erforderlicher Log-Dateien
- 🔍 **Schlüsselwort-Scanning**: Erweiterte Fehlersuche mit konfigurierbaren Keywords
- 📎 **E-Mail-Anhänge**: Automatischer Versand von Fehler-Reports als Datei-Anhang
- 🔄 **Migration von Unraid**: Einfache Migration bestehender checkbackup-Konfigurationen
- ⚙️ **100% Kompatibilität**: Drop-in Replacement für bestehende checkbackup-Scripts

## 🚀 Schnellstart

### Für bestehende checkbackup-Benutzer (Unraid)

```bash
# 1. Migration der bestehenden Konfiguration
python migrate_from_checkbackup.py /path/to/your/checkbackup/

# 2. Konfiguration ins Docker-Projekt kopieren
cp migrated_config/* ./app/config/

# 3. Volume-Mappings in docker-compose.yml anpassen
# (siehe migrated_config/docker-compose-volumes.txt)

# 4. Container starten
docker-compose up -d
```

### Für neue Installationen

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

#### Für checkbackup-Migration (Unraid):
```yaml
volumes:
  # Hauptverzeichnis mit Datums-Unterordnern (YYYY-MM-DD)
  - /mnt/user/logs/rsync:/app/data/logs:ro
  
  # Ausgabe-Verzeichnis für Reports
  - /mnt/user/logs/logcheck:/app/logs/logcheck:rw
  
  # Konfigurationsdateien
  - ./app/config:/app/config:ro
```

#### Für Standard-Monitoring:
```yaml
volumes:
  # Standard Backup-Log-Verzeichnisse
  - /var/log/backup:/app/data/backup:ro
  - /var/log/system:/app/data/system:ro
```

## 📁 Verzeichnisstruktur

### Standard-Struktur:
```
/app
├── config/
│   ├── config.yaml          # Hauptkonfiguration
│   ├── logfilelist.txt      # NEU: Liste erforderlicher Log-Dateien
│   └── keywords.txt         # NEU: Schlüsselwörter für Fehlersuche
├── scripts/
│   ├── advanced_backup_checker.py  # NEU: Erweiterte checkbackup-Integration
│   ├── backup_monitor.py           # Standard Backup-Monitoring
│   ├── email_utils.py              # E-Mail-Utility
│   └── [weitere_scripts]
├── logs/
│   ├── logcheck/            # NEU: Ausgabe für Backup-Check-Reports
│   └── *.log               # Anwendungs-Logs
└── data/
    ├── logs/               # NEU: Zeitbasierte Log-Verzeichnisse (YYYY-MM-DD)
    ├── backup/             # Standard Backup-Logs
    └── system/             # Standard System-Logs
```

### checkbackup-kompatible Log-Struktur:
```
/app/data/logs/
├── 2024-12-29/            # Heutiger Tag
│   ├── Administration.log
│   ├── Nevaris.log
│   └── Share_MSSQL.log
├── 2024-12-28/            # Gestern
│   ├── Administration.log
│   └── Share_MSSQL.log    # Nevaris.log fehlt = Fehler!
└── 2024-12-27/            # Vorgestern
    └── ...                # Weitere Tage
```

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

## 🔧 Konfiguration & Anpassung

### checkbackup-Konfiguration

#### 1. Erforderliche Log-Dateien definieren (`logfilelist.txt`):
```
Administration.log
Nevaris.log
Share_MSSQL.log
Database_Backup.log
```

#### 2. Schlüsselwörter für Fehlersuche (`keywords.txt`):
```
denied
Denied
Warn
warn
Warning
fail
Fail
error
Error
ERROR
critical
Critical
CRITICAL
```

#### 3. Erweiterte Konfiguration in `config.yaml`:
```yaml
advanced_backup_check:
  server_name: "Mein-Server"              # Name für E-Mail-Betreff
  log_directory: "/app/data/logs"          # Basis-Verzeichnis
  output_directory: "/app/logs/logcheck"   # Report-Ausgabe
  days_to_check: 1                        # Anzahl Tage prüfen
  start_day_offset: 0                     # 0 = heute, 1 = gestern
  email_subject_prefix: "Backup-Check"    # E-Mail-Betreff-Präfix
```

### Standard Monitoring-Scripts hinzufügen

1. Script in `app/scripts/` erstellen
2. E-Mail-Utility importieren:
```python
from email_utils import EmailSender

sender = EmailSender()
sender.send_error_notification("script_name", "Fehlermeldung")
```

3. Cron-Job in `config.yaml` hinzufügen

### checkbackup-kompatibles Script-Beispiel

```python
#!/usr/bin/env python3
from advanced_backup_checker import AdvancedBackupChecker

def main():
    checker = AdvancedBackupChecker()
    success = checker.check_log_files()
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
```

### Standard Monitoring-Script-Struktur

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

## 🔄 Migration von checkbackup (Unraid)

### Automatische Migration

```bash
# 1. Migration ausführen
python migrate_from_checkbackup.py ./checkbackup/

# 2. Generierte Dateien prüfen
ls migrated_config/
# config.yaml
# logfilelist.txt  
# keywords.txt
# docker-compose-volumes.txt

# 3. Dateien ins Projekt kopieren
cp migrated_config/config.yaml ./app/config/
cp migrated_config/logfilelist.txt ./app/config/
cp migrated_config/keywords.txt ./app/config/

# 4. Volume-Mappings anpassen
cat migrated_config/docker-compose-volumes.txt
# Anweisungen für docker-compose.yml
```

### Manuelle Migration

1. **Pfade anpassen**: `/mnt/user/logs/rsync/` → `/app/data/logs`
2. **Konfigurationsdateien kopieren**: `Logfilelist.txt` → `logfilelist.txt`
3. **E-Mail-Einstellungen übertragen**: `config.txt` → `config.yaml`
4. **Cron-Job einrichten**: Tägliche Ausführung von `advanced_backup_checker.py`

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

### checkbackup-spezifische Debugging
```bash
# Erweiterte Backup-Check Logs
docker exec log-checker tail -f /app/logs/advanced_backup_checker.log

# Generierte Reports prüfen
docker exec log-checker ls -la /app/logs/logcheck/
docker exec log-checker cat /app/logs/logcheck/2024-12-29-ErrWarn.log

# Test-Ausführung
docker exec log-checker python /app/scripts/advanced_backup_checker.py
```

### Standard Cron-Jobs überprüfen
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

**checkbackup-Migration Probleme:**
```bash
# 1. Pfad-Mappings prüfen
docker exec log-checker ls -la /app/data/logs/
# Sollte Datums-Verzeichnisse zeigen: 2024-12-29, 2024-12-28, etc.

# 2. Log-Dateien prüfen
docker exec log-checker ls -la /app/data/logs/$(date +%Y-%m-%d)/
# Sollte erforderliche .log-Dateien zeigen

# 3. Keywords und Logfilelist prüfen
docker exec log-checker cat /app/config/logfilelist.txt
docker exec log-checker cat /app/config/keywords.txt
```

**Container startet nicht:**
```bash
# Logs prüfen
docker-compose logs log-checker

# Konfiguration validieren
docker run --rm -v $(pwd)/app/config:/app/config python:3.11-slim python -c "import yaml; print(yaml.safe_load(open('/app/config/config.yaml')))"
```

**E-Mails werden nicht gesendet:**
```bash
# E-Mail-Test für checkbackup-Integration
docker exec log-checker python -c "
from advanced_backup_checker import AdvancedBackupChecker
checker = AdvancedBackupChecker()
checker.email_sender.test_connection()
"

# Standard E-Mail-Test
docker exec log-checker python /app/scripts/email_utils.py test

# SMTP-Konfiguration prüfen
docker exec log-checker python -c "
import yaml
with open('/app/config/config.yaml') as f:
    print(yaml.safe_load(f)['smtp'])
"
```

**checkbackup-Script findet keine Dateien:**
```bash
# Verzeichnis-Struktur prüfen
docker exec log-checker find /app/data/logs -name "*.log" | head -10

# Berechtigungen prüfen
docker exec log-checker ls -la /app/data/logs/

# Konfiguration der erweiterten Backup-Checks
docker exec log-checker python -c "
import yaml
with open('/app/config/config.yaml') as f:
    print(yaml.safe_load(f)['advanced_backup_check'])
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

### checkbackup-Integration Berichte:
- 📅 **Zeitbasierte Analysen**: Automatische Prüfung von YYYY-MM-DD Verzeichnissen
- 📋 **Datei-Vollständigkeit**: Prüfung auf fehlende erforderliche Log-Dateien
- 🔍 **Schlüsselwort-Scanning**: Detaillierte Fehlersuche mit Zeilen-Referenzen
- 📎 **E-Mail-Anhänge**: Fehler-Reports als Datei-Anhang (genau wie checkbackup)
- 🏷️ **Server-Identifikation**: Konfigurierbare Server-Namen in E-Mail-Betreffs

### Standard-Monitoring Berichte:
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