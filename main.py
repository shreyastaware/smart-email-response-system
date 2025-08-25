#!/usr/bin/env python3
"""
Done & Delivered - AI-Powered Email Response System

Powered by Portia AI's multi-agent framework for intelligent email and document processing.
Simply add "Done" to your Google Doc title, and let Portia's AI agents handle the rest!
"""

import sys
from portia_agent import EmailDocumentAgent
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
        print("\nPlease create a .env file with the required values.")
        return False
    
    print("✅ Configuration validated!")
    return True

def main():
    """Main execution using Portia AI's multi-agent framework"""
    print("=" * 70)
    print("🤖 DONE & DELIVERED - AI EMAIL RESPONSE SYSTEM")
    print("Powered by Portia AI Multi-Agent Framework")
    print("=" * 70)
    print()
    
    # Check configuration
    if not check_configuration():
        return 1
    
    try:
        print("🚀 Initializing Portia AI Agents...")
        
        # Initialize the Portia-powered agent
        agent = EmailDocumentAgent()
        
        print("📋 Portia AI will now:")
        print("   1. 🔍 Intelligently analyze your recent emails")
        print("   2. 📄 Scan Google Docs for completed work")
        print("   3. 🧠 Match documents to relevant email requests")
        print("   4. ✨ Generate professional summaries and PDFs")
        print("   5. 📧 Send polished response emails automatically")
        print()
        
        # Execute Portia's intelligent workflow
        print("🤖 Portia AI agents are working...")
        results = agent.execute_full_workflow()
        
        # Display results
        print("\n" + "=" * 70)
        print("📊 PORTIA AI EXECUTION RESULTS")
        print("=" * 70)
        print(f"✅ Emails intelligently processed: {results['emails_processed']}")
        print(f"📝 Documents automatically processed: {results['documents_processed']}")
        print(f"📧 Professional responses sent: {results['emails_sent']}")
        print(f"🎯 Workflow steps completed: {len(results['steps_completed'])}")
        
        if results['errors']:
            print(f"\n⚠️  Issues handled by Portia ({len(results['errors'])}):") 
            for i, error in enumerate(results['errors'], 1):
                print(f"   {i}. {error}")
        else:
            print("\n🎉 Perfect execution! No issues encountered.")
        
        print(f"\n🚀 Portia AI completed your workflow in {len(results['steps_completed'])} intelligent steps!")
        
        return 0 if not results['errors'] else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Workflow interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
