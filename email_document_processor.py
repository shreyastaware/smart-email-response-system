#!/usr/bin/env python3
"""
Standalone Email Document Processor

This script processes emails and documents without using complex Portia plans.
It provides the same functionality but with direct function calls.
"""

import os
import time
from typing import List, Dict, Optional
from gmail_processor import GmailProcessor
from docs_processor import DocsProcessor
from document_processor import DocumentProcessor
from config import Config

class EmailDocumentProcessor:
    """Standalone email and document processor"""
    
    def __init__(self):
        self.gmail_processor = GmailProcessor()
        self.docs_processor = DocsProcessor()
        self.document_processor = DocumentProcessor()
    
    def execute_workflow(self, days_back: int = 7, max_results: int = 100) -> Dict:
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
            print(f"📧 Step 1: Reading recent emails (last {days_back} days)...")
            try:
                emails = self.gmail_processor.get_recent_emails(days_back, max_results)
                response_required = self.gmail_processor.identify_response_required_emails(emails)
                results['steps_completed'].append('read_emails')
                
                print(f"   Analyzed {len(emails)} emails from last {days_back} days")
                print(f"   Found {len(response_required)} emails requiring responses")
                
                if not response_required:
                    print("   No emails requiring responses found.")
                    return results
                    
            except Exception as e:
                error_msg = f"Email reading failed: {e}"
                results['errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
                return results
            
            # Step 2: Read Google Docs
            print("📄 Step 2: Reading Google Docs...")
            try:
                all_docs = self.docs_processor.get_all_docs()
                completed_docs = self.docs_processor.find_completed_docs(all_docs)
                results['steps_completed'].append('read_docs')
                
                print(f"   Found {len(completed_docs)} completed documents")
                
                if not completed_docs:
                    print("   No completed documents found.")
                    return results
                    
            except Exception as e:
                error_msg = f"Docs reading failed: {e}"
                results['errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
                return results
            
            # Step 3-5: Process each email that requires response
            for i, email in enumerate(response_required, 1):
                print(f"\\n🔄 Processing email {i}/{len(response_required)}: {email['subject'][:50]}...")
                print(f"   From: {email['sender'][:40]}...")
                print(f"   Confidence: {email.get('confidence_score', 0):.2f}")
                
                if email.get('document_references'):
                    print(f"   Referenced docs: {', '.join(email['document_references'][:2])}...")
                
                try:
                    # Step 3: Match documents
                    matched_docs = self.docs_processor.match_docs_to_email_context(completed_docs, email)
                    
                    if not matched_docs:
                        print(f"   ❌ No matching documents found for this email")
                        continue
                    
                    # Process the best matching document
                    best_match = matched_docs[0]
                    print(f"   ✅ Best match: {best_match['title']} (score: {best_match['relevance_score']})") 
                    print(f"   Match reasons: {', '.join(best_match['match_reasons'][:2])}...")
                    
                    # Step 4: Process document (get content, summarize, create PDF)
                    try:
                        doc_data = self.docs_processor.get_document_summary_data(best_match['id'])
                        if not doc_data:
                            print(f"   ❌ Could not retrieve document data")
                            continue
                        
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
                        
                        results['documents_processed'] += 1
                        print(f"   📝 Document processed, PDF created: {pdf_created}")
                        
                    except Exception as e:
                        error_msg = f"Document processing failed: {e}"
                        results['errors'].append(error_msg)
                        print(f"   ❌ {error_msg}")
                        continue
                    
                    # Step 5: Send response email
                    try:
                        # Compose email
                        email_response = self.document_processor.compose_response_email(
                            email,
                            doc_data,
                            summary
                        )
                        
                        # Send email
                        success = self.gmail_processor.send_email(
                            email_response['to'],
                            email_response['subject'], 
                            email_response['body'],
                            pdf_path if pdf_created else None
                        )
                        
                        if success:
                            results['emails_sent'] += 1
                            print(f"   ✅ Response sent to: {email_response['to']}")
                        else:
                            error_msg = f"Email sending failed for {email_response['to']}"
                            results['errors'].append(error_msg)
                            print(f"   ❌ {error_msg}")
                        
                        results['emails_processed'] += 1
                        
                    except Exception as e:
                        error_msg = f"Email sending failed: {e}"
                        results['errors'].append(error_msg)
                        print(f"   ❌ {error_msg}")
                        continue
                        
                except Exception as e:
                    error_msg = f"Processing failed for email '{email['subject'][:30]}...': {e}"
                    results['errors'].append(error_msg)
                    print(f"   ❌ {error_msg}")
                    continue
            
            # Final results
            print(f"\\n🎉 Workflow completed!")
            print(f"   Emails processed: {results['emails_processed']}")
            print(f"   Documents processed: {results['documents_processed']}")
            print(f"   Emails sent: {results['emails_sent']}")
            
            if results['errors']:
                print(f"   Errors encountered: {len(results['errors'])}")
                for j, error in enumerate(results['errors'], 1):
                    print(f"   {j}. {error}")
        
        except Exception as e:
            results['errors'].append(f"Workflow execution failed: {str(e)}")
            print(f"❌ Workflow failed: {e}")
        
        return results

def main():
    """Main execution function"""
    print("=" * 60)
    print("📧 EMAIL DOCUMENT PROCESSING WORKFLOW")
    print("=" * 60)
    print()
    
    # Check configuration
    if not Config.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not configured in .env file")
        return 1
        
    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        print("❌ Google OAuth credentials not configured in .env file")
        return 1
    
    try:
        # Initialize and run the processor
        processor = EmailDocumentProcessor()
        
        # Execute with default settings (7 days, 100 emails max)
        results = processor.execute_workflow(days_back=3, max_results=100)
        
        # Display summary
        print("\\n" + "=" * 60)
        print("📊 EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Emails processed: {results['emails_processed']}")
        print(f"Documents processed: {results['documents_processed']}")
        print(f"Response emails sent: {results['emails_sent']}")
        print(f"Steps completed: {len(results['steps_completed'])}")
        
        if results['errors']:
            print(f"\\n❌ Errors encountered: {len(results['errors'])}")
        else:
            print("\\n✅ No errors encountered!")
        
        return 0 if not results['errors'] else 1
        
    except KeyboardInterrupt:
        print("\\n🛑 Execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\\n❌ Execution failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
