#!/usr/bin/env python3
"""
Backup-Monitor Script
Überwacht Backup-Log-Dateien auf Fehler und Vollständigkeit
"""

import os
import glob
import re
import yaml
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from email_utils import EmailSender

class BackupMonitor:
    """
    Klasse zur Überwachung von Backup-Logs
    """
    
    def __init__(self, config_path: str = "/app/config/config.yaml"):
        """
        Initialisiert den BackupMonitor
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.email_sender = EmailSender(config_path)
        
        # Backup-spezifische Konfiguration
        self.backup_log_path = self.config.get('paths', {}).get('backup_logs', '/app/data/backup')
        self.log_patterns = self.config.get('paths', {}).get('log_patterns', {})
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Lädt die YAML-Konfigurationsdatei
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
            return {}
    
    def _setup_logging(self) -> logging.Logger:
        """
        Richtet Logging ein
        """
        logger = logging.getLogger('BackupMonitor')
        
        if not logger.handlers:
            log_config = self.config.get('logging', {})
            log_level = getattr(logging, log_config.get('level', 'INFO'))
            
            # File Handler
            log_file = log_config.get('file', '/app/logs/backup_monitor.log')
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
    
    def find_backup_logs(self) -> List[str]:
        """
        Findet alle Backup-Log-Dateien
        
        Returns:
            Liste der gefundenen Log-Dateien
        """
        try:
            pattern = os.path.join(self.backup_log_path, self.log_patterns.get('backup', 'backup_*.log'))
            log_files = glob.glob(pattern)
            
            # Nach Änderungszeit sortieren (neueste zuerst)
            log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            self.logger.info(f"Gefundene Backup-Log-Dateien: {len(log_files)}")
            return log_files
            
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen von Backup-Logs: {e}")
            return []
    
    def analyze_log_file(self, log_file: str) -> Dict[str, Any]:
        """
        Analysiert eine einzelne Log-Datei
        
        Args:
            log_file: Pfad zur Log-Datei
            
        Returns:
            Dictionary mit Analyse-Ergebnissen
        """
        analysis = {
            'file': log_file,
            'file_size': 0,
            'last_modified': None,
            'errors': [],
            'warnings': [],
            'success_indicators': [],
            'backup_completed': False,
            'duration': None,
            'transferred_data': None
        }
        
        try:
            # Datei-Metadaten
            stat = os.stat(log_file)
            analysis['file_size'] = stat.st_size
            analysis['last_modified'] = datetime.fromtimestamp(stat.st_mtime)
            
            # Log-Inhalt analysieren
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                analysis.update(self._parse_log_content(content))
            
            self.logger.debug(f"Analysiert: {log_file}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Analysieren von {log_file}: {e}")
            analysis['errors'].append(f"Analyse-Fehler: {str(e)}")
        
        return analysis
    
    def _parse_log_content(self, content: str) -> Dict[str, Any]:
        """
        Parst den Inhalt einer Log-Datei
        
        Args:
            content: Log-Datei-Inhalt
            
        Returns:
            Dictionary mit geparsten Informationen
        """
        result = {
            'errors': [],
            'warnings': [],
            'success_indicators': [],
            'backup_completed': False,
            'duration': None,
            'transferred_data': None
        }
        
        lines = content.split('\n')
        
        # Regex-Patterns für verschiedene Log-Formate
        error_patterns = [
            r'(?i)error:?\s*(.*)',
            r'(?i)failed:?\s*(.*)',
            r'(?i)exception:?\s*(.*)',
            r'(?i)critical:?\s*(.*)',
            r'(?i)cannot\s+(.*)',
            r'(?i)permission\s+denied',
            r'(?i)no\s+space\s+left',
            r'(?i)connection\s+refused'
        ]
        
        warning_patterns = [
            r'(?i)warning:?\s*(.*)',
            r'(?i)warn:?\s*(.*)',
            r'(?i)skipped:?\s*(.*)',
            r'(?i)timeout:?\s*(.*)'
        ]
        
        success_patterns = [
            r'(?i)backup\s+completed?',
            r'(?i)successfully?\s+completed?',
            r'(?i)finished\s+successfully?',
            r'(?i)done\s+successfully?',
            r'(?i)backup\s+successful'
        ]
        
        # Zeilen durchgehen und Patterns suchen
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Fehler suchen
            for pattern in error_patterns:
                match = re.search(pattern, line)
                if match:
                    result['errors'].append(line)
                    break
            
            # Warnungen suchen
            for pattern in warning_patterns:
                match = re.search(pattern, line)
                if match:
                    result['warnings'].append(line)
                    break
            
            # Erfolgs-Indikatoren suchen
            for pattern in success_patterns:
                if re.search(pattern, line):
                    result['success_indicators'].append(line)
                    result['backup_completed'] = True
                    break
            
            # Backup-Dauer extrahieren
            duration_match = re.search(r'(?i)duration:?\s*(\d+:\d+:\d+|\d+\s*(?:hours?|hrs?|minutes?|mins?|seconds?|secs?))', line)
            if duration_match:
                result['duration'] = duration_match.group(1)
            
            # Übertragene Datenmenge extrahieren
            data_match = re.search(r'(?i)transferred:?\s*(\d+(?:\.\d+)?\s*(?:GB|MB|KB|TB|bytes?))', line)
            if data_match:
                result['transferred_data'] = data_match.group(1)
        
        return result
    
    def check_backup_freshness(self, log_file: str, max_age_hours: int = 25) -> bool:
        """
        Prüft, ob ein Backup aktuell genug ist
        
        Args:
            log_file: Pfad zur Log-Datei
            max_age_hours: Maximales Alter in Stunden
            
        Returns:
            True wenn Backup aktuell, False wenn zu alt
        """
        try:
            stat = os.stat(log_file)
            file_age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            
            is_fresh = file_age.total_seconds() < (max_age_hours * 3600)
            
            if not is_fresh:
                self.logger.warning(f"Backup zu alt: {log_file} (Alter: {file_age})")
            
            return is_fresh
            
        except Exception as e:
            self.logger.error(f"Fehler beim Prüfen der Backup-Aktualität: {e}")
            return False
    
    def generate_report(self, analyses: List[Dict[str, Any]]) -> str:
        """
        Generiert einen Bericht aus den Analyse-Ergebnissen
        
        Args:
            analyses: Liste der Analyse-Ergebnisse
            
        Returns:
            Formatierter Bericht als String
        """
        report_lines = []
        report_lines.append("🤖 BACKUP-MONITORING BERICHT")
        report_lines.append("=" * 50)
        report_lines.append(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Analysierte Dateien: {len(analyses)}")
        report_lines.append("")
        
        total_errors = 0
        total_warnings = 0
        successful_backups = 0
        
        for analysis in analyses:
            file_name = os.path.basename(analysis['file'])
            report_lines.append(f"📁 {file_name}")
            report_lines.append("-" * 30)
            
            # Dateigröße und Alter
            size_mb = analysis['file_size'] / (1024 * 1024)
            report_lines.append(f"Größe: {size_mb:.2f} MB")
            
            if analysis['last_modified']:
                age = datetime.now() - analysis['last_modified']
                report_lines.append(f"Alter: {age}")
            
            # Backup-Status
            if analysis['backup_completed']:
                report_lines.append("✅ Backup abgeschlossen")
                successful_backups += 1
            else:
                report_lines.append("❌ Backup nicht abgeschlossen")
            
            # Dauer und Datenmenge
            if analysis['duration']:
                report_lines.append(f"Dauer: {analysis['duration']}")
            
            if analysis['transferred_data']:
                report_lines.append(f"Übertragen: {analysis['transferred_data']}")
            
            # Fehler
            if analysis['errors']:
                report_lines.append(f"❌ Fehler ({len(analysis['errors'])}):")
                for error in analysis['errors'][:5]:  # Maximal 5 Fehler anzeigen
                    report_lines.append(f"   • {error}")
                total_errors += len(analysis['errors'])
            
            # Warnungen
            if analysis['warnings']:
                report_lines.append(f"⚠️ Warnungen ({len(analysis['warnings'])}):")
                for warning in analysis['warnings'][:3]:  # Maximal 3 Warnungen anzeigen
                    report_lines.append(f"   • {warning}")
                total_warnings += len(analysis['warnings'])
            
            report_lines.append("")
        
        # Zusammenfassung
        report_lines.append("📊 ZUSAMMENFASSUNG")
        report_lines.append("=" * 50)
        report_lines.append(f"Erfolgreiche Backups: {successful_backups}/{len(analyses)}")
        report_lines.append(f"Gesamte Fehler: {total_errors}")
        report_lines.append(f"Gesamte Warnungen: {total_warnings}")
        
        # Status bestimmen
        if total_errors > 0:
            report_lines.append("🔴 STATUS: KRITISCH - Fehler gefunden!")
        elif total_warnings > 0:
            report_lines.append("🟡 STATUS: WARNUNG - Warnungen vorhanden")
        elif successful_backups == len(analyses):
            report_lines.append("🟢 STATUS: OK - Alle Backups erfolgreich")
        else:
            report_lines.append("🔴 STATUS: KRITISCH - Unvollständige Backups!")
        
        return "\n".join(report_lines)
    
    def run_monitoring(self) -> bool:
        """
        Führt das komplette Backup-Monitoring durch
        
        Returns:
            True bei Erfolg, False bei kritischen Fehlern
        """
        try:
            self.logger.info("🤖 Starte Backup-Monitoring...")
            
            # Log-Dateien finden
            log_files = self.find_backup_logs()
            
            if not log_files:
                message = "Keine Backup-Log-Dateien gefunden!"
                self.logger.error(message)
                self.email_sender.send_error_notification("backup_monitor.py", message)
                return False
            
            # Log-Dateien analysieren
            analyses = []
            for log_file in log_files[:10]:  # Maximal 10 neueste Dateien
                analysis = self.analyze_log_file(log_file)
                
                # Aktualität prüfen
                if not self.check_backup_freshness(log_file):
                    analysis['errors'].append("Backup zu alt")
                
                analyses.append(analysis)
            
            # Bericht generieren
            report = self.generate_report(analyses)
            self.logger.info("Bericht generiert")
            
            # E-Mail-Benachrichtigung senden
            total_errors = sum(len(a['errors']) for a in analyses)
            total_warnings = sum(len(a['warnings']) for a in analyses)
            
            if total_errors > 0:
                self.email_sender.send_email(
                    subject="Backup-Monitoring: KRITISCHE FEHLER",
                    body=report,
                    email_type="error"
                )
            elif total_warnings > 0:
                self.email_sender.send_email(
                    subject="Backup-Monitoring: WARNUNGEN",
                    body=report,
                    email_type="warning"
                )
            else:
                self.email_sender.send_email(
                    subject="Backup-Monitoring: ALLES OK",
                    body=report,
                    email_type="success"
                )
            
            self.logger.info("✅ Backup-Monitoring abgeschlossen")
            return True
            
        except Exception as e:
            error_msg = f"Kritischer Fehler im Backup-Monitoring: {e}"
            self.logger.error(error_msg)
            self.email_sender.send_error_notification("backup_monitor.py", error_msg)
            return False


def main():
    """
    Hauptfunktion des Backup-Monitors
    """
    monitor = BackupMonitor()
    success = monitor.run_monitoring()
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()