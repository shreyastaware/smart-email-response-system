import os
from openai import OpenAI
from typing import Dict, Optional
from config import Config

class DocumentProcessor:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def summarize_document(self, document_data: Dict) -> str:
        """Generate a summary of the document using OpenAI"""
        try:
            content = document_data['content']
            title = document_data['title']
            
            # Prepare the prompt
            prompt = f"""
            Please provide a concise professional summary of the following document titled "{title}".
            
            Focus on:
            - Key objectives and goals
            - Main points and findings
            - Deliverables or outcomes
            - Any important conclusions or recommendations
            
            Document content:
            {content[:4000]}  # Limit content to stay within token limits
            
            Provide a summary that would be suitable for sharing in a professional email response.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional assistant helping to summarize completed work documents. Provide clear, concise, and professional summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            print(f"Error summarizing document: {e}")
            return f"Summary unavailable for document: {document_data.get('title', 'Unknown')}"
    
    def compose_response_email(self, original_email: Dict, document_data: Dict, summary: str) -> Dict:
        """Compose a response email with document summary and attachment"""
        try:
            # Extract sender information
            original_sender = original_email['sender']
            original_subject = original_email['subject']
            
            # Create response subject
            if original_subject.lower().startswith('re:'):
                response_subject = original_subject
            else:
                response_subject = f"Re: {original_subject}"
            
            # Generate email body using OpenAI
            prompt = f"""
            Compose a professional email response based on the following context:
            
            Original email subject: {original_subject}
            Original sender: {original_sender}
            Document completed: {document_data['title']}
            
            The email should:
            1. Acknowledge the original request
            2. Inform that the requested document has been completed
            3. Include the summary below
            4. Mention that the full document is attached as PDF
            5. Be polite and professional
            
            Document Summary:
            {summary}
            
            Write a complete email body (no subject line needed).
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional assistant composing email responses about completed work. Write clear, polite, and informative emails."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            email_body = response.choices[0].message.content.strip()
            
            return {
                'to': self._extract_sender_email(original_sender),
                'subject': response_subject,
                'body': email_body,
                'original_email_id': original_email['id']
            }
            
        except Exception as e:
            print(f"Error composing email: {e}")
            # Fallback to template
            return self._create_fallback_email(original_email, document_data, summary)
    
    def _extract_sender_email(self, sender: str) -> str:
        """Extract email address from sender field"""
        import re
        match = re.search(r'<(.+?)>', sender)
        if match:
            return match.group(1)
        return sender
    
    def _create_fallback_email(self, original_email: Dict, document_data: Dict, summary: str) -> Dict:
        """Create a fallback email if AI composition fails"""
        original_subject = original_email['subject']
        response_subject = f"Re: {original_subject}" if not original_subject.lower().startswith('re:') else original_subject
        
        email_body = f"""Hello,

Thank you for your email regarding the document request.

I'm pleased to inform you that the requested document "{document_data['title']}" has been completed and is ready for your review.

Document Summary:
{summary}

Please find the complete document attached as a PDF file. Feel free to reach out if you have any questions or need any clarifications.

Best regards"""
        
        return {
            'to': self._extract_sender_email(original_email['sender']),
            'subject': response_subject,
            'body': email_body,
            'original_email_id': original_email['id']
        }
