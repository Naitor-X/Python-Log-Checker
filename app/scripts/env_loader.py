import os
from typing import Dict, Any, List
import yaml

class EnvLoader:
    """Lädt Umgebungsvariablen und stellt sie als Konfiguration zur Verfügung"""
    
    @staticmethod
    def load_smtp_config() -> Dict[str, Any]:
        """Lädt SMTP-Konfiguration aus Umgebungsvariablen"""
        return {
            'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            'use_ssl': os.getenv('SMTP_USE_SSL', 'false').lower() == 'true',
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('SMTP_FROM_EMAIL', ''),
            'from_name': os.getenv('SMTP_FROM_NAME', 'Log Checker System'),
            'default_recipients': os.getenv('SMTP_DEFAULT_RECIPIENTS', '').split(',') if os.getenv('SMTP_DEFAULT_RECIPIENTS') else [],
            'templates': {
                'error_subject': "[FEHLER] {hostname} - {script_name} - {timestamp}",
                'warning_subject': "[WARNUNG] {hostname} - {script_name} - {timestamp}",
                'success_subject': "[OK] {hostname} - {script_name} - {timestamp}"
            }
        }
    
    @staticmethod
    def load_system_config() -> Dict[str, Any]:
        """Lädt System-Konfiguration aus Umgebungsvariablen"""
        return {
            'hostname': os.getenv('SYSTEM_HOSTNAME', ''),
            'environment': os.getenv('SYSTEM_ENVIRONMENT', 'production'),
            'timezone': os.getenv('SYSTEM_TIMEZONE', 'Europe/Berlin')
        }
    
    @staticmethod
    def load_logging_config() -> Dict[str, Any]:
        """Lädt Logging-Konfiguration aus Umgebungsvariablen"""
        return {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file': '/app/logs/log_checker.log',
            'max_size_mb': int(os.getenv('LOG_MAX_SIZE_MB', '10')),
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S'
        }
    
    @staticmethod
    def load_monitoring_config() -> Dict[str, Any]:
        """Lädt Monitoring-Konfiguration aus Umgebungsvariablen"""
        return {
            'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
            'script_timeout': int(os.getenv('SCRIPT_TIMEOUT', '300')),
            'max_concurrent_scripts': int(os.getenv('MAX_CONCURRENT_SCRIPTS', '3')),
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'retry_delay': int(os.getenv('RETRY_DELAY', '60'))
        }
    
    @staticmethod
    def load_backup_check_config() -> Dict[str, Any]:
        """Lädt erweiterte Backup-Check-Konfiguration aus Umgebungsvariablen"""
        return {
            'server_name': os.getenv('BACKUP_CHECK_SERVER_NAME', 'Docker-Container'),
            'log_directory': '/app/data/logs',
            'output_directory': '/app/logs/logcheck',
            'logfilelist_path': '/app/config/logfilelist.txt',
            'keywords_path': '/app/config/keywords.txt',
            'days_to_check': int(os.getenv('BACKUP_CHECK_DAYS', '1')),
            'start_day_offset': int(os.getenv('BACKUP_CHECK_START_DAY_OFFSET', '0')),
            'email_subject_prefix': 'Backup-Check',
            'required_log_files': [
                'Administration.log',
                'Nevaris.log',
                'Share_MSSQL.log'
            ],
            'error_keywords': [
                'denied', 'Denied', 'Warn', 'warn', 'Warning',
                'fail', 'Fail', 'error', 'Error', 'ERROR',
                'critical', 'Critical', 'CRITICAL'
            ]
        }
    
    @staticmethod
    def load_full_config() -> Dict[str, Any]:
        """Lädt vollständige Konfiguration aus Umgebungsvariablen"""
        return {
            'smtp': EnvLoader.load_smtp_config(),
            'system': EnvLoader.load_system_config(),
            'logging': EnvLoader.load_logging_config(),
            'monitoring': EnvLoader.load_monitoring_config(),
            'advanced_backup_check': EnvLoader.load_backup_check_config(),
            'paths': {
                'backup_logs': '/app/data/backup',
                'system_logs': '/app/data/system',
                'scripts_dir': '/app/scripts',
                'logs_dir': '/app/logs',
                'temp_dir': '/tmp',
                'log_patterns': {
                    'backup': 'backup_*.log',
                    'system': 'syslog*',
                    'error': 'error*.log'
                }
            },
            'security': {
                'allowed_script_paths': ['/app/scripts'],
                'max_log_file_size': 100,
                'allowed_script_extensions': ['.py']
            }
        }