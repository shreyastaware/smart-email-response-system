import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import Config

class GoogleAuthenticator:
    def __init__(self):
        self.gmail_service = None
        self.docs_service = None
        self.drive_service = None
    
    def authenticate_gmail(self):
        """Authenticate and return Gmail API service"""
        creds = None
        token_file = 'gmail_token.pickle'
        
        # The file token.pickle stores the user's access and refresh tokens.
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": Config.GOOGLE_CLIENT_ID,
                            "client_secret": Config.GOOGLE_CLIENT_SECRET,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost:8080"]
                        }
                    },
                    Config.GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        return self.gmail_service
    
    def authenticate_docs_and_drive(self):
        """Authenticate and return Google Docs and Drive API services"""
        creds = None
        token_file = 'docs_token.pickle'
        
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": Config.GOOGLE_CLIENT_ID,
                            "client_secret": Config.GOOGLE_CLIENT_SECRET,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost:8080"]
                        }
                    },
                    Config.DOCS_SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.docs_service = build('docs', 'v1', credentials=creds)
        self.drive_service = build('drive', 'v3', credentials=creds)
        return self.docs_service, self.drive_service