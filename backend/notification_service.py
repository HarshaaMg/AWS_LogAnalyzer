import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
import json
from typing import Optional, Dict, Any


class NotificationService:
    """Handles SMS, Email, and structured Auto-Scaling notifications."""

    def __init__(self):
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        self.alerts_file = os.path.join(backend_dir, 'local_storage', 'alerts.json')

        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.alert_email = os.getenv('ALERT_EMAIL', 'harshamg41@gmail.com')

        # Twilio configuration for SMS
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '')
        self.mobile_number = os.getenv('MOBILE_NUMBER', '')

    def send_email_alert(self, subject: str, message: str) -> bool:
        """Send email alert"""
        try:
            if not self.smtp_username or not self.smtp_password:
                return False

            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            msg['Subject'] = f"[AWS Log Analyzer & Auto-Scaler] {subject}"

            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d9534f;">{subject}</h2>
                <pre style="background: #f4f4f4; padding: 12px; border-radius: 4px;">{message}</pre>
                <hr>
                <p><small>Generated at: {datetime.now(timezone.utc).isoformat()}</small></p>
                <p><small>Automated notification from Real-Time Linux Observability & Scaling Platform</small></p>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_sms_alert(self, message: str) -> bool:
        """Send SMS alert using Twilio"""
        try:
            if not self.twilio_account_sid or not self.twilio_auth_token:
                return False

            from twilio.rest import Client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=self.mobile_number
            )
            return True
        except Exception as e:
            return False

    def create_structured_alert(
        self,
        alert_type: str,
        host: str,
        value: float,
        threshold: float,
        duration: str = "5m",
        severity: str = "CRITICAL",
        action: str = "SCALE_UP"
    ) -> Dict[str, Any]:
        """
        Creates an advanced structured scaling alert:
        RESOURCE_HIGH_CPU, RESOURCE_HIGH_MEMORY, RESOURCE_HIGH_DISK,
        VM_PROVISIONING_STARTED, VM_UNHEALTHY, etc.
        """
        msg = f"[{alert_type}] Host: {host} | Value: {value} | Threshold: {threshold} ({duration}) | Action: {action}"
        alert = {
            'alert_id': f"alert_{datetime.now(timezone.utc).timestamp()}",
            'alert_type': alert_type,
            'host': host,
            'value': value,
            'threshold': threshold,
            'duration': duration,
            'severity': severity,
            'level': severity,
            'action': action,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': msg,
            'source': 'auto_scaler',
            'sent_email': False,
            'sent_sms': False
        }

        alerts = self._load_alerts()
        alerts.insert(0, alert)
        self._save_alerts(alerts)

        if severity == 'CRITICAL':
            if self.send_email_alert(f"CRITICAL: {alert_type} on {host}", msg):
                alert['sent_email'] = True
            if self.send_sms_alert(f"[ALERT] {alert_type}: {host} ({value} >= {threshold})"):
                alert['sent_sms'] = True
            alerts[0] = alert
            self._save_alerts(alerts)

        return alert

    def create_alert(self, level: str, message: str, source: str = 'local') -> Dict[str, Any]:
        """Backward-compatible create_alert method."""
        alert = {
            'alert_id': f"alert_{datetime.now(timezone.utc).timestamp()}",
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'severity': level,
            'message': message,
            'source': source,
            'sent_email': False,
            'sent_sms': False
        }

        alerts = self._load_alerts()
        alerts.insert(0, alert)
        self._save_alerts(alerts)

        if level == 'CRITICAL':
            if self.send_email_alert(f"CRITICAL: {message[:60]}", message):
                alert['sent_email'] = True
            if self.send_sms_alert(f"[CRITICAL] {message[:120]}"):
                alert['sent_sms'] = True
            alerts[0] = alert
            self._save_alerts(alerts)

        return alert

    def _load_alerts(self):
        try:
            if not os.path.exists(self.alerts_file):
                return []
            with open(self.alerts_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_alerts(self, alerts):
        try:
            os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
            with open(self.alerts_file, 'w') as f:
                json.dump(alerts[:200], f, indent=2)
        except Exception as e:
            print(f"Error saving alerts: {e}")
