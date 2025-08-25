# Smart Email Response System

A streamlined email automation system that scans your gmail for pending work, extracts completed work from your google docs and sends the update!

## ✨ What It Does

1. **🔍 Intelligent Email Scanning** - Portia AI scans your recent Gmail for document requests
2. **📄 Smart Document Detection** - Finds Google Docs marked as "Done" 
3. **🧠 AI-Powered Matching** - Intelligently matches completed documents to email requests
4. **✨ Professional Responses** - Generates summaries, creates PDFs, and sends threaded replies
5. **📧 Full Transparency** - CC's you on all responses so you know what was sent

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env with your Portia API key and email
```

### 3. Run the System
```bash
python portia_main.py
```

## 📋 Configuration

Only two required settings in your `.env` file:

- `PORTIA_API_KEY` - Your Portia AI API key from [portia.ai](https://portia.ai)
- `USER_EMAIL` - Your Gmail address for CC notifications

## 🎯 How It Works

The system uses Portia AI's native cloud tools to:

- **Gmail Integration** - Portia handles OAuth and email operations
- **Google Docs Access** - Built-in document scanning and PDF generation  
- **AI Intelligence** - Natural language processing for smart matching
- **Email Threading** - Proper reply threading and conversation management

## 🔄 Workflow

1. Portia scans your recent Gmail messages for document requests
2. Checks your Google Docs for documents with "Done" in the title
3. Uses AI to intelligently match completed docs to email requests
4. Generates professional summaries and converts docs to PDF
5. Sends threaded reply emails with attachments and CC's you

## 🛠 Advanced Usage

The system is powered by a single natural language task that Portia AI executes. You can modify the task in `portia_main.py` to customize the behavior.

## 📚 Learn More

- [Portia AI Documentation](https://docs.portia.ai)
- [Example Projects](https://github.com/portia-ai/portia-agent-examples)

---

**Powered by Portia AI** - The future of intelligent automation is here! 🤖✨
