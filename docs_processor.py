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
    
    def match_docs_to_email_context(self, completed_docs: List[Dict], email_data: Dict) -> List[Dict]:
        """Intelligently match completed documents to email using multiple criteria"""
        matched_docs = []
        
        email_subject = email_data['subject'].lower()
        email_body = email_data['body'].lower()
        document_references = email_data.get('document_references', [])
        
        print(f"🔍 Matching {len(completed_docs)} completed docs to email context...")
        if document_references:
            print(f"   Document references found: {document_references[:3]}...")
        
        for doc in completed_docs:
            doc_title = doc['title'].lower()
            doc_title_clean = doc_title.replace('done', '').strip()
            
            relevance_score = self._calculate_document_relevance(
                doc_title_clean, 
                email_subject, 
                email_body, 
                document_references
            )
            
            if relevance_score > 0:
                doc_copy = doc.copy()
                doc_copy['relevance_score'] = relevance_score
                doc_copy['match_reasons'] = self._get_match_reasons(
                    doc_title_clean, 
                    email_subject, 
                    email_body, 
                    document_references
                )
                matched_docs.append(doc_copy)
        
        # Sort by relevance score
        matched_docs.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Log top matches
        for i, doc in enumerate(matched_docs[:3]):
            print(f"   Match {i+1}: {doc['title']} (score: {doc['relevance_score']:.2f})")
            print(f"     Reasons: {', '.join(doc['match_reasons'])}")
        
        return matched_docs
    
    def _calculate_document_relevance(self, doc_title: str, email_subject: str, email_body: str, document_refs: List[str]) -> float:
        """Calculate how relevant a document is to an email"""
        score = 0.0
        
        # 1. Direct title matching with document references (highest priority)
        for ref in document_refs:
            ref_clean = ref.lower().strip('"\'')
            # Exact match
            if ref_clean in doc_title or doc_title in ref_clean:
                score += 2.0
            # Partial match (multiple words)
            ref_words = set(ref_clean.split())
            doc_words = set(doc_title.split())
            common_words = ref_words.intersection(doc_words)
            if len(common_words) >= 2:
                score += 1.5
            elif len(common_words) == 1 and len(ref_words) <= 2:
                score += 1.0
        
        # 2. Subject line matching (high priority)
        subject_words = set(email_subject.split())
        doc_words = set(doc_title.split())
        subject_overlap = len(subject_words.intersection(doc_words))
        
        if subject_overlap >= 2:
            score += 1.0
        elif subject_overlap == 1:
            score += 0.5
        
        # 3. Body content matching (medium priority)
        body_words = set(email_body.split())
        body_overlap = len(body_words.intersection(doc_words))
        
        if body_overlap >= 3:
            score += 0.7
        elif body_overlap >= 2:
            score += 0.4
        elif body_overlap == 1:
            score += 0.2
        
        # 4. Semantic matching for common document types
        doc_type_matches = self._check_document_type_matching(doc_title, email_subject + ' ' + email_body)
        score += doc_type_matches * 0.3
        
        # 5. Project/category matching
        project_score = self._check_project_category_matching(doc_title, email_subject + ' ' + email_body)
        score += project_score * 0.5
        
        return round(score, 2)
    
    def _get_match_reasons(self, doc_title: str, email_subject: str, email_body: str, document_refs: List[str]) -> List[str]:
        """Get human-readable reasons for why a document matched"""
        reasons = []
        
        # Check document references
        for ref in document_refs:
            ref_clean = ref.lower().strip('"\'“”')
            if ref_clean in doc_title or doc_title in ref_clean:
                reasons.append(f"Direct reference match: '{ref}'")
            else:
                ref_words = set(ref_clean.split())
                doc_words = set(doc_title.split())
                common = ref_words.intersection(doc_words)
                if len(common) >= 2:
                    reasons.append(f"Partial reference match: {', '.join(common)}")
        
        # Check subject matching
        subject_words = set(email_subject.split())
        doc_words = set(doc_title.split())
        subject_common = subject_words.intersection(doc_words)
        if len(subject_common) >= 2:
            reasons.append(f"Subject match: {', '.join(list(subject_common)[:3])}")
        
        # Check document type
        doc_types = ['report', 'analysis', 'document', 'project', 'paper', 'study', 'presentation']
        full_text = email_subject + ' ' + email_body
        for doc_type in doc_types:
            if doc_type in doc_title and doc_type in full_text:
                reasons.append(f"Document type: {doc_type}")
                break
        
        return reasons if reasons else ['General keyword overlap']
    
    def _check_document_type_matching(self, doc_title: str, email_content: str) -> int:
        """Check if document type mentioned in email matches document title"""
        doc_types = {
            'report': ['report', 'reporting', 'summary', 'findings'],
            'analysis': ['analysis', 'analyze', 'research', 'study'],
            'presentation': ['presentation', 'slides', 'deck', 'ppt'],
            'document': ['document', 'doc', 'documentation'],
            'paper': ['paper', 'article', 'publication'],
            'proposal': ['proposal', 'plan', 'strategy'],
            'review': ['review', 'evaluation', 'assessment']
        }
        
        matches = 0
        for doc_type, keywords in doc_types.items():
            if any(keyword in doc_title for keyword in keywords):
                if any(keyword in email_content for keyword in keywords):
                    matches += 1
        
        return matches
    
    def _check_project_category_matching(self, doc_title: str, email_content: str) -> int:
        """Check for project or category name matching"""
        # Extract potential project names (capitalized words)
        import re
        
        doc_projects = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', doc_title)
        email_projects = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', email_content)
        
        # Count matching project names
        matches = 0
        for doc_proj in doc_projects:
            if any(doc_proj.lower() in email_proj.lower() or email_proj.lower() in doc_proj.lower() 
                   for email_proj in email_projects):
                matches += 1
        
        return matches
    
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
