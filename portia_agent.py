import os
import time
from typing import List, Dict, Optional
from portia import Agent, PlanRun, Tool, Clarification
from gmail_processor import GmailProcessor
from docs_processor import DocsProcessor
from document_processor import DocumentProcessor
from config import Config

class EmailDocumentAgent:
    """Main Portia AI agent for processing emails and documents"""
    
    def __init__(self):
        self.gmail_processor = GmailProcessor()
        self.docs_processor = DocsProcessor()
        self.document_processor = DocumentProcessor()
        
        # Initialize Portia Agent
        self.agent = Agent(api_key=Config.PORTIA_API_KEY)
        
        # Define tools
        self.tools = [
            self._create_email_reader_tool(),
            self._create_docs_reader_tool(),
            self._create_document_matcher_tool(),
            self._create_document_processor_tool(),
            self._create_email_sender_tool()
        ]
    
    def _create_email_reader_tool(self) -> Tool:
        """Create tool for reading emails"""
        def read_emails(max_results: int = 50) -> Dict:
            try:
                emails = self.gmail_processor.get_recent_emails(max_results)
                response_required = self.gmail_processor.identify_response_required_emails(emails)
                
                return {
                    'success': True,
                    'total_emails': len(emails),
                    'response_required_emails': response_required,
                    'count_response_required': len(response_required)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return Tool(
            name="read_emails",
            description="Read recent emails and identify those requiring responses about pending documents",
            function=read_emails
        )
    
    def _create_docs_reader_tool(self) -> Tool:
        """Create tool for reading Google Docs"""
        def read_docs() -> Dict:
            try:
                all_docs = self.docs_processor.get_all_docs()
                completed_docs = self.docs_processor.find_completed_docs(all_docs)
                
                return {
                    'success': True,
                    'total_docs': len(all_docs),
                    'completed_docs': completed_docs,
                    'count_completed': len(completed_docs)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return Tool(
            name="read_docs",
            description="Read all Google Docs and identify completed documents marked with 'Done'",
            function=read_docs
        )
    
    def _create_document_matcher_tool(self) -> Tool:
        """Create tool for matching documents to emails"""
        def match_documents(email_data: Dict, completed_docs: List[Dict]) -> Dict:
            try:
                email_context = f"{email_data['subject']} {email_data['body']}"
                matched_docs = self.docs_processor.match_docs_to_email_context(
                    completed_docs, 
                    email_context
                )
                
                return {
                    'success': True,
                    'matched_docs': matched_docs,
                    'count_matched': len(matched_docs)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return Tool(
            name="match_documents",
            description="Match completed documents to email context using keyword analysis",
            function=match_documents
        )
    
    def _create_document_processor_tool(self) -> Tool:
        """Create tool for processing documents and creating summaries"""
        def process_document(doc_id: str) -> Dict:
            try:
                # Get document data
                doc_data = self.docs_processor.get_document_summary_data(doc_id)
                if not doc_data:
                    return {
                        'success': False,
                        'error': 'Could not retrieve document data'
                    }
                
                # Generate summary
                summary = self.document_processor.summarize_document(doc_data)
                
                # Create PDF
                pdf_filename = f"{doc_data['title'].replace(' ', '_').replace('Done', '').strip('_')}.pdf"
                pdf_path = os.path.join(os.getcwd(), pdf_filename)
                
                pdf_created = self.docs_processor.create_pdf_from_text(
                    doc_data['content'],
                    doc_data['title'],
                    pdf_path
                )
                
                return {
                    'success': True,
                    'document_data': doc_data,
                    'summary': summary,
                    'pdf_path': pdf_path if pdf_created else None,
                    'pdf_created': pdf_created
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return Tool(
            name="process_document",
            description="Process document to create summary and PDF",
            function=process_document
        )
    
    def _create_email_sender_tool(self) -> Tool:
        """Create tool for sending response emails"""
        def send_response_email(original_email: Dict, document_data: Dict, summary: str, pdf_path: Optional[str] = None) -> Dict:
            try:
                # Compose email
                email_response = self.document_processor.compose_response_email(
                    original_email, 
                    document_data, 
                    summary
                )
                
                # Send email
                success = self.gmail_processor.send_email(
                    email_response['to'],
                    email_response['subject'],
                    email_response['body'],
                    pdf_path
                )
                
                return {
                    'success': success,
                    'email_sent_to': email_response['to'],
                    'subject': email_response['subject'],
                    'attachment_included': pdf_path is not None
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return Tool(
            name="send_response_email",
            description="Compose and send response email with document summary and PDF attachment",
            function=send_response_email
        )
    
    def create_email_processing_plan(self) -> PlanRun:
        """Create a multi-agent plan for processing emails and documents"""
        
        plan_steps = [
            {
                'step': 1,
                'description': 'Read recent emails and identify response-required emails',
                'tool': 'read_emails',
                'clarification': Clarification(
                    question="How many recent emails should I check?",
                    options=["25", "50", "100"],
                    default="50"
                )
            },
            {
                'step': 2,
                'description': 'Read Google Docs and identify completed documents',
                'tool': 'read_docs'
            },
            {
                'step': 3,
                'description': 'Match completed documents to response-required emails',
                'tool': 'match_documents',
                'condition': 'response_required_emails_found AND completed_docs_found'
            },
            {
                'step': 4,
                'description': 'Process matched documents (summarize and create PDFs)',
                'tool': 'process_document',
                'condition': 'documents_matched'
            },
            {
                'step': 5,
                'description': 'Send response emails with summaries and PDFs',
                'tool': 'send_response_email',
                'condition': 'documents_processed'
            }
        ]
        
        # Create and return PlanRun
        plan_run = self.agent.create_plan_run(
            plan_steps=plan_steps,
            tools=self.tools,
            name="Email Document Processing Plan"
        )
        
        return plan_run
    
    def execute_full_workflow(self) -> Dict:
        """Execute the complete email and document processing workflow"""
        results = {
            'timestamp': time.time(),
            'steps_completed': [],
            'errors': [],
            'emails_processed': 0,
            'documents_processed': 0,
            'emails_sent': 0
        }
        
        try:
            print("🚀 Starting Email Document Processing Workflow...")
            
            # Step 1: Read emails
            print("📧 Step 1: Reading recent emails...")
            email_result = self.tools[0].function()
            results['steps_completed'].append('read_emails')
            
            if not email_result['success']:
                results['errors'].append(f"Email reading failed: {email_result['error']}")
                return results
            
            response_emails = email_result['response_required_emails']
            print(f"   Found {len(response_emails)} emails requiring responses")
            
            if not response_emails:
                print("   No emails requiring responses found.")
                return results
            
            # Step 2: Read Google Docs
            print("📄 Step 2: Reading Google Docs...")
            docs_result = self.tools[1].function()
            results['steps_completed'].append('read_docs')
            
            if not docs_result['success']:
                results['errors'].append(f"Docs reading failed: {docs_result['error']}")
                return results
            
            completed_docs = docs_result['completed_docs']
            print(f"   Found {len(completed_docs)} completed documents")
            
            if not completed_docs:
                print("   No completed documents found.")
                return results
            
            # Step 3-5: Process each email that requires response
            for email in response_emails:
                print(f"\\n🔄 Processing email: {email['subject'][:50]}...")
                
                # Match documents
                match_result = self.tools[2].function(email, completed_docs)
                
                if not match_result['success'] or not match_result['matched_docs']:
                    print(f"   No matching documents found for this email")
                    continue
                
                # Process the best matching document
                best_match = match_result['matched_docs'][0]
                print(f"   Best matching document: {best_match['title']}")
                
                process_result = self.tools[3].function(best_match['id'])
                
                if not process_result['success']:
                    results['errors'].append(f"Document processing failed: {process_result['error']}")
                    continue
                
                results['documents_processed'] += 1
                
                # Send response email
                send_result = self.tools[4].function(
                    email,
                    process_result['document_data'],
                    process_result['summary'],
                    process_result.get('pdf_path')
                )
                
                if send_result['success']:
                    results['emails_sent'] += 1
                    print(f"   ✅ Response sent to: {send_result['email_sent_to']}")
                else:
                    results['errors'].append(f"Email sending failed: {send_result['error']}")
                
                results['emails_processed'] += 1
            
            print(f"\\n🎉 Workflow completed!")
            print(f"   Emails processed: {results['emails_processed']}")
            print(f"   Documents processed: {results['documents_processed']}")
            print(f"   Emails sent: {results['emails_sent']}")
            
            if results['errors']:
                print(f"   Errors encountered: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"   ❌ {error}")
        
        except Exception as e:
            results['errors'].append(f"Workflow execution failed: {str(e)}")
            print(f"❌ Workflow failed: {e}")
        
        return results

# Usage example
if __name__ == "__main__":
    agent = EmailDocumentAgent()
    results = agent.execute_full_workflow()
    print("\\n" + "="*50)
    print("WORKFLOW RESULTS:")
    print("="*50)
    for key, value in results.items():
        print(f"{key}: {value}")
