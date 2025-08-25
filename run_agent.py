#!/usr/bin/env python3
"""
Email Document Processing Agent Runner

This script runs the automated email and document processing workflow.
It will:
1. Read your Gmail inbox for emails requiring responses about pending documents
2. Check your Google Docs for documents marked as "Done"
3. Match relevant completed documents to emails
4. Generate summaries and PDFs of the documents
5. Send response emails with the summaries and PDF attachments
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from email_document_processor import EmailDocumentProcessor
from config import Config

def check_configuration():
    """Check if all required configuration is present"""
    missing_configs = []
    
    if not Config.PORTIA_API_KEY:
        missing_configs.append("PORTIA_API_KEY")
    
    if not Config.OPENAI_API_KEY:
        missing_configs.append("OPENAI_API_KEY")
    
    if not Config.GOOGLE_CLIENT_ID:
        missing_configs.append("GOOGLE_CLIENT_ID")
    
    if not Config.GOOGLE_CLIENT_SECRET:
        missing_configs.append("GOOGLE_CLIENT_SECRET")
    
    if not Config.USER_EMAIL:
        missing_configs.append("USER_EMAIL")
    
    if missing_configs:
        print("❌ Missing required configuration:")
        for config in missing_configs:
            print(f"   - {config}")
        print("\\nPlease copy .env.template to .env and fill in the required values.")
        return False
    
    print("✅ Configuration check passed!")
    return True

def main():
    """Main execution function"""
    print("=" * 60)
    print("📧 EMAIL DOCUMENT PROCESSING AGENT")
    print("=" * 60)
    print()
    
    # Check configuration
    if not check_configuration():
        return 1
    
    try:
        # Initialize and run the processor
        print("🤖 Initializing Email Document Processor...")
        processor = EmailDocumentProcessor()
        
        print("🚀 Starting workflow execution...")
        print()
        
        # Execute the workflow (7 days back, max 100 emails)
        results = processor.execute_workflow(days_back=7, max_results=100)
        
        # Display results
        print("\\n" + "=" * 60)
        print("📊 EXECUTION RESULTS")
        print("=" * 60)
        print(f"Emails processed: {results['emails_processed']}")
        print(f"Documents processed: {results['documents_processed']}")
        print(f"Response emails sent: {results['emails_sent']}")
        print(f"Steps completed: {len(results['steps_completed'])}")
        
        if results['errors']:
            print(f"\\n❌ Errors encountered ({len(results['errors'])}):") 
            for i, error in enumerate(results['errors'], 1):
                print(f"   {i}. {error}")
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
    exit_code = main()
    sys.exit(exit_code)
