#!/usr/bin/env python3
"""
System-Monitor Script
Überwacht System-Log-Dateien auf kritische Ereignisse
"""

import os
import glob
import re
import yaml
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from email_utils import EmailSender

class SystemMonitor:
    """
    Klasse zur Überwachung von System-Logs
    """
    
    def __init__(self, config_path: str = "/app/config/config.yaml"):
        """
        Initialisiert den SystemMonitor
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.email_sender = EmailSender(config_path)
        
        # System-spezifische Konfiguration
        self.system_log_path = self.config.get('paths', {}).get('system_logs', '/app/data/system')
        
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
        logger = logging.getLogger('SystemMonitor')
        
        if not logger.handlers:
            log_config = self.config.get('logging', {})
            log_level = getattr(logging, log_config.get('level', 'INFO'))
            
            log_file = '/app/logs/system_monitor.log'
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
    
    def find_system_logs(self) -> List[str]:
        """Findet alle System-Log-Dateien"""
        try:
            patterns = [
                os.path.join(self.system_log_path, 'syslog*'),
                os.path.join(self.system_log_path, 'messages*'),
                os.path.join(self.system_log_path, 'kern.log*'),
                os.path.join(self.system_log_path, 'auth.log*'),
            ]
            
            log_files = []
            for pattern in patterns:
                log_files.extend(glob.glob(pattern))
            
            # Nach Änderungszeit sortieren
            log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            self.logger.info(f"Gefundene System-Log-Dateien: {len(log_files)}")
            return log_files
            
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen von System-Logs: {e}")
            return []
    
    def analyze_system_log(self, log_file: str, hours_back: int = 1) -> Dict[str, Any]:
        """
        Analysiert eine System-Log-Datei der letzten Stunden
        
        Args:
            log_file: Pfad zur Log-Datei
            hours_back: Anzahl Stunden rückwirkend zu analysieren
        """
        analysis = {
            'file': log_file,
            'errors': [],
            'warnings': [],
            'critical_events': [],
            'security_events': [],
            'disk_space_warnings': [],
            'memory_issues': [],
            'network_issues': []
        }
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Zeitstempel extrahieren und prüfen
                    if not self._is_recent_log_entry(line, cutoff_time):
                        continue
                    
                    # Verschiedene Event-Typen analysieren
                    self._analyze_line(line, analysis)
            
            self.logger.debug(f"Analysiert: {log_file}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Analysieren von {log_file}: {e}")
            analysis['errors'].append(f"Analyse-Fehler: {str(e)}")
        
        return analysis
    
    def _is_recent_log_entry(self, line: str, cutoff_time: datetime) -> bool:
        """Prüft, ob ein Log-Eintrag aus dem gewünschten Zeitraum stammt"""
        try:
            # Verschiedene Zeitstempel-Formate unterstützen
            timestamp_patterns = [
                r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',  # Nov 21 14:30:45
                r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',   # 2023-11-21T14:30:45
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',   # 2023-11-21 14:30:45
            ]
            
            for pattern in timestamp_patterns:
                match = re.search(pattern, line)
                if match:
                    timestamp_str = match.group(1)
                    
                    # Zeitstempel parsen (vereinfacht)
                    try:
                        if 'T' in timestamp_str or '-' in timestamp_str:
                            # ISO-Format
                            if 'T' in timestamp_str:
                                log_time = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
                            else:
                                log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        else:
                            # Syslog-Format (Jahr hinzufügen)
                            log_time = datetime.strptime(f"{datetime.now().year} {timestamp_str}", '%Y %b %d %H:%M:%S')
                        
                        return log_time >= cutoff_time
                    except ValueError:
                        # Wenn Zeitstempel nicht parsbar, als aktuell betrachten
                        return True
            
            # Wenn kein Zeitstempel gefunden, als aktuell betrachten
            return True
            
        except Exception:
            return True
    
    def _analyze_line(self, line: str, analysis: Dict[str, Any]):
        """Analysiert eine einzelne Log-Zeile"""
        line_lower = line.lower()
        
        # Kritische Fehler
        critical_patterns = [
            r'(?i)kernel panic',
            r'(?i)out of memory',
            r'(?i)segmentation fault',
            r'(?i)system crash',
            r'(?i)fatal error',
            r'(?i)emergency',
            r'(?i)critical.*error'
        ]
        
        for pattern in critical_patterns:
            if re.search(pattern, line):
                analysis['critical_events'].append(line)
                break
        
        # Sicherheitsereignisse
        security_patterns = [
            r'(?i)authentication failure',
            r'(?i)failed.*login',
            r'(?i)invalid.*user',
            r'(?i)sudo.*incorrect password',
            r'(?i)break.*attempt',
            r'(?i)intrusion.*detect',
            r'(?i)unauthorized.*access'
        ]
        
        for pattern in security_patterns:
            if re.search(pattern, line):
                analysis['security_events'].append(line)
                break
        
        # Speicherplatz-Warnungen
        disk_patterns = [
            r'(?i)no space left',
            r'(?i)disk.*full',
            r'(?i)filesystem.*full',
            r'(?i)out of disk space',
            r'(?i)device.*full'
        ]
        
        for pattern in disk_patterns:
            if re.search(pattern, line):
                analysis['disk_space_warnings'].append(line)
                break
        
        # Speicher-Probleme
        memory_patterns = [
            r'(?i)out of memory',
            r'(?i)oom.*kill',
            r'(?i)memory.*exhausted',
            r'(?i)cannot allocate memory',
            r'(?i)virtual memory.*exhausted'
        ]
        
        for pattern in memory_patterns:
            if re.search(pattern, line):
                analysis['memory_issues'].append(line)
                break
        
        # Netzwerk-Probleme
        network_patterns = [
            r'(?i)network.*unreachable',
            r'(?i)connection.*refused',
            r'(?i)timeout.*connecting',
            r'(?i)dns.*resolution.*failed',
            r'(?i)network.*interface.*down'
        ]
        
        for pattern in network_patterns:
            if re.search(pattern, line):
                analysis['network_issues'].append(line)
                break
        
        # Allgemeine Fehler
        if any(keyword in line_lower for keyword in ['error', 'failed', 'failure', 'exception']):
            # Ausnahmen für bekannte, unkritische Meldungen
            if not any(exclude in line_lower for exclude in ['info', 'debug', 'notice']):
                analysis['errors'].append(line)
        
        # Warnungen
        if any(keyword in line_lower for keyword in ['warning', 'warn']):
            analysis['warnings'].append(line)
    
    def generate_system_report(self, analyses: List[Dict[str, Any]], hours_back: int = 1) -> str:
        """Generiert einen System-Monitoring-Bericht"""
        report_lines = []
        report_lines.append("🤖 SYSTEM-MONITORING BERICHT")
        report_lines.append("=" * 50)
        report_lines.append(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Zeitraum: Letzten {hours_back} Stunde(n)")
        report_lines.append(f"Analysierte Dateien: {len(analyses)}")
        report_lines.append("")
        
        # Zusammenfassung der Ereignisse
        total_critical = sum(len(a['critical_events']) for a in analyses)
        total_security = sum(len(a['security_events']) for a in analyses)
        total_disk_warnings = sum(len(a['disk_space_warnings']) for a in analyses)
        total_memory_issues = sum(len(a['memory_issues']) for a in analyses)
        total_network_issues = sum(len(a['network_issues']) for a in analyses)
        total_errors = sum(len(a['errors']) for a in analyses)
        total_warnings = sum(len(a['warnings']) for a in analyses)
        
        report_lines.append("📊 EREIGNIS-ÜBERSICHT")
        report_lines.append("-" * 30)
        report_lines.append(f"🔴 Kritische Ereignisse: {total_critical}")
        report_lines.append(f"🔒 Sicherheitsereignisse: {total_security}")
        report_lines.append(f"💾 Speicherplatz-Warnungen: {total_disk_warnings}")
        report_lines.append(f"🧠 Speicher-Probleme: {total_memory_issues}")
        report_lines.append(f"🌐 Netzwerk-Probleme: {total_network_issues}")
        report_lines.append(f"❌ Allgemeine Fehler: {total_errors}")
        report_lines.append(f"⚠️ Warnungen: {total_warnings}")
        report_lines.append("")
        
        # Details der kritischsten Ereignisse
        if total_critical > 0:
            report_lines.append("🔴 KRITISCHE EREIGNISSE")
            report_lines.append("-" * 30)
            for analysis in analyses:
                for event in analysis['critical_events'][:3]:  # Max 3 pro Datei
                    report_lines.append(f"• {event}")
            report_lines.append("")
        
        if total_security > 0:
            report_lines.append("🔒 SICHERHEITSEREIGNISSE")
            report_lines.append("-" * 30)
            for analysis in analyses:
                for event in analysis['security_events'][:5]:  # Max 5 pro Datei
                    report_lines.append(f"• {event}")
            report_lines.append("")
        
        if total_disk_warnings > 0:
            report_lines.append("💾 SPEICHERPLATZ-WARNUNGEN")
            report_lines.append("-" * 30)
            for analysis in analyses:
                for warning in analysis['disk_space_warnings'][:3]:
                    report_lines.append(f"• {warning}")
            report_lines.append("")
        
        # Gesamtstatus bestimmen
        report_lines.append("📋 GESAMTSTATUS")
        report_lines.append("=" * 50)
        
        if total_critical > 0:
            report_lines.append("🔴 STATUS: KRITISCH - Sofortige Aufmerksamkeit erforderlich!")
            status = "critical"
        elif total_security > 0 or total_disk_warnings > 0 or total_memory_issues > 0:
            report_lines.append("🟡 STATUS: WARNUNG - Überwachung erforderlich")
            status = "warning"
        elif total_errors > 0:
            report_lines.append("🟠 STATUS: FEHLER - Überprüfung empfohlen")
            status = "error"
        elif total_warnings > 0:
            report_lines.append("🟡 STATUS: WARNUNGEN - Informationszwecke")
            status = "info"
        else:
            report_lines.append("🟢 STATUS: OK - Keine kritischen Ereignisse")
            status = "success"
        
        return "\n".join(report_lines), status
    
    def run_monitoring(self, hours_back: int = 1) -> bool:
        """Führt das System-Monitoring durch"""
        try:
            self.logger.info(f"🤖 Starte System-Monitoring (letzte {hours_back} Stunde(n))...")
            
            # Log-Dateien finden
            log_files = self.find_system_logs()
            
            if not log_files:
                message = "Keine System-Log-Dateien gefunden!"
                self.logger.warning(message)
                return True  # Nicht kritisch, wenn keine System-Logs vorhanden
            
            # Log-Dateien analysieren
            analyses = []
            for log_file in log_files[:5]:  # Maximal 5 Dateien
                analysis = self.analyze_system_log(log_file, hours_back)
                analyses.append(analysis)
            
            # Bericht generieren
            report, status = self.generate_system_report(analyses, hours_back)
            self.logger.info(f"System-Monitoring-Bericht generiert (Status: {status})")
            
            # E-Mail senden basierend auf Status
            if status == "critical":
                self.email_sender.send_email(
                    subject="System-Monitoring: KRITISCHE EREIGNISSE",
                    body=report,
                    email_type="error"
                )
            elif status in ["warning", "error"]:
                self.email_sender.send_email(
                    subject=f"System-Monitoring: {status.upper()}",
                    body=report,
                    email_type="warning"
                )
            # Bei "success" oder "info" keine E-Mail senden (zu häufig)
            
            self.logger.info("✅ System-Monitoring abgeschlossen")
            return True
            
        except Exception as e:
            error_msg = f"Kritischer Fehler im System-Monitoring: {e}"
            self.logger.error(error_msg)
            self.email_sender.send_error_notification("system_monitor.py", error_msg)
            return False


def main():
    """Hauptfunktion des System-Monitors"""
    import sys
    
    # Parameter für Zeitraum (Standard: 1 Stunde)
    hours_back = 1
    if len(sys.argv) > 1:
        try:
            hours_back = int(sys.argv[1])
        except ValueError:
            print("Ungültiger Parameter für Stunden. Verwende Standard: 1")
    
    monitor = SystemMonitor()
    success = monitor.run_monitoring(hours_back)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()