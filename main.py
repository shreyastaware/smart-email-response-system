#!/usr/bin/env python3
"""
Done & Delivered - AI-Powered Email Response System

An advanced example demonstrating Portia AI's cloud tools for automated email workflows.
Follows the pattern from portia-agent-examples/getting-started/2_tools_end_users_llms.py

Required configuration:
- `PORTIA_API_KEY`
- `USER_EMAIL`
"""

from dotenv import load_dotenv
from portia import (
    Config,
    DefaultToolRegistry,
    Portia,
    StorageClass,
    open_source_tool_registry,
)
from portia.cli import CLIExecutionHooks
import os
import sys

load_dotenv()

def main():
    """Main execution using Portia AI's cloud tools"""
    print("🤖 Done & Delivered - Portia AI Email Response System")
    print("=" * 60)
    
    # Check required environment variables
    if not os.getenv('PORTIA_API_KEY'):
        print("❌ PORTIA_API_KEY not found in environment")
        print("Please add your Portia API key to .env file")
        return 1
    
    if not os.getenv('USER_EMAIL'):
        print("❌ USER_EMAIL not found in environment") 
        print("Please add your email address to .env file")
        return 1
    
    try:
        # Instantiate Portia with cloud storage and default tools
        # This gives us access to Gmail, Google Docs, and other cloud services
        my_config = Config.from_default(storage_class=StorageClass.CLOUD)
        
        portia = Portia(
            config=my_config,
            tools=DefaultToolRegistry(my_config) + open_source_tool_registry,
            execution_hooks=CLIExecutionHooks(),
        )
        
        user_email = os.getenv('USER_EMAIL')
        
        # Define the email automation task
        # Portia will handle Gmail OAuth, Google Docs access, and all processing
        email_automation_task = f"""
        I need help with an automated email response workflow. Here's what I need you to do:

        1. **Email Analysis**: Scan my recent Gmail messages (last 7 days) to find emails where people (they have gmail.com in their emails) are requesting documents, reports, work updates, or asking for completed tasks.

        2. **Document Discovery**: Check my Google Docs for documents that have "Done" in their title - these represent work I've completed.

        3. **Intelligent Matching**: For each "Done" document, use your AI capabilities to determine if it corresponds to any of the recent email requests. Consider:
           - Subject line keywords
           - Sender information  
           - Content context
           - Timeline alignment

        4. **Professional Response Generation**: For each matched pair:
           - Read the Google Doc content and generate a concise, professional summary
           - Convert the Google Doc to PDF format
           - Compose a professional REPLY email that:
             * REPLIES DIRECTLY to the original email (not a new email)
             * Uses proper email threading with "Re:" prefix in subject
             * Includes the In-Reply-To and References headers for proper conversation threading
             * References the original request appropriately in the email body
             * Includes the document summary in the email body
             * Attaches the PDF version of the document
             * CC's me at {user_email} so I can see what was sent
             * Appears in the same conversation thread as the original request
           - Send the REPLY email (not a new standalone email)

        5. **Email Threading Requirements**: 
           - CRITICAL: Each response must be sent as a REPLY to the original email
           - The reply must appear in the same conversation thread in Gmail
           - Use proper email headers to maintain conversation threading
           - Subject should be "Re: [original subject]"

        6. **Reporting**: Provide me with a summary of all actions taken, including which documents were matched to which emails and what responses were sent.

        Please be intelligent and contextual in your matching - don't just rely on exact keyword matches. Use natural language understanding to make appropriate connections between requests and completed work.

        IMPORTANT: Every email you send MUST be a reply to an existing email, not a new standalone email.
        """
        
        print("📋 Creating execution plan...")
        plan = portia.plan(email_automation_task)
        
        print("\n🔍 Execution Plan Preview:")
        print(plan.pretty_print())
        
        print(f"\n🚀 Executing workflow for user: {user_email}")
        print("Note: Portia will handle Google OAuth authentication as needed...")
        
        # Execute the plan with user context for authentication
        # The end_user parameter helps Portia manage authentication tokens
        plan_run = portia.run_plan(plan, end_user=user_email)
        
        print("\n✅ Workflow completed!")
        print("📧 Check your Gmail for sent responses and CC notifications.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
