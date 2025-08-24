import base64
import re
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google_auth import GoogleAuthenticator
from config import Config

class GmailProcessor:
    def __init__(self):
        self.auth = GoogleAuthenticator()
        self.service = None
    
    def initialize(self):
        """Initialize Gmail service"""
        self.service = self.auth.authenticate_gmail()
    
    def get_recent_emails(self, max_results: int = 50) -> List[Dict]:
        """Get recent emails from inbox"""
        if not self.service:
            self.initialize()
        
        try:
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                # Get full message details
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()
                
                email_data = self._parse_email(message)
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"Error getting emails: {e}")
            return []
    
    def _parse_email(self, message: Dict) -> Optional[Dict]:
        """Parse Gmail message into structured data"""
        try:
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract email body
            body = self._extract_body(message['payload'])
            
            return {
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'thread_id': message['threadId']
            }
            
        except Exception as e:
            print(f"Error parsing email: {e}")
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def identify_response_required_emails(self, emails: List[Dict]) -> List[Dict]:
        """Identify emails that require responses about pending documents"""
        response_required = []
        
        for email in emails:
            # Check subject and body for response keywords
            text_to_check = f"{email['subject']} {email['body']}".lower()
            
            for keyword in Config.RESPONSE_KEYWORDS:
                if keyword.lower() in text_to_check:
                    email['matched_keyword'] = keyword
                    response_required.append(email)
                    break
        
        return response_required
    
    def send_email(self, to_email: str, subject: str, body: str, attachment_path: Optional[str] = None) -> bool:
        """Send an email with optional attachment"""
        if not self.service:
            self.initialize()
        
        try:
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachment if provided
            if attachment_path:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment_path.split("/")[-1]}'
                    )
                    message.attach(part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"Email sent successfully. Message ID: {send_message['id']}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def extract_sender_email(self, sender: str) -> str:
        """Extract email address from sender field"""
        # Use regex to extract email from "Name <email@domain.com>" format
        match = re.search(r'<(.+?)>', sender)
        if match:
            return match.group(1)
        return sender
