# Email Document Processing Agent with Portia AI

This project uses Portia AI to create an intelligent agent that automates email responses for completed documents. The agent monitors your Gmail inbox for emails requesting document updates, checks your Google Docs for completed work (marked with "Done"), and automatically sends responses with document summaries and PDF attachments.

## Features

🤖 **Intelligent Email Processing**: Uses Portia AI's multi-agent framework to orchestrate complex workflows

📧 **Gmail Integration**: Automatically reads and identifies emails requiring responses about pending documents

📄 **Google Docs Integration**: Scans your Google Docs for completed documents marked with "Done"

🔍 **Smart Document Matching**: Uses keyword analysis to match completed documents to relevant emails

📝 **AI-Powered Summarization**: Uses OpenAI to generate professional document summaries

📎 **Automatic PDF Generation**: Creates PDF versions of completed documents for email attachments

✉️ **Automated Email Responses**: Composes and sends professional response emails with summaries and attachments

## Prerequisites

Before setting up this project, you'll need:

1. **Python 3.8+** installed on your system
2. **Google Account** with Gmail and Google Drive enabled
3. **API Keys** for the following services:
   - Portia AI API key
   - OpenAI API key
   - Google OAuth2 credentials

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

1. Copy the environment template:
```bash
cp .env.template .env
```

2. Edit the `.env` file with your API keys and configuration:

```env
# Portia AI Configuration
PORTIA_API_KEY=your_portia_api_key_here

# OpenAI Configuration (for summarization)
OPENAI_API_KEY=your_openai_api_key_here

# Google API Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Email Configuration
USER_EMAIL=your_email@gmail.com
```

### 3. API Key Setup Guide

#### Portia AI API Key
1. Sign up at [Portia Labs](https://docs.portialabs.ai/)
2. Navigate to your dashboard and create an API key
3. Copy the key to your `.env` file

#### OpenAI API Key
1. Go to [OpenAI API](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key to your `.env` file

#### Google OAuth2 Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API and Google Docs API
4. Go to "Credentials" and create OAuth 2.0 client credentials
5. Choose "Desktop application" as the application type
6. Copy the Client ID and Client Secret to your `.env` file

### 4. Document Naming Convention

For the agent to identify completed documents, make sure your Google Docs titles end with "Done". For example:
- "Project Report Done"
- "Meeting Notes - Q3 Planning Done"
- "Research Analysis Done"

### 5. Email Keywords

The agent identifies emails requiring responses by looking for these keywords:
- "pending document"
- "document review" 
- "please review"
- "awaiting document"
- "document status"
- "completed work"
- "finished document"

You can modify these keywords in `config.py`.

## Usage

### Run the Complete Workflow

Execute the main workflow that processes all emails and documents:

```bash
python run_agent.py
```

### Run Individual Components

You can also test individual components:

```bash
# Test Gmail connection
python -c "from gmail_processor import GmailProcessor; gp = GmailProcessor(); gp.initialize(); print('Gmail connected!')"

# Test Google Docs connection  
python -c "from docs_processor import DocsProcessor; dp = DocsProcessor(); dp.initialize(); print('Google Docs connected!')"

# Run the full Portia agent
python portia_agent.py
```

## How It Works

### Workflow Steps

1. **Email Analysis**: The agent reads your recent Gmail messages and identifies emails containing keywords that suggest someone is asking about document status.

2. **Document Discovery**: Scans your Google Docs for documents with titles ending in "Done".

3. **Intelligent Matching**: Uses keyword analysis to match completed documents to relevant email requests.

4. **Content Processing**: 
   - Extracts the full text content from matched Google Docs
   - Uses OpenAI to generate professional summaries
   - Creates PDF versions of the documents

5. **Response Generation**: 
   - Uses OpenAI to compose appropriate response emails
   - Includes document summaries in the email body
   - Attaches the PDF version of the completed document

6. **Automated Sending**: Sends the response emails through Gmail API.

### File Structure

```
email-completed-work/
├── config.py                 # Configuration and settings
├── google_auth.py            # Google API authentication
├── gmail_processor.py        # Gmail reading and sending functionality
├── docs_processor.py         # Google Docs integration and PDF generation
├── document_processor.py     # AI-powered summarization and email composition
├── portia_agent.py          # Main Portia AI agent orchestration
├── run_agent.py             # Simple runner script
├── requirements.txt         # Python dependencies
├── .env.template           # Environment variables template
└── README.md               # This file
```

## Customization

### Modify Response Keywords

Edit the `RESPONSE_KEYWORDS` list in `config.py` to change which emails trigger responses:

```python
RESPONSE_KEYWORDS = [
    'pending document',
    'document review',
    # Add your custom keywords here
]
```

### Adjust Document Completion Marker

Change the completion marker from "Done" to something else in `config.py`:

```python
COMPLETION_MARKER = 'Finished'  # or 'Complete', 'Ready', etc.
```

### Customize Email Templates

Modify the email composition logic in `document_processor.py` to change how response emails are generated.

## Troubleshooting

### Common Issues

1. **Authentication Errors**: 
   - Make sure all API keys are correctly set in `.env`
   - For Google APIs, you may need to go through OAuth flow on first run

2. **No Emails Found**:
   - Check that your keywords match the actual content of emails
   - Verify the email account being accessed is correct

3. **No Documents Found**:
   - Ensure Google Docs titles end with the completion marker (default: "Done")
   - Verify Google Docs API is enabled and authenticated

4. **PDF Generation Issues**:
   - Make sure reportlab is properly installed
   - Check file permissions in the output directory

### Debug Mode

Add debug prints to track execution:

```python
# In any processor file, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Notes

- All API keys are stored in environment variables and should never be committed to version control
- Google OAuth tokens are stored locally in pickle files (automatically handled)
- The agent only reads emails and documents you have access to
- Email sending requires explicit OAuth permissions

## Contributing

Feel free to submit issues and enhancement requests! Key areas for improvement:
- Enhanced document matching algorithms
- Support for other document formats (Word, PDF, etc.)
- Integration with other email providers
- More sophisticated email classification
- Support for additional cloud storage providers

## License

This project is open source and available under the MIT License.

---

For support with Portia AI features, visit [Portia Labs Documentation](https://docs.portialabs.ai/).
