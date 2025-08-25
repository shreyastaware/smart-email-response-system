#!/usr/bin/env python3
"""
Done & Delivered - AI-Powered Email Response System

An advanced example demonstrating Portia AI's cloud tools for automated email workflows.

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
            1. Scan the last 7 days of your Gmail inbox for pending work/document/ any kind of work related requests and identify completed Google Docs with "Done" in the title.

            2. AI-match the email requests to the corresponding "Done" documents.

            3. For each match, auto-reply within the original email thread, attaching a PDF of the document and including a brief summary. CC yourself on the reply.

            4. Verify email of original sender and the person you are sending for each matched document and then send.

            5. The previous should appear as a thread while sending the reply. This is important!

            6. Provide a summary report of all actions taken.
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
