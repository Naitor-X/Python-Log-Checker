#!/usr/bin/env python3
"""
Advanced Backup Checker
Erweiterte Version des ursprünglichen checkbackup-Scripts mit Docker-Kompatibilität
Prüft zeitbasierte Log-Verzeichnisse auf spezifische Dateien und Schlüsselwörter
"""

import os
import configparser
import datetime
import logging
import yaml
from typing import List, Tuple, Dict, Any
from email_utils import EmailSender

class AdvancedBackupChecker:
    """
    Erweiterte Backup-Checker-Klasse basierend auf dem ursprünglichen checkbackup-Script
    """
    
    def __init__(self, config_path: str = "/app/config/config.yaml"):
        """
        Initialisiert den AdvancedBackupChecker
        
        Args:
            config_path: Pfad zur YAML-Konfigurationsdatei
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.email_sender = EmailSender(config_path)
        
        # Konfiguration für erweiterten Backup-Check
        self.backup_check_config = self.config.get('advanced_backup_check', {})
        
        # Activity Log und Error/Warning Collections
        self.activity_log = []
        self.errors_warnings = []
        
    def _load_config(self) -> Dict[str, Any]:
        """Lädt die YAML-Konfigurationsdatei"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
            return {}
    
    def _setup_logging(self) -> logging.Logger:
        """Richtet Logging ein"""
        logger = logging.getLogger('AdvancedBackupChecker')
        
        if not logger.handlers:
            log_config = self.config.get('logging', {})
            log_level = getattr(logging, log_config.get('level', 'INFO'))
            
            log_file = self.config.get('logging', {}).get('file', '/app/logs/advanced_backup_checker.log')
            try:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
            except (OSError, PermissionError):
                # Fallback für Test-Umgebung
                log_file = './test-output/advanced_backup_checker.log'
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            console_handler = logging.StreamHandler()
            
            formatter = logging.Formatter(
                log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.setLevel(log_level)
        
        return logger
    
    def load_required_files(self) -> List[str]:
        """
        Lädt die Liste der erforderlichen Log-Dateien
        
        Returns:
            Liste der erforderlichen Log-Dateinamen
        """
        try:
            logfilelist_path = self.backup_check_config.get('logfilelist_path', '/app/config/logfilelist.txt')
            
            if os.path.exists(logfilelist_path):
                with open(logfilelist_path, 'r', encoding='utf-8') as f:
                    files = [line.strip() for line in f.readlines() if line.strip()]
                self.logger.info(f"Geladene erforderliche Dateien: {files}")
                return files
            else:
                # Fallback: Verwende Konfiguration aus YAML
                files = self.backup_check_config.get('required_log_files', [
                    'Administration.log',
                    'Nevaris.log', 
                    'Share_MSSQL.log'
                ])
                self.logger.warning(f"Logfilelist nicht gefunden, verwende Standard: {files}")
                return files
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Log-Dateiliste: {e}")
            return []
    
    def load_keywords(self) -> List[str]:
        """
        Lädt die Liste der Schlüsselwörter für die Fehlersuche
        
        Returns:
            Liste der Schlüsselwörter
        """
        try:
            keywords_path = self.backup_check_config.get('keywords_path', '/app/config/keywords.txt')
            
            if os.path.exists(keywords_path):
                with open(keywords_path, 'r', encoding='utf-8') as f:
                    keywords = [line.strip() for line in f.readlines() if line.strip()]
                self.logger.info(f"Geladene Schlüsselwörter: {keywords}")
                return keywords
            else:
                # Fallback: Verwende Konfiguration aus YAML
                keywords = self.backup_check_config.get('error_keywords', [
                    'denied', 'Denied', 'Warn', 'warn', 'Warning', 'fail', 'Fail'
                ])
                self.logger.warning(f"Keywords-Datei nicht gefunden, verwende Standard: {keywords}")
                return keywords
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Schlüsselwörter: {e}")
            return []
    
    def generate_date_range(self) -> List[str]:
        """
        Generiert die Liste der zu prüfenden Datumsverzeichnisse
        
        Returns:
            Liste der Datumsstrings im Format YYYY-MM-DD
        """
        try:
            days = int(self.backup_check_config.get('days_to_check', 1))
            startday = int(self.backup_check_config.get('start_day_offset', 0))
            
            today = datetime.date.today()
            dates = [(today - datetime.timedelta(days=i)).strftime('%Y-%m-%d') 
                    for i in range(startday, days)]
            
            self.logger.info(f"Generierte Datumsbereiche: {dates}")
            return dates
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Datumsgenerierung: {e}")
            return [datetime.date.today().strftime('%Y-%m-%d')]
    
    def check_log_files(self) -> bool:
        """
        Hauptfunktion: Prüft alle Log-Dateien auf Fehler und Warnungen
        
        Returns:
            True bei erfolgreicher Durchführung, False bei kritischen Fehlern
        """
        try:
            self.logger.info("🤖 Starte erweiterte Backup-Überprüfung...")
            
            # Konfiguration laden
            log_dir = self.backup_check_config.get('log_directory', '/app/data/logs')
            required_logs = self.load_required_files()
            keywords = self.load_keywords()
            dates = self.generate_date_range()
            
            if not required_logs:
                self.logger.error("Keine erforderlichen Log-Dateien definiert!")
                return False
            
            if not keywords:
                self.logger.warning("Keine Schlüsselwörter definiert - prüfe nur auf Dateiexistenz")
            
            # Reset der Collections
            self.activity_log = []
            self.errors_warnings = []
            
            # Überprüfung der Logdateien für jeden Tag
            for date in dates:
                date_dir = os.path.join(log_dir, date)
                self._check_date_directory(date_dir, date, required_logs, keywords)
            
            # Ergebnisse speichern und E-Mail senden
            return self._process_results()
            
        except Exception as e:
            error_msg = f"Kritischer Fehler bei der Backup-Überprüfung: {e}"
            self.logger.error(error_msg)
            self.email_sender.send_error_notification("advanced_backup_checker.py", error_msg)
            return False
    
    def _check_date_directory(self, date_dir: str, date: str, required_logs: List[str], keywords: List[str]):
        """
        Prüft ein einzelnes Datumsverzeichnis
        
        Args:
            date_dir: Pfad zum Datumsverzeichnis
            date: Datumsstring
            required_logs: Liste der erforderlichen Log-Dateien
            keywords: Liste der Schlüsselwörter
        """
        if os.path.isdir(date_dir):
            self.activity_log.append(f'Überprüfe Ordner: {date_dir}')
            self.logger.debug(f"Prüfe Verzeichnis: {date_dir}")
            
            for log_file in required_logs:
                log_path = os.path.join(date_dir, log_file)
                self._check_log_file(log_path, date, log_file, keywords)
        else:
            error_msg = f'Fehlender Ordner: {date_dir}'
            self.errors_warnings.append((date, '', error_msg))
            self.activity_log.append(error_msg)
            self.logger.warning(error_msg)
    
    def _check_log_file(self, log_path: str, date: str, log_file: str, keywords: List[str]):
        """
        Prüft eine einzelne Log-Datei
        
        Args:
            log_path: Vollständiger Pfad zur Log-Datei
            date: Datumsstring
            log_file: Name der Log-Datei
            keywords: Liste der Schlüsselwörter
        """
        if os.path.isfile(log_path):
            self.activity_log.append(f'Überprüfe Datei: {log_path}')
            self.logger.debug(f"Prüfe Datei: {log_path}")
            
            try:
                # Dateigröße prüfen
                file_size = os.path.getsize(log_path)
                if file_size == 0:
                    self.errors_warnings.append((date, log_file, 'Leere Log-Datei'))
                    return
                
                # Dateiinhalt auf Schlüsselwörter prüfen
                error_count = self._scan_file_for_keywords(log_path, date, log_file, keywords)
                
                if error_count == 0 and keywords:
                    self.activity_log.append(f'Keine Fehler in {log_file} gefunden')
                
            except Exception as e:
                error_msg = f'Fehler beim Lesen der Datei {log_file}: {str(e)}'
                self.errors_warnings.append((date, log_file, error_msg))
                self.logger.error(error_msg)
        else:
            error_msg = f'Fehlende Datei: {log_file}'
            self.errors_warnings.append((date, log_file, error_msg))
            self.activity_log.append(error_msg)
            self.logger.warning(f"Datei nicht gefunden: {log_path}")
    
    def _scan_file_for_keywords(self, log_path: str, date: str, log_file: str, keywords: List[str]) -> int:
        """
        Scannt eine Datei nach Schlüsselwörtern
        
        Args:
            log_path: Pfad zur Log-Datei
            date: Datumsstring
            log_file: Name der Log-Datei
            keywords: Liste der Schlüsselwörter
            
        Returns:
            Anzahl gefundener Fehler
        """
        error_count = 0
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    for keyword in keywords:
                        if keyword.lower() in line.lower():
                            error_entry = f'Zeile {line_number}: {line}'
                            self.errors_warnings.append((date, log_file, error_entry))
                            error_count += 1
                            self.logger.debug(f"Schlüsselwort '{keyword}' gefunden in {log_file}:{line_number}")
                            break  # Nur ein Keyword pro Zeile zählen
        
        except Exception as e:
            self.logger.error(f"Fehler beim Scannen von {log_path}: {e}")
            error_count += 1
        
        return error_count
    
    def _process_results(self) -> bool:
        """
        Verarbeitet die Ergebnisse: speichert Logs und sendet E-Mails
        
        Returns:
            True bei Erfolg
        """
        try:
            today = datetime.date.today()
            logcheck_dir = self.backup_check_config.get('output_directory', '/app/logs/logcheck')
            
            # Verzeichnis erstellen falls nicht vorhanden
            os.makedirs(logcheck_dir, exist_ok=True)
            
            # Log-Dateien erstellen
            log_filename = os.path.join(logcheck_dir, f'{today}-Logcheck.log')
            errwarn_filename = os.path.join(logcheck_dir, f'{today}-ErrWarn.log')
            
            # Aktivitätsprotokoll speichern
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(f"Backup-Check Aktivitätsprotokoll - {today}\n")
                f.write("=" * 50 + "\n\n")
                for log_entry in self.activity_log:
                    f.write(log_entry + '\n')
            
            # Fehler-/Warnungsprotokoll speichern
            with open(errwarn_filename, 'w', encoding='utf-8') as f:
                f.write(f"Backup-Check Fehler/Warnungen - {today}\n")
                f.write("=" * 50 + "\n\n")
                if self.errors_warnings:
                    for err in self.errors_warnings:
                        f.write(f'{err[0]} - {err[1]} - {err[2]}\n')
                else:
                    f.write("Keine Fehler oder Warnungen gefunden.\n")
            
            # E-Mail senden
            return self._send_notification_email(errwarn_filename)
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Ergebnisverarbeitung: {e}")
            return False
    
    def _send_notification_email(self, errwarn_filename: str) -> bool:
        """
        Sendet Benachrichtigungs-E-Mail mit Ergebnissen
        
        Args:
            errwarn_filename: Pfad zur Fehler-/Warnungsdatei
            
        Returns:
            True bei erfolgreichem Versand
        """
        try:
            # E-Mail-Konfiguration
            server_name = self.backup_check_config.get('server_name', 'Docker-Container')
            subject_prefix = self.backup_check_config.get('email_subject_prefix', 'Backup-Check')
            
            if self.errors_warnings:
                # Fehler gefunden - sende Datei als Anhang
                subject = f"{subject_prefix} {server_name} - FEHLER GEFUNDEN"
                body = f"""Es wurden {len(self.errors_warnings)} Fehler oder Warnungen gefunden.
                
Überprüfte Zeiträume: {self.generate_date_range()}
Server: {server_name}
Zeitstempel: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Details siehe Anhang."""
                
                # E-Mail mit Anhang senden
                success = self.email_sender.send_email(
                    subject=subject,
                    body=body,
                    email_type="error",
                    attachments=[errwarn_filename]
                )
                
                self.logger.info(f"Fehler-E-Mail gesendet: {len(self.errors_warnings)} Probleme gefunden")
                
            else:
                # Keine Fehler - kurze Erfolgsmeldung
                subject = f"{subject_prefix} {server_name} - ALLES OK"
                body = f"""Backup-Check erfolgreich abgeschlossen - keine Fehler gefunden.

Überprüfte Zeiträume: {self.generate_date_range()}
Server: {server_name}
Zeitstempel: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Alle erforderlichen Log-Dateien wurden erfolgreich überprüft."""
                
                success = self.email_sender.send_email(
                    subject=subject,
                    body=body,
                    email_type="success"
                )
                
                self.logger.info("Erfolgs-E-Mail gesendet: Keine Probleme gefunden")
            
            if success:
                self.activity_log.append('E-Mail erfolgreich gesendet')
            else:
                self.activity_log.append('E-Mail konnte nicht gesendet werden')
                
            return success
            
        except Exception as e:
            error_msg = f'E-Mail konnte nicht gesendet werden: {e}'
            self.activity_log.append(error_msg)
            self.logger.error(error_msg)
            return False
    
    def generate_summary_report(self) -> str:
        """
        Generiert einen zusammenfassenden Bericht
        
        Returns:
            Formatierter Bericht als String
        """
        report_lines = []
        report_lines.append("🤖 ERWEITERTE BACKUP-ÜBERPRÜFUNG")
        report_lines.append("=" * 50)
        report_lines.append(f"Zeitstempel: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Server: {self.backup_check_config.get('server_name', 'Docker-Container')}")
        report_lines.append("")
        
        # Überprüfte Zeiträume
        dates = self.generate_date_range()
        report_lines.append(f"Überprüfte Zeiträume: {', '.join(dates)}")
        report_lines.append(f"Anzahl Aktivitäten: {len(self.activity_log)}")
        report_lines.append(f"Gefundene Probleme: {len(self.errors_warnings)}")
        report_lines.append("")
        
        # Problem-Details
        if self.errors_warnings:
            report_lines.append("❌ GEFUNDENE PROBLEME:")
            report_lines.append("-" * 30)
            for i, (date, file, error) in enumerate(self.errors_warnings[:10], 1):  # Max 10 zeigen
                report_lines.append(f"{i}. {date} - {file}: {error}")
            
            if len(self.errors_warnings) > 10:
                report_lines.append(f"... und {len(self.errors_warnings) - 10} weitere")
        else:
            report_lines.append("✅ KEINE PROBLEME GEFUNDEN")
        
        return "\n".join(report_lines)


def main():
    """
    Hauptfunktion des erweiterten Backup-Checkers
    """
    checker = AdvancedBackupChecker()
    success = checker.check_log_files()
    
    # Summary-Report loggen
    summary = checker.generate_summary_report()
    checker.logger.info(f"Zusammenfassung:\n{summary}")
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()