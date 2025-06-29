#!/usr/bin/env python3
"""
E-Mail-Utility für SMTP-Versand
Zentrale Klasse für den Versand von E-Mail-Benachrichtigungen
"""

import smtplib
import ssl
import yaml
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional, Dict, Any

class EmailSender:
    """
    Zentrale Klasse für E-Mail-Versand mit SMTP
    """
    
    def __init__(self, config_path: str = "/app/config/config.yaml"):
        """
        Initialisiert den EmailSender mit Konfiguration
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.smtp_config = self.config.get('smtp', {})
        self.logger = self._setup_logging()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Lädt die YAML-Konfigurationsdatei
        
        Returns:
            Konfigurationsdictionary
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
        
        Returns:
            Logger-Instanz
        """
        logger = logging.getLogger('EmailSender')
        
        if not logger.handlers:
            log_config = self.config.get('logging', {})
            log_level = getattr(logging, log_config.get('level', 'INFO'))
            
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(log_level)
        
        return logger
    
    def send_email(self, 
                   subject: str, 
                   body: str, 
                   recipients: Optional[List[str]] = None,
                   email_type: str = "info",
                   attachments: Optional[List[str]] = None) -> bool:
        """
        Sendet eine E-Mail
        
        Args:
            subject: E-Mail-Betreff
            body: E-Mail-Inhalt (Text oder HTML)
            recipients: Liste der Empfänger (optional, verwendet Standard-Empfänger)
            email_type: Typ der E-Mail (error, warning, success, info)
            attachments: Liste der Anhänge (Dateipfade)
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Empfänger bestimmen
            if recipients is None:
                recipients = self.smtp_config.get('default_recipients', [])
            
            if not recipients:
                self.logger.error("Keine E-Mail-Empfänger definiert")
                return False
            
            # E-Mail erstellen
            msg = self._create_message(subject, body, recipients, email_type, attachments)
            
            # E-Mail versenden
            return self._send_message(msg, recipients)
            
        except Exception as e:
            self.logger.error(f"Fehler beim E-Mail-Versand: {e}")
            return False
    
    def _create_message(self, 
                       subject: str, 
                       body: str, 
                       recipients: List[str],
                       email_type: str,
                       attachments: Optional[List[str]] = None) -> MIMEMultipart:
        """
        Erstellt die E-Mail-Nachricht
        
        Args:
            subject: E-Mail-Betreff
            body: E-Mail-Inhalt
            recipients: Liste der Empfänger
            email_type: Typ der E-Mail
            attachments: Liste der Anhänge
            
        Returns:
            MIMEMultipart-Nachricht
        """
        msg = MIMEMultipart()
        
        # Header setzen
        msg['From'] = f"{self.smtp_config.get('from_name', 'Log Checker')} <{self.smtp_config.get('from_email', '')}>"
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = self._format_subject(subject, email_type)
        
        # Body hinzufügen
        formatted_body = self._format_body(body, email_type)
        msg.attach(MIMEText(formatted_body, 'html'))
        
        # Anhänge hinzufügen
        if attachments:
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    self._add_attachment(msg, attachment_path)
                else:
                    self.logger.warning(f"Anhang nicht gefunden: {attachment_path}")
        
        return msg
    
    def _format_subject(self, subject: str, email_type: str) -> str:
        """
        Formatiert den E-Mail-Betreff basierend auf dem Typ
        
        Args:
            subject: Ursprünglicher Betreff
            email_type: Typ der E-Mail
            
        Returns:
            Formatierter Betreff
        """
        templates = self.smtp_config.get('templates', {})
        hostname = self.config.get('system', {}).get('hostname', 'unknown')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        template_key = f"{email_type}_subject"
        template = templates.get(template_key, "[{email_type.upper()}] {hostname} - {subject} - {timestamp}")
        
        return template.format(
            hostname=hostname,
            subject=subject,
            timestamp=timestamp,
            email_type=email_type.upper()
        )
    
    def _format_body(self, body: str, email_type: str) -> str:
        """
        Formatiert den E-Mail-Body mit HTML
        
        Args:
            body: Ursprünglicher Body
            email_type: Typ der E-Mail
            
        Returns:
            HTML-formatierter Body
        """
        color_map = {
            'error': '#dc3545',
            'warning': '#ffc107', 
            'success': '#28a745',
            'info': '#17a2b8'
        }
        
        color = color_map.get(email_type, '#6c757d')
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: {color}; color: white; padding: 10px; }}
                .content {{ padding: 20px; }}
                .footer {{ font-size: 12px; color: #666; margin-top: 20px; }}
                pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🤖 Log Checker Benachrichtigung</h2>
            </div>
            <div class="content">
                <pre>{body}</pre>
            </div>
            <div class="footer">
                <p>Gesendet von: {self.config.get('system', {}).get('hostname', 'Log Checker System')}</p>
                <p>Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """
        Fügt einen Anhang zur E-Mail hinzu
        
        Args:
            msg: E-Mail-Nachricht
            file_path: Pfad zur Anhang-Datei
        """
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            
            msg.attach(part)
            self.logger.info(f"Anhang hinzugefügt: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen des Anhangs {file_path}: {e}")
    
    def _send_message(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """
        Versendet die E-Mail-Nachricht über SMTP
        
        Args:
            msg: E-Mail-Nachricht
            recipients: Liste der Empfänger
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            server = self.smtp_config.get('server')
            port = self.smtp_config.get('port', 587)
            username = self.smtp_config.get('username')
            password = self.smtp_config.get('password')
            use_tls = self.smtp_config.get('use_tls', True)
            use_ssl = self.smtp_config.get('use_ssl', False)
            
            if not all([server, username, password]):
                self.logger.error("SMTP-Konfiguration unvollständig")
                return False
            
            # SMTP-Verbindung aufbauen
            if use_ssl:
                context = ssl.create_default_context()
                smtp_server = smtplib.SMTP_SSL(server, port, context=context)
            else:
                smtp_server = smtplib.SMTP(server, port)
                if use_tls:
                    context = ssl.create_default_context()
                    smtp_server.starttls(context=context)
            
            # Anmelden und senden
            smtp_server.login(username, password)
            text = msg.as_string()
            smtp_server.sendmail(username, recipients, text)
            smtp_server.quit()
            
            self.logger.info(f"E-Mail erfolgreich gesendet an: {', '.join(recipients)}")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP-Fehler: {e}")
            return False
    
    def send_error_notification(self, script_name: str, error_message: str, log_content: str = "") -> bool:
        """
        Sendet eine Fehler-Benachrichtigung
        
        Args:
            script_name: Name des fehlerhaften Scripts
            error_message: Fehlermeldung
            log_content: Log-Inhalt (optional)
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        subject = f"Script-Fehler: {script_name}"
        body = f"Fehler in Script '{script_name}':\n\n{error_message}"
        
        if log_content:
            body += f"\n\nLog-Ausgabe:\n{log_content}"
        
        return self.send_email(subject, body, email_type="error")
    
    def send_success_notification(self, script_name: str, message: str) -> bool:
        """
        Sendet eine Erfolgs-Benachrichtigung
        
        Args:
            script_name: Name des Scripts
            message: Erfolgsmeldung
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        subject = f"Script erfolgreich: {script_name}"
        body = f"Script '{script_name}' erfolgreich ausgeführt:\n\n{message}"
        
        return self.send_email(subject, body, email_type="success")
    
    def test_connection(self) -> bool:
        """
        Testet die SMTP-Verbindung
        
        Returns:
            True bei erfolgreicher Verbindung, False bei Fehler
        """
        try:
            subject = "Test-E-Mail von Log Checker"
            body = "Dies ist eine Test-E-Mail zur Überprüfung der SMTP-Konfiguration."
            
            return self.send_email(subject, body, email_type="info")
            
        except Exception as e:
            self.logger.error(f"Test-Verbindung fehlgeschlagen: {e}")
            return False


# CLI-Interface für Tests
if __name__ == "__main__":
    import sys
    
    sender = EmailSender()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🤖 Teste E-Mail-Verbindung...")
        if sender.test_connection():
            print("✅ Test-E-Mail erfolgreich gesendet!")
        else:
            print("❌ Test-E-Mail fehlgeschlagen!")
    else:
        print("Verwendung: python email_utils.py test")