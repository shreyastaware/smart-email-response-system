import os
import time
from typing import List, Dict, Optional

# Set Portia API key before importing
from config import Config
os.environ['PORTIA_API_KEY'] = Config.PORTIA_API_KEY

from portia import Portia, PlanRun, Clarification, PlanBuilder
from portia_tool_wrapper import CustomTool, create_tool
from gmail_processor import GmailProcessor
from docs_processor import DocsProcessor
from document_processor import DocumentProcessor

class EmailDocumentAgent:
    """Main Portia AI agent for processing emails and documents"""
    
    def __init__(self):
        self.gmail_processor = GmailProcessor()
        self.docs_processor = DocsProcessor()
        self.document_processor = DocumentProcessor()
        
        # Initialize Portia client
        self.portia = Portia()
        
        # Define tools
        self.tools = [
            self._create_email_reader_tool(),
            self._create_docs_reader_tool(),
            self._create_document_matcher_tool(),
            self._create_document_processor_tool(),
            self._create_email_sender_tool()
        ]
    
    def _create_email_reader_tool(self) -> CustomTool:
        """Create tool for reading emails from the last 7 days"""
        def read_emails(days_back: int = 7, max_results: int = 100) -> Dict:
            try:
                # print(days_back, max_results)
                emails = self.gmail_processor.get_recent_emails(days_back, max_results)
                response_required = self.gmail_processor.identify_response_required_emails(emails)
                
                return {
                    'success': True,
                    'total_emails': len(emails),
                    'response_required_emails': response_required,
                    'count_response_required': len(response_required),
                    'days_analyzed': days_back
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return create_tool(
            name="read_emails",
            description="Read recent emails from the last 7 days and intelligently identify those requiring responses about pending documents",
            function=read_emails
        )
    
    def _create_docs_reader_tool(self) -> CustomTool:
        """Create tool for reading Google Docs"""
        def read_docs() -> Dict:
            try:
                print("📄 Scanning Google Docs...")
                all_docs = self.docs_processor.get_all_docs()
                print(f"📊 Found {len(all_docs)} total documents")
                
                if all_docs:
                    print("📋 Document titles found:")
                    for i, doc in enumerate(all_docs[:5], 1):  # Show first 5
                        print(f"   {i}. {doc['title']}")
                    if len(all_docs) > 5:
                        print(f"   ... and {len(all_docs) - 5} more")
                
                completed_docs = self.docs_processor.find_completed_docs(all_docs)
                print(f"✅ Found {len(completed_docs)} completed documents (ending with '{Config.COMPLETION_MARKER}')")
                
                if completed_docs:
                    print("📝 Completed documents:")
                    for i, doc in enumerate(completed_docs, 1):
                        print(f"   {i}. {doc['title']} (ID: {doc['id']})")
                else:
                    print(f"💡 No documents found ending with '{Config.COMPLETION_MARKER}'")
                    print("   Make sure your Google Docs titles end with 'Done'")
                    print("   Example: 'Project Report Done'")
                
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
        
        return create_tool(
            name="read_docs",
            description="Read all Google Docs and identify completed documents marked with 'Done'",
            function=read_docs
        )
    
    def _create_document_matcher_tool(self) -> CustomTool:
        """Create tool for intelligently matching documents to emails"""
        def match_documents(email_data: Dict, completed_docs: List[Dict]) -> Dict:
            try:
                matched_docs = self.docs_processor.match_docs_to_email_context(
                    completed_docs, 
                    email_data  # Pass the full email data object
                )
                
                return {
                    'success': True,
                    'matched_docs': matched_docs,
                    'count_matched': len(matched_docs),
                    'email_subject': email_data['subject'],
                    'document_references': email_data.get('document_references', [])
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return create_tool(
            name="match_documents",
            description="Intelligently match completed documents to email using content analysis, document references, and semantic matching",
            function=match_documents
        )
    
    def _create_document_processor_tool(self) -> CustomTool:
        """Create tool for processing documents and creating summaries"""
        def process_document(doc_id: str) -> Dict:
            try:
                print(f"🔄 Processing document with ID: {doc_id}")
                
                # Get document data
                doc_data = self.docs_processor.get_document_summary_data(doc_id)
                if not doc_data:
                    return {
                        'success': False,
                        'error': f'Could not retrieve document data for ID: {doc_id}. Check Google API permissions and document access.'
                    }
                
                print(f"📝 Document retrieved: {doc_data['title']}")
                print(f"📏 Content length: {doc_data['size']} characters")
                
                # Generate summary
                print("🤖 Generating AI summary...")
                summary = self.document_processor.summarize_document(doc_data)
                
                # Create PDF
                pdf_filename = f"{doc_data['title'].replace(' ', '_').replace('Done', '').strip('_')}.pdf"
                pdf_path = os.path.join(os.getcwd(), pdf_filename)
                
                print(f"📄 Creating PDF: {pdf_filename}")
                pdf_created = self.docs_processor.create_pdf_from_text(
                    doc_data['content'],
                    doc_data['title'],
                    pdf_path
                )
                
                if pdf_created:
                    print(f"✅ PDF created successfully: {pdf_path}")
                else:
                    print("⚠️ PDF creation failed")
                
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
        
        return create_tool(
            name="process_document",
            description="Process document to create summary and PDF",
            function=process_document
        )
    
    def _create_email_sender_tool(self) -> CustomTool:
        """Create tool for sending response emails"""
        def send_response_email(original_email: Dict, document_data: Dict, summary: str, pdf_path: Optional[str] = None) -> Dict:
            try:
                # Compose email
                email_response = self.document_processor.compose_response_email(
                    original_email, 
                    document_data, 
                    summary
                )
                
                # Send email as reply
                success = self.gmail_processor.send_email(
                    email_response['to'],
                    email_response['subject'],
                    email_response['body'],
                    pdf_path,
                    email_response.get('original_email_id')  # Pass original email ID for threading
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
        
        return create_tool(
            name="send_response_email",
            description="Compose and send response email with document summary and PDF attachment",
            function=send_response_email
        )
    
    def create_email_processing_plan(self) -> PlanRun:
        """Create a multi-agent plan for processing emails and documents"""
        
        try:
            # Create a plan using PlanBuilder
            plan_builder = PlanBuilder()
            
            # Add steps to the plan
            plan_builder.add_step(
                "Read recent emails and identify response-required emails",
                tool_name="read_emails"
            )
            
            plan_builder.add_step(
                "Read Google Docs and identify completed documents", 
                tool_name="read_docs"
            )
            
            plan_builder.add_step(
                "Match completed documents to response-required emails",
                tool_name="match_documents"
            )
            
            plan_builder.add_step(
                "Process matched documents (summarize and create PDFs)",
                tool_name="process_document"
            )
            
            plan_builder.add_step(
                "Send response emails with summaries and PDFs",
                tool_name="send_response_email"
            )
            
            # Build the plan
            plan = plan_builder.build()
            
            # Create and return PlanRun
            plan_run = self.portia.create_plan_run(
                plan=plan,
                tools=self.tools
            )
            
            return plan_run
            
        except Exception as e:
            print(f"Error creating plan: {e}")
            return None
    
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
            
            # Step 1: Read emails from last 7 days
            print("📧 Step 1: Reading recent emails (last 3 days)...")
            email_result = self.tools[0].function(days_back=3, max_results=100)
            results['steps_completed'].append('read_emails')
            
            if not email_result['success']:
                results['errors'].append(f"Email reading failed: {email_result['error']}")
                return results
            
            response_emails = email_result['response_required_emails']
            print(f"   Analyzed {email_result['total_emails']} emails from last {email_result['days_analyzed']} days")
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
            for i, email in enumerate(response_emails, 1):
                print(f"\n🔄 Processing email {i}/{len(response_emails)}: {email['subject'][:50]}...")
                print(f"   From: {email['sender'][:40]}...")
                print(f"   Confidence: {email.get('confidence_score', 0):.2f}")
                
                if email.get('document_references'):
                    print(f"   Referenced docs: {', '.join(email['document_references'][:2])}...")
                
                # Match documents
                match_result = self.tools[2].function(email, completed_docs)
                
                if not match_result['success'] or not match_result['matched_docs']:
                    print(f"   ❌ No matching documents found for this email")
                    continue
                
                # Process the best matching document
                best_match = match_result['matched_docs'][0]
                print(f"   ✅ Best match: {best_match['title']} (score: {best_match['relevance_score']})")
                print(f"   Match reasons: {', '.join(best_match['match_reasons'][:2])}...")
                
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
