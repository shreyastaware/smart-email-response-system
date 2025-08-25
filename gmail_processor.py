import base64
import re
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from google_auth import GoogleAuthenticator
from config import Config

class GmailProcessor:
    def __init__(self):
        self.auth = GoogleAuthenticator()
        self.service = None
    
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
        """Analyze email content to determine if it requires a response about documents"""
        subject = email['subject'].lower()
        body = email['body'].lower()
        sender = email['sender'].lower()
        
        # Combine all text for analysis
        full_text = f"{subject} {body}"
        
        # Enhanced keyword patterns for document requests
        document_request_patterns = [
            # Direct requests
            r'\b(send|share|provide|submit)\s+.*\b(document|doc|file|report|paper)\b',
            r'\b(where\s+is|what\s+about|status\s+of|update\s+on)\s+.*\b(document|doc|file|report|paper)\b',
            r'\b(pending|waiting\s+for|awaiting|expecting)\s+.*\b(document|doc|file|report|paper)\b',
            
            # Status inquiries
            r'\b(ready|finished|completed|done)\s+.*\b(document|doc|file|report|paper)\b',
            r'\b(document|doc|file|report|paper)\s+.*\b(ready|finished|completed|done)\b',
            
            # Review requests
            r'\b(review|check|look\s+at|feedback\s+on)\s+.*\b(document|doc|file|report|paper)\b',
            r'\bplease\s+(review|check|send|share)\b',
            
            # Deadline related
            r'\b(deadline|due\s+date|timeline)\b.*\b(document|doc|file|report|paper)\b',
            r'\b(urgent|asap|immediately)\b.*\b(document|doc|file|report|paper)\b',
            
            # Work completion
            r'\b(work|task|project)\s+.*\b(complete|finished|done|ready)\b',
            r'\b(complete|finished|done|ready)\s+.*\b(work|task|project)\b'
        ]
        
        # Simple keyword fallback
        simple_keywords = [
            'pending document', 'document review', 'please review', 'awaiting document',
            'document status', 'completed work', 'finished document', 'send document',
            'share document', 'document ready', 'work done', 'project complete',
            'status update', 'where is', 'when will', 'document deadline'
        ]
        
        matched_keywords = []
        confidence_score = 0.0
        document_references = []
        
        # Check regex patterns (higher confidence)
        for pattern in document_request_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                matched_keywords.extend([match[0] if isinstance(match, tuple) else match for match in matches])
                confidence_score += 0.3
        
        # Check simple keywords (lower confidence)
        for keyword in simple_keywords:
            if keyword in full_text:
                matched_keywords.append(keyword)
                confidence_score += 0.1
        
        # Extract potential document references
        doc_name_patterns = [
            r'"([^"%]*(?:document|doc|file|report|paper|project)[^"%]*)"|\''([^\]'*(?:document|doc|file|report|paper|project)[^\]'*)\'',
            r'\b([A-Z][a-zA-Z\s]+(?:Report|Document|Paper|Project|Analysis))\b',
            r'\b(\w+\s+(?:document|doc|file|report|paper|project))\b'
        ]
        
        for pattern in doc_name_patterns:
            matches = re.findall(pattern, email['subject'] + ' ' + email['body'], re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    for submatch in match:
                        if submatch.strip():
                            document_references.append(submatch.strip())
                else:
                    document_references.append(match.strip())
        
        # Remove duplicates and filter out very short references
        document_references = list(set([ref for ref in document_references if len(ref) > 3]))
        
        # Boost confidence if sender seems to be requesting something
        question_indicators = ['?', 'when', 'where', 'what', 'how', 'please', 'can you', 'could you']
        if any(indicator in full_text for indicator in question_indicators):
            confidence_score += 0.1
        
        # Reduce confidence for automated emails
        automated_indicators = ['noreply', 'no-reply', 'automated', 'system', 'notification']
        if any(indicator in sender for indicator in automated_indicators):
            confidence_score -= 0.2
        
        # Determine if response is required (threshold-based)
        requires_response = confidence_score > 0.2 and len(matched_keywords) > 0
        
        return {
            'requires_response': requires_response,
            'confidence_score': min(confidence_score, 1.0),  # Cap at 1.0
            'matched_keywords': list(set(matched_keywords)),
            'document_references': document_references[:10],  # Limit to top 10
            'analysis_method': 'enhanced_pattern_matching'
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
