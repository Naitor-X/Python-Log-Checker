#!/usr/bin/env python3
"""
Health-Check-Script für den Python Log Checker Container
Überprüft den Status der wichtigsten Komponenten
"""

import os
import sys
import yaml
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any, List

class HealthChecker:
    """
    Klasse für Container Health-Checks
    """
    
    def __init__(self):
        """
        Initialisiert den HealthChecker
        """
        self.config_path = "/app/config/config.yaml"
        self.config = self._load_config()
        self.checks = []
        self.failed_checks = []
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Lädt die Konfigurationsdatei
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            return {}
    
    def _log_check(self, check_name: str, status: bool, message: str = ""):
        """
        Protokolliert einen Check
        
        Args:
            check_name: Name des Checks
            status: True bei Erfolg, False bei Fehler
            message: Zusätzliche Nachricht
        """
        self.checks.append({
            'name': check_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now()
        })
        
        if not status:
            self.failed_checks.append(check_name)
    
    def check_config_file(self) -> bool:
        """
        Prüft, ob die Konfigurationsdatei existiert und gültig ist
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            if not os.path.exists(self.config_path):
                self._log_check("config_exists", False, f"Konfigurationsdatei nicht gefunden: {self.config_path}")
                return False
            
            if not self.config:
                self._log_check("config_valid", False, "Konfigurationsdatei ist ungültig oder leer")
                return False
            
            # Prüfe wichtige Konfigurationsabschnitte
            required_sections = ['cron_jobs', 'smtp', 'paths', 'logging']
            for section in required_sections:
                if section not in self.config:
                    self._log_check("config_complete", False, f"Konfigurationsabschnitt '{section}' fehlt")
                    return False
            
            self._log_check("config", True, "Konfigurationsdatei OK")
            return True
            
        except Exception as e:
            self._log_check("config", False, f"Konfigurationsfehler: {e}")
            return False
    
    def check_directories(self) -> bool:
        """
        Prüft, ob alle erforderlichen Verzeichnisse existieren
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            required_dirs = ['/app/config', '/app/scripts', '/app/logs', '/app/data']
            paths_config = self.config.get('paths', {})
            
            # Zusätzliche Pfade aus Konfiguration
            for key, path in paths_config.items():
                if isinstance(path, str) and path.startswith('/app'):
                    required_dirs.append(path)
            
            missing_dirs = []
            for directory in required_dirs:
                if not os.path.exists(directory):
                    missing_dirs.append(directory)
            
            if missing_dirs:
                self._log_check("directories", False, f"Fehlende Verzeichnisse: {', '.join(missing_dirs)}")
                return False
            
            self._log_check("directories", True, "Alle Verzeichnisse vorhanden")
            return True
            
        except Exception as e:
            self._log_check("directories", False, f"Verzeichnisprüfung fehlgeschlagen: {e}")
            return False
    
    def check_cron_service(self) -> bool:
        """
        Prüft, ob der Cron-Service läuft
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Prüfe, ob cron-Prozess läuft
            result = subprocess.run(['pgrep', 'cron'], capture_output=True, text=True)
            
            if result.returncode != 0:
                self._log_check("cron_service", False, "Cron-Service läuft nicht")
                return False
            
            # Prüfe, ob Crontab installiert ist
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            
            if result.returncode != 0:
                self._log_check("cron_crontab", False, "Keine Crontab installiert")
                return False
            
            # Prüfe, ob Cron-Jobs konfiguriert sind
            crontab_content = result.stdout
            if not crontab_content.strip() or crontab_content.count('\n') < 2:
                self._log_check("cron_jobs", False, "Keine aktiven Cron-Jobs gefunden")
                return False
            
            self._log_check("cron", True, "Cron-Service und Jobs OK")
            return True
            
        except Exception as e:
            self._log_check("cron", False, f"Cron-Prüfung fehlgeschlagen: {e}")
            return False
    
    def check_python_modules(self) -> bool:
        """
        Prüft, ob alle erforderlichen Python-Module verfügbar sind
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            required_modules = ['yaml', 'smtplib', 'schedule', 'logging']
            missing_modules = []
            
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                self._log_check("python_modules", False, f"Fehlende Module: {', '.join(missing_modules)}")
                return False
            
            self._log_check("python_modules", True, "Alle Python-Module verfügbar")
            return True
            
        except Exception as e:
            self._log_check("python_modules", False, f"Python-Modul-Prüfung fehlgeschlagen: {e}")
            return False
    
    def check_disk_space(self) -> bool:
        """
        Prüft den verfügbaren Speicherplatz
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Prüfe Speicherplatz in wichtigen Verzeichnissen
            paths_to_check = ['/app/logs', '/app/data', '/tmp']
            
            for path in paths_to_check:
                if os.path.exists(path):
                    statvfs = os.statvfs(path)
                    
                    # Verfügbarer Speicher in MB
                    available_mb = (statvfs.f_bavail * statvfs.f_frsize) / (1024 * 1024)
                    
                    # Warnung bei weniger als 100 MB
                    if available_mb < 100:
                        self._log_check("disk_space", False, f"Wenig Speicherplatz in {path}: {available_mb:.1f} MB")
                        return False
            
            self._log_check("disk_space", True, "Speicherplatz ausreichend")
            return True
            
        except Exception as e:
            self._log_check("disk_space", False, f"Speicherplatz-Prüfung fehlgeschlagen: {e}")
            return False
    
    def check_log_files(self) -> bool:
        """
        Prüft den Status der Log-Dateien
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            log_dir = "/app/logs"
            
            if not os.path.exists(log_dir):
                self._log_check("log_files", False, f"Log-Verzeichnis nicht gefunden: {log_dir}")
                return False
            
            # Prüfe, ob Log-Dateien schreibbar sind
            test_log = os.path.join(log_dir, "healthcheck_test.log")
            try:
                with open(test_log, 'w') as f:
                    f.write("Health check test\n")
                os.remove(test_log)
            except Exception:
                self._log_check("log_files", False, "Log-Verzeichnis nicht schreibbar")
                return False
            
            # Prüfe auf sehr große Log-Dateien (> 100 MB)
            large_files = []
            for file in os.listdir(log_dir):
                file_path = os.path.join(log_dir, file)
                if os.path.isfile(file_path):
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    if size_mb > 100:
                        large_files.append(f"{file}: {size_mb:.1f}MB")
            
            if large_files:
                self._log_check("log_files", False, f"Große Log-Dateien: {', '.join(large_files)}")
                return False
            
            self._log_check("log_files", True, "Log-Dateien OK")
            return True
            
        except Exception as e:
            self._log_check("log_files", False, f"Log-Datei-Prüfung fehlgeschlagen: {e}")
            return False
    
    def check_smtp_config(self) -> bool:
        """
        Prüft die SMTP-Konfiguration (ohne tatsächliche Verbindung)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            smtp_config = self.config.get('smtp', {})
            
            required_fields = ['server', 'port', 'username', 'password', 'from_email']
            missing_fields = []
            
            for field in required_fields:
                if not smtp_config.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                self._log_check("smtp_config", False, f"SMTP-Konfiguration unvollständig: {', '.join(missing_fields)}")
                return False
            
            self._log_check("smtp_config", True, "SMTP-Konfiguration vollständig")
            return True
            
        except Exception as e:
            self._log_check("smtp_config", False, f"SMTP-Konfigurationsprüfung fehlgeschlagen: {e}")
            return False
    
    def check_scripts(self) -> bool:
        """
        Prüft, ob die konfigurierten Scripts existieren
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            scripts_dir = "/app/scripts"
            cron_jobs = self.config.get('cron_jobs', [])
            
            missing_scripts = []
            for job in cron_jobs:
                if job.get('enabled', True):
                    script_name = job.get('script')
                    if script_name:
                        script_path = os.path.join(scripts_dir, script_name)
                        if not os.path.exists(script_path):
                            missing_scripts.append(script_name)
            
            if missing_scripts:
                self._log_check("scripts", False, f"Fehlende Scripts: {', '.join(missing_scripts)}")
                return False
            
            self._log_check("scripts", True, "Alle konfigurierten Scripts vorhanden")
            return True
            
        except Exception as e:
            self._log_check("scripts", False, f"Script-Prüfung fehlgeschlagen: {e}")
            return False
    
    def run_all_checks(self) -> bool:
        """
        Führt alle Health-Checks durch
        
        Returns:
            True wenn alle Checks erfolgreich, False bei Fehlern
        """
        checks_to_run = [
            self.check_config_file,
            self.check_directories,
            self.check_python_modules,
            self.check_disk_space,
            self.check_log_files,
            self.check_smtp_config,
            self.check_scripts,
            self.check_cron_service
        ]
        
        all_passed = True
        
        for check in checks_to_run:
            try:
                result = check()
                if not result:
                    all_passed = False
            except Exception as e:
                self._log_check(check.__name__, False, f"Unerwarteter Fehler: {e}")
                all_passed = False
        
        return all_passed
    
    def get_status_report(self) -> str:
        """
        Erstellt einen Status-Bericht
        
        Returns:
            Formatierter Status-Bericht
        """
        lines = []
        lines.append("🤖 HEALTH CHECK BERICHT")
        lines.append("=" * 40)
        lines.append(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Durchgeführte Checks: {len(self.checks)}")
        lines.append(f"Fehlgeschlagene Checks: {len(self.failed_checks)}")
        lines.append("")
        
        # Details der Checks
        for check in self.checks:
            status_icon = "✅" if check['status'] else "❌"
            lines.append(f"{status_icon} {check['name']}")
            if check['message']:
                lines.append(f"   {check['message']}")
        
        lines.append("")
        
        # Gesamtstatus
        if not self.failed_checks:
            lines.append("🟢 GESAMTSTATUS: GESUND")
        else:
            lines.append("🔴 GESAMTSTATUS: PROBLEME ERKANNT")
            lines.append(f"Fehlgeschlagene Checks: {', '.join(self.failed_checks)}")
        
        return "\n".join(lines)


def main():
    """
    Hauptfunktion für Health-Check
    """
    checker = HealthChecker()
    
    # Alle Checks durchführen
    healthy = checker.run_all_checks()
    
    # Bei Problemen: Report ausgeben
    if not healthy:
        print(checker.get_status_report())
        sys.exit(1)
    
    # Bei Erfolg: Kurze OK-Meldung
    print("🤖 Health Check: OK")
    sys.exit(0)


if __name__ == "__main__":
    main()