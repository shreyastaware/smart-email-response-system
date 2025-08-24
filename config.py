import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Portia AI Configuration
    PORTIA_API_KEY = os.getenv('PORTIA_API_KEY')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Google API Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # Email Configuration
    USER_EMAIL = os.getenv('USER_EMAIL')
    
    # Google API Scopes
    GMAIL_SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    DOCS_SCOPES = [
        'https://www.googleapis.com/auth/documents.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
    
    # Keywords to identify emails requiring responses
    RESPONSE_KEYWORDS = [
        'pending document',
        'document review',
        'please review',
        'awaiting document',
        'document status',
        'completed work',
        'finished document'
    ]
    
    # Document completion marker
    COMPLETION_MARKER = 'Done'
