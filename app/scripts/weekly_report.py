#!/usr/bin/env python3
"""
Weekly Report Script
Erstellt einen wöchentlichen Zusammenfassungsbericht
"""

import os
import glob
import yaml
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from email_utils import EmailSender

class WeeklyReporter:
    """
    Klasse für wöchentliche Berichte
    """
    
    def __init__(self, config_path: str = "/app/config/config.yaml"):
        """
        Initialisiert den WeeklyReporter
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.email_sender = EmailSender(config_path)
        
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
        logger = logging.getLogger('WeeklyReporter')
        
        if not logger.handlers:
            log_config = self.config.get('logging', {})
            log_level = getattr(logging, log_config.get('level', 'INFO'))
            
            log_file = '/app/logs/weekly_report.log'
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
    
    def analyze_weekly_logs(self) -> Dict[str, Any]:
        """
        Analysiert die Logs der letzten Woche
        """
        analysis = {
            'period': {
                'start': datetime.now() - timedelta(days=7),
                'end': datetime.now()
            },
            'log_files_analyzed': 0,
            'total_log_entries': 0,
            'backup_statistics': {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'warnings': 0
            },
            'system_statistics': {
                'critical_events': 0,
                'security_events': 0,
                'disk_warnings': 0,
                'memory_issues': 0,
                'network_issues': 0
            },
            'error_summary': [],
            'performance_metrics': {
                'avg_backup_duration': None,
                'total_data_transferred': 0,
                'largest_backup': None
            }
        }
        
        try:
            # Analysiere Application Logs
            self._analyze_application_logs(analysis)
            
            # Analysiere Backup Logs
            self._analyze_backup_logs(analysis)
            
            # Analysiere System Logs (falls vorhanden)
            self._analyze_system_logs(analysis)
            
        except Exception as e:
            self.logger.error(f"Fehler bei der wöchentlichen Analyse: {e}")
        
        return analysis
    
    def _analyze_application_logs(self, analysis: Dict[str, Any]):
        """Analysiert die Application-Log-Dateien"""
        log_dir = "/app/logs"
        
        if not os.path.exists(log_dir):
            return
        
        week_ago = datetime.now() - timedelta(days=7)
        
        for log_file in glob.glob(os.path.join(log_dir, "*.log")):
            try:
                # Prüfe Datei-Alter
                file_stat = os.stat(log_file)
                if datetime.fromtimestamp(file_stat.st_mtime) < week_ago:
                    continue
                
                analysis['log_files_analyzed'] += 1
                
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if line.strip():
                            analysis['total_log_entries'] += 1
                            
                            # Suche nach spezifischen Patterns
                            line_lower = line.lower()
                            
                            if 'backup' in line_lower:
                                if 'successful' in line_lower or 'completed' in line_lower:
                                    analysis['backup_statistics']['successful_runs'] += 1
                                elif 'error' in line_lower or 'failed' in line_lower:
                                    analysis['backup_statistics']['failed_runs'] += 1
                                    analysis['error_summary'].append(line.strip())
                                elif 'warning' in line_lower:
                                    analysis['backup_statistics']['warnings'] += 1
                                
                                analysis['backup_statistics']['total_runs'] += 1
                            
            except Exception as e:
                self.logger.warning(f"Fehler beim Analysieren von {log_file}: {e}")
    
    def _analyze_backup_logs(self, analysis: Dict[str, Any]):
        """Analysiert die Backup-Log-Dateien"""
        backup_log_path = self.config.get('paths', {}).get('backup_logs', '/app/data/backup')
        
        if not os.path.exists(backup_log_path):
            return
        
        week_ago = datetime.now() - timedelta(days=7)
        durations = []
        
        for log_file in glob.glob(os.path.join(backup_log_path, "backup_*.log")):
            try:
                file_stat = os.stat(log_file)
                if datetime.fromtimestamp(file_stat.st_mtime) < week_ago:
                    continue
                
                file_size_mb = file_stat.st_size / (1024 * 1024)
                
                # Größtes Backup tracken
                if (analysis['performance_metrics']['largest_backup'] is None or 
                    file_size_mb > analysis['performance_metrics']['largest_backup']):
                    analysis['performance_metrics']['largest_backup'] = file_size_mb
                
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Suche nach Dauer-Informationen
                    import re
                    duration_match = re.search(r'duration:?\s*(\d+):(\d+):(\d+)', content.lower())
                    if duration_match:
                        hours = int(duration_match.group(1))
                        minutes = int(duration_match.group(2))
                        seconds = int(duration_match.group(3))
                        total_minutes = hours * 60 + minutes + seconds / 60
                        durations.append(total_minutes)
                    
                    # Suche nach übertragenen Daten
                    data_match = re.search(r'transferred:?\s*(\d+(?:\.\d+)?)\s*(gb|mb|tb)', content.lower())
                    if data_match:
                        amount = float(data_match.group(1))
                        unit = data_match.group(2)
                        
                        # Konvertiere zu MB
                        if unit == 'gb':
                            amount *= 1024
                        elif unit == 'tb':
                            amount *= 1024 * 1024
                        
                        analysis['performance_metrics']['total_data_transferred'] += amount
                
            except Exception as e:
                self.logger.warning(f"Fehler beim Analysieren von {log_file}: {e}")
        
        # Durchschnittliche Dauer berechnen
        if durations:
            analysis['performance_metrics']['avg_backup_duration'] = sum(durations) / len(durations)
    
    def _analyze_system_logs(self, analysis: Dict[str, Any]):
        """Analysiert die System-Log-Dateien"""
        system_log_path = self.config.get('paths', {}).get('system_logs', '/app/data/system')
        
        if not os.path.exists(system_log_path):
            return
        
        week_ago = datetime.now() - timedelta(days=7)
        
        for log_file in glob.glob(os.path.join(system_log_path, "*")):
            try:
                file_stat = os.stat(log_file)
                if datetime.fromtimestamp(file_stat.st_mtime) < week_ago:
                    continue
                
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line_lower = line.lower()
                        
                        if any(keyword in line_lower for keyword in ['critical', 'emergency', 'panic']):
                            analysis['system_statistics']['critical_events'] += 1
                        
                        if any(keyword in line_lower for keyword in ['authentication failure', 'failed login', 'invalid user']):
                            analysis['system_statistics']['security_events'] += 1
                        
                        if any(keyword in line_lower for keyword in ['no space left', 'disk full']):
                            analysis['system_statistics']['disk_warnings'] += 1
                        
                        if any(keyword in line_lower for keyword in ['out of memory', 'oom kill']):
                            analysis['system_statistics']['memory_issues'] += 1
                        
                        if any(keyword in line_lower for keyword in ['network unreachable', 'connection refused']):
                            analysis['system_statistics']['network_issues'] += 1
                            
            except Exception as e:
                self.logger.warning(f"Fehler beim Analysieren von {log_file}: {e}")
    
    def generate_weekly_report(self, analysis: Dict[str, Any]) -> str:
        """Generiert den wöchentlichen Bericht"""
        report_lines = []
        
        # Header
        report_lines.append("🤖 WÖCHENTLICHER MONITORING-BERICHT")
        report_lines.append("=" * 60)
        
        period_start = analysis['period']['start'].strftime('%Y-%m-%d')
        period_end = analysis['period']['end'].strftime('%Y-%m-%d')
        report_lines.append(f"Berichtszeitraum: {period_start} bis {period_end}")
        report_lines.append(f"Generiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Übersicht der analysierten Daten
        report_lines.append("📊 DATENÜBERSICHT")
        report_lines.append("-" * 40)
        report_lines.append(f"Analysierte Log-Dateien: {analysis['log_files_analyzed']}")
        report_lines.append(f"Gesamte Log-Einträge: {analysis['total_log_entries']:,}")
        report_lines.append("")
        
        # Backup-Statistiken
        backup_stats = analysis['backup_statistics']
        report_lines.append("💾 BACKUP-STATISTIKEN")
        report_lines.append("-" * 40)
        report_lines.append(f"Gesamte Backup-Läufe: {backup_stats['total_runs']}")
        report_lines.append(f"Erfolgreiche Backups: {backup_stats['successful_runs']}")
        report_lines.append(f"Fehlgeschlagene Backups: {backup_stats['failed_runs']}")
        report_lines.append(f"Warnungen: {backup_stats['warnings']}")
        
        if backup_stats['total_runs'] > 0:
            success_rate = (backup_stats['successful_runs'] / backup_stats['total_runs']) * 100
            report_lines.append(f"Erfolgsrate: {success_rate:.1f}%")
        
        report_lines.append("")
        
        # Performance-Metriken
        perf_metrics = analysis['performance_metrics']
        report_lines.append("⚡ PERFORMANCE-METRIKEN")
        report_lines.append("-" * 40)
        
        if perf_metrics['avg_backup_duration']:
            avg_duration = perf_metrics['avg_backup_duration']
            hours = int(avg_duration // 60)
            minutes = int(avg_duration % 60)
            report_lines.append(f"Durchschnittliche Backup-Dauer: {hours:02d}:{minutes:02d}")
        
        if perf_metrics['total_data_transferred'] > 0:
            total_gb = perf_metrics['total_data_transferred'] / 1024
            report_lines.append(f"Gesamt übertragene Daten: {total_gb:.2f} GB")
        
        if perf_metrics['largest_backup']:
            report_lines.append(f"Größtes Backup-Log: {perf_metrics['largest_backup']:.1f} MB")
        
        report_lines.append("")
        
        # System-Statistiken
        sys_stats = analysis['system_statistics']
        total_system_events = sum(sys_stats.values())
        
        if total_system_events > 0:
            report_lines.append("🖥️ SYSTEM-EREIGNISSE")
            report_lines.append("-" * 40)
            report_lines.append(f"Kritische Ereignisse: {sys_stats['critical_events']}")
            report_lines.append(f"Sicherheitsereignisse: {sys_stats['security_events']}")
            report_lines.append(f"Speicherplatz-Warnungen: {sys_stats['disk_warnings']}")
            report_lines.append(f"Speicher-Probleme: {sys_stats['memory_issues']}")
            report_lines.append(f"Netzwerk-Probleme: {sys_stats['network_issues']}")
            report_lines.append("")
        
        # Fehler-Zusammenfassung
        if analysis['error_summary']:
            report_lines.append("❌ WICHTIGSTE FEHLER (letzte 10)")
            report_lines.append("-" * 40)
            for error in analysis['error_summary'][-10:]:  # Letzte 10 Fehler
                report_lines.append(f"• {error}")
            report_lines.append("")
        
        # Empfehlungen
        report_lines.append("💡 EMPFEHLUNGEN")
        report_lines.append("-" * 40)
        recommendations = []
        
        if backup_stats['failed_runs'] > 0:
            fail_rate = (backup_stats['failed_runs'] / backup_stats['total_runs']) * 100
            if fail_rate > 10:
                recommendations.append(f"Hohe Fehlerrate bei Backups ({fail_rate:.1f}%) - Konfiguration prüfen")
        
        if sys_stats['critical_events'] > 0:
            recommendations.append("Kritische Systemereignisse gefunden - Sofortige Überprüfung erforderlich")
        
        if sys_stats['security_events'] > 5:
            recommendations.append("Mehrere Sicherheitsereignisse - Sicherheitsrichtlinien überprüfen")
        
        if sys_stats['disk_warnings'] > 0:
            recommendations.append("Speicherplatz-Warnungen - Disk Cleanup empfohlen")
        
        if perf_metrics['avg_backup_duration'] and perf_metrics['avg_backup_duration'] > 180:  # > 3 Stunden
            recommendations.append("Lange Backup-Zeiten - Optimierung der Backup-Strategie prüfen")
        
        if not recommendations:
            recommendations.append("✅ Keine besonderen Maßnahmen erforderlich - System läuft stabil")
        
        for rec in recommendations:
            report_lines.append(f"• {rec}")
        
        report_lines.append("")
        
        # Gesamtbewertung
        report_lines.append("📋 GESAMTBEWERTUNG")
        report_lines.append("=" * 60)
        
        if (backup_stats['failed_runs'] == 0 and 
            sys_stats['critical_events'] == 0 and 
            sys_stats['security_events'] < 3):
            report_lines.append("🟢 AUSGEZEICHNET - System läuft optimal")
        elif (backup_stats['failed_runs'] < 2 and 
              sys_stats['critical_events'] == 0):
            report_lines.append("🟡 GUT - Kleinere Probleme, aber stabil")
        elif sys_stats['critical_events'] > 0:
            report_lines.append("🔴 KRITISCH - Sofortige Aufmerksamkeit erforderlich")
        else:
            report_lines.append("🟠 VERBESSERUNGSBEDARF - Überwachung verstärken")
        
        return "\n".join(report_lines)
    
    def run_weekly_report(self) -> bool:
        """Führt die wöchentliche Berichtserstellung durch"""
        try:
            self.logger.info("🤖 Starte wöchentliche Berichtserstellung...")
            
            # Daten der letzten Woche analysieren
            analysis = self.analyze_weekly_logs()
            
            # Bericht generieren
            report = self.generate_weekly_report(analysis)
            
            # Bericht speichern
            report_file = f"/app/logs/weekly_report_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"Wöchentlicher Bericht gespeichert: {report_file}")
            
            # E-Mail versenden
            self.email_sender.send_email(
                subject="Wöchentlicher Monitoring-Bericht",
                body=report,
                email_type="info"
            )
            
            self.logger.info("✅ Wöchentlicher Bericht erfolgreich erstellt und versendet")
            return True
            
        except Exception as e:
            error_msg = f"Fehler bei der wöchentlichen Berichtserstellung: {e}"
            self.logger.error(error_msg)
            self.email_sender.send_error_notification("weekly_report.py", error_msg)
            return False


def main():
    """Hauptfunktion des Weekly-Reporters"""
    reporter = WeeklyReporter()
    success = reporter.run_weekly_report()
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()