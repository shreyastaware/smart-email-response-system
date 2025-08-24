import io
from typing import List, Dict, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from google_auth import GoogleAuthenticator
from config import Config

class DocsProcessor:
    def __init__(self):
        self.auth = GoogleAuthenticator()
        self.docs_service = None
        self.drive_service = None
    
    def initialize(self):
        """Initialize Google Docs and Drive services"""
        self.docs_service, self.drive_service = self.auth.authenticate_docs_and_drive()
    
    def get_all_docs(self) -> List[Dict]:
        """Get all Google Docs from user's Drive"""
        if not self.drive_service:
            self.initialize()
        
        try:
            # Query for Google Docs files
            results = self.drive_service.files().list(
                q="mimeType='application/vnd.google-apps.document' and trashed=false",
                fields="files(id, name, modifiedTime, createdTime)"
            ).execute()
            
            files = results.get('files', [])
            docs = []
            
            for file in files:
                docs.append({
                    'id': file['id'],
                    'title': file['name'],
                    'modified_time': file.get('modifiedTime', ''),
                    'created_time': file.get('createdTime', '')
                })
            
            return docs
            
        except Exception as e:
            print(f"Error getting Google Docs: {e}")
            return []
    
    def find_completed_docs(self, docs: List[Dict]) -> List[Dict]:
        """Find documents marked as 'Done'"""
        completed_docs = []
        
        for doc in docs:
            if doc['title'].endswith(Config.COMPLETION_MARKER):
                completed_docs.append(doc)
        
        return completed_docs
    
    def get_document_content(self, doc_id: str) -> Optional[str]:
        """Get the full text content of a Google Doc"""
        if not self.docs_service:
            self.initialize()
        
        try:
            document = self.docs_service.documents().get(documentId=doc_id).execute()
            content = self._extract_text_from_document(document)
            return content
            
        except Exception as e:
            print(f"Error getting document content for {doc_id}: {e}")
            return None
    
    def _extract_text_from_document(self, document: Dict) -> str:
        """Extract plain text from Google Docs document structure"""
        content = document.get('body', {}).get('content', [])
        text_content = []
        
        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                paragraph_text = self._extract_paragraph_text(paragraph)
                if paragraph_text.strip():
                    text_content.append(paragraph_text)
        
        return '\n\n'.join(text_content)
    
    def _extract_paragraph_text(self, paragraph: Dict) -> str:
        """Extract text from a paragraph element"""
        elements = paragraph.get('elements', [])
        text_parts = []
        
        for element in elements:
            text_run = element.get('textRun', {})
            content = text_run.get('content', '')
            text_parts.append(content)
        
        return ''.join(text_parts)
    
    def create_pdf_from_text(self, text: str, title: str, output_path: str) -> bool:
        """Create a PDF from text content"""
        try:
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=TA_LEFT,
                spaceAfter=20
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_JUSTIFY,
                spaceAfter=12
            )
            
            # Build PDF content
            story = []
            
            # Add title
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 20))
            
            # Add content paragraphs
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Clean up the text for PDF
                    cleaned_para = para.strip().replace('\n', ' ')
                    story.append(Paragraph(cleaned_para, body_style))
                    story.append(Spacer(1, 12))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error creating PDF: {e}")
            return False
    
    def match_docs_to_email_context(self, completed_docs: List[Dict], email_context: str) -> List[Dict]:
        """Match completed documents to email context using keywords"""
        matched_docs = []
        email_words = set(email_context.lower().split())
        
        for doc in completed_docs:
            doc_words = set(doc['title'].lower().split())
            
            # Simple keyword matching - can be enhanced with more sophisticated NLP
            overlap = len(email_words.intersection(doc_words))
            if overlap > 0:
                doc['relevance_score'] = overlap
                matched_docs.append(doc)
        
        # Sort by relevance score
        matched_docs.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return matched_docs
    
    def get_document_summary_data(self, doc_id: str) -> Optional[Dict]:
        """Get document data for summarization"""
        if not self.drive_service or not self.docs_service:
            self.initialize()
        
        try:
            # Get document metadata
            file_data = self.drive_service.files().get(fileId=doc_id).execute()
            
            # Get document content
            content = self.get_document_content(doc_id)
            
            if content:
                return {
                    'id': doc_id,
                    'title': file_data['name'],
                    'content': content,
                    'modified_time': file_data.get('modifiedTime', ''),
                    'size': len(content)
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting document summary data: {e}")
            return None
