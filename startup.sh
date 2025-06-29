#!/bin/bash

# Startup-Script für Python Log Checker Container
# Initialisiert Cron-Daemon und Python-Environment

set -e

echo "🤖 Starting Python Log Checker..."

# Funktionen definieren
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Umgebungsvariablen setzen
export PYTHONPATH="/app:$PYTHONPATH"
export PATH="/home/appuser/.local/bin:$PATH"

# Konfigurationsdatei prüfen
CONFIG_FILE="/app/config/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    error_exit "Konfigurationsdatei nicht gefunden: $CONFIG_FILE"
fi

log "Konfigurationsdatei gefunden: $CONFIG_FILE"

# Python-Module prüfen
log "Prüfe Python-Abhängigkeiten..."
python -c "import yaml, smtplib, schedule" || error_exit "Python-Abhängigkeiten fehlen"

# Verzeichnisse erstellen und Berechtigungen setzen
log "Erstelle erforderliche Verzeichnisse..."
mkdir -p /app/logs /app/data
chmod 755 /app/logs /app/data

# Cron-Service vorbereiten
log "Konfiguriere Cron-Jobs..."

# Cron-Jobs aus Konfiguration generieren
python3 << 'EOF'
import yaml
import os
import sys

try:
    with open('/app/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    cron_jobs = config.get('cron_jobs', [])
    
    with open('/tmp/crontab', 'w') as f:
        f.write("# Generierte Cron-Jobs für Log Checker\n")
        f.write("SHELL=/bin/bash\n")
        f.write("PATH=/home/appuser/.local/bin:/usr/local/bin:/usr/bin:/bin\n")
        f.write("PYTHONPATH=/app\n")
        f.write("\n")
        
        for job in cron_jobs:
            if job.get('enabled', True):
                schedule = job['schedule']
                script = job['script']
                name = job['name']
                
                # Cron-Job Eintrag erstellen
                log_file = f"/app/logs/{name}.log"
                command = f"cd /app && python /app/scripts/{script} >> {log_file} 2>&1"
                
                f.write(f"# {job.get('description', name)}\n")
                f.write(f"{schedule} {command}\n")
                f.write("\n")
    
    print("Cron-Jobs erfolgreich generiert")
    
except Exception as e:
    print(f"Fehler beim Generieren der Cron-Jobs: {e}")
    sys.exit(1)
EOF

# Crontab installieren
if [ -f /tmp/crontab ]; then
    crontab /tmp/crontab
    log "Crontab installiert"
    rm /tmp/crontab
else
    error_exit "Crontab-Datei konnte nicht erstellt werden"
fi

# Cron-Daemon starten
log "Starte Cron-Daemon..."
cron

# Log-Rotation einrichten
log "Konfiguriere Log-Rotation..."
cat > /tmp/logrotate.conf << 'EOF'
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 appuser appuser
    postrotate
        /usr/bin/pkill -f "python.*scripts" || true
    endscript
}
EOF

# Initialer Health-Check
log "Führe initialen Health-Check durch..."
python /app/healthcheck.py || log "WARNUNG: Health-Check fehlgeschlagen"

# Status anzeigen
log "Aktive Cron-Jobs:"
crontab -l | grep -v "^#" | grep -v "^$" || log "Keine aktiven Cron-Jobs gefunden"

log "Python Log Checker erfolgreich gestartet"

# Signal-Handler für graceful shutdown
trap 'log "Empfange Shutdown-Signal..."; pkill -f cron; exit 0' SIGTERM SIGINT

# Container am Leben halten und auf Signale warten
log "Container läuft... (PID: $$)"
while true; do
    sleep 30
    
    # Prüfe ob Cron noch läuft
    if ! pgrep cron > /dev/null; then
        log "Cron-Daemon gestoppt, starte neu..."
        cron
    fi
    
    # Führe periodischen Health-Check durch
    if ! python /app/healthcheck.py > /dev/null 2>&1; then
        log "WARNUNG: Health-Check fehlgeschlagen"
    fi
done