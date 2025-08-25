#!/usr/bin/env python3
"""
Setup script for Email Document Processing Agent
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment file"""
    env_file = Path('.env')
    template_file = Path('.env.template')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not template_file.exists():
        print("❌ .env.template not found")
        return False
    
    try:
        # Copy template to .env
        with open(template_file, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your API keys before running the agent")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def print_next_steps():
    """Print instructions for next steps"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit the .env file with your API keys:")
    print("   - Portia AI API key")
    print("   - OpenAI API key") 
    print("   - Google OAuth2 credentials")
    print("   - Your Gmail address")
    print("\n2. Run the agent:")
    print("   python run_agent.py")
    print("\n3. For detailed setup instructions, see README.md")
    print("\nAPI Key Setup URLs:")
    print("- Portia AI: https://docs.portialabs.ai/")
    print("- OpenAI: https://platform.openai.com/api-keys")
    print("- Google Cloud: https://console.cloud.google.com/")

def main():
    """Main setup function"""
    print("🚀 Email Document Processing Agent Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Setup environment
    if not setup_environment():
        return 1
    
    # Print next steps
    print_next_steps()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
