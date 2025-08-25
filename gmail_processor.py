import base64
import re
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import openai
from google_auth import GoogleAuthenticator
from config import Config

class GmailProcessor:
    def __init__(self):
        self.auth = GoogleAuthenticator()
        self.service = None
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def initialize(self):
        """Initialize Gmail service"""
        self.service = self.auth.authenticate_gmail()
    
    def get_recent_emails(self, days_back: int = 7, max_results: int = 100) -> List[Dict]:
        """Get recent emails from inbox within the specified number of days"""
        if not self.service:
            self.initialize()
        
        try:
            # Calculate date range (last N days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for Gmail API query
            start_date_str = start_date.strftime('%Y/%m/%d')
            end_date_str = end_date.strftime('%Y/%m/%d')
            
            # Gmail query to get emails from last 7 days
            query = f'in:inbox after:{start_date_str} before:{end_date_str}'
            
            print(f"📅 Searching for emails from {start_date_str} to {end_date_str}")
            
            # Get list of messages with date filter
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            print(f"📧 Found {len(messages)} emails in date range")
            
            for msg in messages:
                # Get full message details
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
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
        """Extract email body from payload, handling both plain text and HTML"""
        body = ""
        
        def extract_from_part(part):
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            elif part['mimeType'] == 'text/html':
                data = part['body'].get('data')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                    # Basic HTML to text conversion
                    import re
                    # Remove HTML tags
                    clean_text = re.sub(r'<[^>]+>', ' ', html_content)
                    # Clean up whitespace
                    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                    return clean_text
            return ""
        
        if 'parts' in payload:
            # Handle multipart messages
            for part in payload['parts']:
                if 'parts' in part:  # Nested parts
                    for subpart in part['parts']:
                        extracted = extract_from_part(subpart)
                        if extracted and not body:  # Prefer plain text
                            body = extracted
                else:
                    extracted = extract_from_part(part)
                    if extracted and not body:  # Prefer plain text
                        body = extracted
        else:
            # Handle single part message
            body = extract_from_part(payload)
        
        return body
    
    def identify_response_required_emails(self, emails: List[Dict]) -> List[Dict]:
        """Intelligently identify emails that require responses about pending documents"""
        response_required = []
        
        for email in emails:
            analysis_result = self._analyze_email_content(email)
            
            if analysis_result['requires_response']:
                email['analysis'] = analysis_result
                email['matched_keywords'] = analysis_result['matched_keywords']
                email['confidence_score'] = analysis_result['confidence_score']
                email['document_references'] = analysis_result['document_references']
                response_required.append(email)
                
                print(f"📋 Found response-required email: {email['subject'][:50]}...")
                print(f"   Confidence: {analysis_result['confidence_score']:.2f}")
                print(f"   Keywords: {', '.join(analysis_result['matched_keywords'])}")
                if analysis_result['document_references']:
                    print(f"   Document refs: {', '.join(analysis_result['document_references'][:3])}...")
        
        return response_required
    
    def _analyze_email_content(self, email: Dict) -> Dict:
        """Analyze email content using OpenAI to determine if it requires a document response"""
        subject = email['subject']
        body = email['body']
        sender = email['sender']
        
        try:
            # Create a prompt for OpenAI to analyze the email
            prompt = f"""
Analyze this email to determine if the sender is requesting, asking about, or expecting:
1. A document, report, proposal, PDF, or any written deliverable
2. An update on work progress or project status
3. A review of completed work
4. Any form of written output or deliverable

Email Details:
Subject: {subject}
From: {sender}
Body: {body[:1000]}...  

Please respond in JSON format with:
{{
    "requires_document_response": true/false,
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation",
    "document_type_mentioned": "type of document if mentioned (report, proposal, etc.)",
    "urgency_level": "low/medium/high",
    "document_references": ["any specific document names mentioned"]
}}

Focus on whether this email is asking for ANY kind of written work, deliverable, or document - not just specific keywords.
"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert email analyst. Analyze emails to identify requests for documents, reports, proposals, or any written deliverables."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            # Parse the response
            import json
            analysis = json.loads(response.choices[0].message.content.strip())
            
            return {
                'requires_response': analysis.get('requires_document_response', False),
                'confidence_score': float(analysis.get('confidence_score', 0.0)),
                'matched_keywords': [analysis.get('document_type_mentioned', 'document')],
                'document_references': analysis.get('document_references', []),
                'reasoning': analysis.get('reasoning', ''),
                'urgency_level': analysis.get('urgency_level', 'medium'),
                'analysis_method': 'openai_analysis'
            }
            
        except Exception as e:
            print(f"Error in OpenAI analysis: {e}")
            # Fallback to simple keyword matching
            return self._fallback_analysis(email)
    
    def _fallback_analysis(self, email: Dict) -> Dict:
        """Simple fallback analysis if OpenAI fails"""
        subject = email['subject'].lower()
        body = email['body'].lower()
        full_text = f"{subject} {body}"
        
        # Simple keywords for fallback
        document_keywords = [
            'document', 'report', 'proposal', 'pdf', 'file', 'deliverable',
            'update', 'status', 'progress', 'review', 'send', 'share',
            'complete', 'done', 'finished', 'ready'
        ]
        
        matched_keywords = [kw for kw in document_keywords if kw in full_text]
        confidence = min(len(matched_keywords) * 0.2, 1.0)
        
        return {
            'requires_response': confidence > 0.3,
            'confidence_score': confidence,
            'matched_keywords': matched_keywords,
            'document_references': [],
            'reasoning': 'Fallback keyword matching',
            'urgency_level': 'medium',
            'analysis_method': 'fallback_keywords'
        }
    
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
