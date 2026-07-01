import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

class NotificationService:
    """Handle SMS and Email notifications"""
    
    def __init__(self):
        self.alerts_file = os.path.join('local_storage', 'alerts.json')
        
        # Email configuration (can be set in .env)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.alert_email = os.getenv('ALERT_EMAIL', 'harshamg41@gmail.com')
        
        # Twilio configuration for SMS (optional)
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '')
        self.mobile_number = os.getenv('MOBILE_NUMBER', '')
    
    def send_email_alert(self, subject: str, message: str):
        """Send email alert"""
        try:
            if not self.smtp_username or not self.smtp_password:
                print("Email credentials not configured. Skipping email alert.")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            msg['Subject'] = f"[AWS Log Analyzer Alert] {subject}"
            
            body = f"""
            <html>
            <body>
                <h2>{subject}</h2>
                <p>{message}</p>
                <hr>
                <p><small>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                <p><small>This is an automated alert from AWS Cloud Log Analyzer</small></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            print(f"Email alert sent to {self.alert_email}")
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def send_sms_alert(self, message: str):
        """Send SMS alert using Twilio"""
        try:
            if not self.twilio_account_sid or not self.twilio_auth_token:
                print("Twilio credentials not configured. Skipping SMS alert.")
                return False
            
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=self.mobile_number
            )
            
            print(f"SMS alert sent to {self.mobile_number}")
            return True
        except ImportError:
            print("Twilio library not installed. Install with: pip install twilio")
            return False
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
            return False
    
    def create_alert(self, level: str, message: str, source: str = 'local'):
        """Create an alert record and send notifications"""
        alert = {
            'alert_id': f"alert_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'source': source,
            'sent_email': False,
            'sent_sms': False
        }
        
        # Save alert to file
        alerts = self._load_alerts()
        alerts.insert(0, alert)  # Add to beginning
        self._save_alerts(alerts)
        
        # Send notifications for critical errors
        if level == 'CRITICAL':
            # Send email
            if self.send_email_alert(f"CRITICAL: {message}", f"A critical error has been detected:\n\n{message}"):
                alert['sent_email'] = True
            
            # Send SMS
            if self.send_sms_alert(f"[CRITICAL] {message}"):
                alert['sent_sms'] = True
            
            # Update alert with notification status
            alerts[0] = alert
            self._save_alerts(alerts)
        
        return alert
    
    def _load_alerts(self):
        """Load alerts from file"""
        try:
            with open(self.alerts_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _save_alerts(self, alerts):
        """Save alerts to file"""
        with open(self.alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)
