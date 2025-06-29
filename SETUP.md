# 🤖 Setup-Anleitung für Python Log Checker

## Schritt 1: Umgebungsvariablen konfigurieren

1. Kopiere die Vorlagen-Datei:
   ```bash
   cp .env.template .env
   ```

2. Bearbeite die `.env` Datei und fülle die Werte aus:
   ```bash
   nano .env
   ```

### Wichtige Konfigurationen:

**SMTP-Einstellungen:**
- `SMTP_SERVER`: SMTP-Server (z.B. smtp.gmail.com)
- `SMTP_PORT`: Port (587 für TLS, 465 für SSL)
- `SMTP_USERNAME`: Deine E-Mail-Adresse
- `SMTP_PASSWORD`: App-Passwort (NICHT dein normales Passwort!)
- `SMTP_DEFAULT_RECIPIENTS`: Empfänger-E-Mails (kommagetrennt)

**System-Einstellungen:**
- `SYSTEM_HOSTNAME`: Hostname für E-Mail-Benachrichtigungen
- `SYSTEM_ENVIRONMENT`: production/development

## Schritt 2: Sicherheitshinweise

✅ **Was ist sicher:**
- `.env` Datei ist in `.gitignore` und wird nicht committed
- Keine Passwörter in der Konfigurationsdatei
- Umgebungsvariablen werden sicher geladen

⚠️ **Wichtige Sicherheitshinweise:**
- Verwende NIEMALS dein normales E-Mail-Passwort
- Erstelle ein App-Passwort für Gmail/Outlook
- Teile die `.env` Datei niemals mit anderen
- Prüfe, dass `.env` nicht in Git ist: `git status`

## Schritt 3: Bereinigte Projektstruktur

Folgende Ordner/Dateien wurden als nicht mehr benötigt entfernt:
- `checkbackup/` - Alte Implementierung
- `migrated_config/` - Temporäre Migrationsdateien
- `test-output/` - Temporäre Testdateien
- `migrate_from_checkbackup.py` - Einmaliges Migrationsskript
- `test_*.py` - Temporäre Testdateien

## Schritt 4: Container starten

```bash
docker-compose up -d
```

## Schritt 5: Testen

```bash
# E-Mail-Konfiguration testen
docker-compose exec log-checker python /app/scripts/email_utils.py test
```

## Troubleshooting

**Fehler beim E-Mail-Versand:**
1. Prüfe SMTP-Konfiguration in `.env`
2. Verwende App-Passwort statt normalem Passwort
3. Prüfe Firewall-Einstellungen
4. Überprüfe Container-Logs: `docker-compose logs`

**Konfigurationsfehler:**
1. Prüfe `.env` Datei auf Syntax-Fehler
2. Stelle sicher, dass alle Pflichtfelder ausgefüllt sind
3. Überprüfe Dateiberechtigungen

## Nächste Schritte

1. Erstelle deine `.env` Datei
2. Konfiguriere SMTP-Einstellungen
3. Teste die E-Mail-Funktionalität
4. Passe Log-Verzeichnisse in `docker-compose.yml` an