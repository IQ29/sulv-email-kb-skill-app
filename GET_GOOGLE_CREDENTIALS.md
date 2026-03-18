# How to Get Google OAuth Credentials for Email Download

## 📋 Quick Summary

To download real emails, you need a `credentials.json` file from Google Cloud Console. Here's exactly how to get it:

## 🚀 Step-by-Step Guide

### **Step 1: Go to Google Cloud Console**
1. Open: https://console.cloud.google.com/
2. Sign in with your Google account (the one with the emails you want to download)

### **Step 2: Create or Select a Project**
1. Click the project dropdown at the top
2. Click "NEW PROJECT"
3. Name it: `SULV-Email-KB` (or similar)
4. Click "CREATE"

### **Step 3: Enable Gmail API**
1. In the left sidebar, click "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "ENABLE"

### **Step 4: Create OAuth 2.0 Credentials**
1. Go to "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. If prompted, configure consent screen:
   - User Type: "External"
   - App name: `SULV Email Knowledge Base`
   - User support email: Your email
   - Developer contact: Your email
   - Click "SAVE AND CONTINUE"
4. Back to creating OAuth client ID:
   - Application type: "Desktop app"
   - Name: `SULV Email KB Desktop`
   - Click "CREATE"

### **Step 5: Download Credentials**
1. Click the download icon (📥) next to your new OAuth client
2. Save as `credentials.json`
3. Place in **ANY** of these locations:
   - `~/Downloads/credentials.json` (Easiest!)
   - `~/Desktop/credentials.json`
   - `~/.credentials/credentials.json`
   - `sulv-unified-kb/credentials/credentials.json`

## 📁 Where to Save the File

**Easiest option:** Save to your Downloads folder:
```
/Users/oppeinqin/Downloads/credentials.json
```

**Project option:** Save in the KB project:
```
/Users/oppeinqin/Documents/trae_projects/Openclaw/temp_home/.openclaw/workspace/sulv-unified-kb/credentials/credentials.json
```

## 🔧 What the File Looks Like

The `credentials.json` file should look something like this:
```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

## 🚀 After Getting Credentials

Once you have `credentials.json`:

```bash
cd /Users/oppeinqin/Documents/trae_projects/Openclaw/temp_home/.openclaw/workspace/sulv-unified-kb
source venv/bin/activate
python test_email_kb_integration.py
```

The system will:
1. Find your credentials automatically
2. Open a browser for Google authentication
3. Download your latest 10 emails with attachments
4. Process them through the knowledge base
5. Enable semantic search across all emails

## ⚠️ Important Notes

1. **First time only:** You'll need to authenticate in browser and grant permissions
2. **Permissions:** The app needs "read-only" access to Gmail
3. **Security:** Credentials stay on your machine, no data sent to Google
4. **Cost:** $0.00 - All processing is local

## 🆘 Troubleshooting

**"Couldn't find credentials.json"**
- Check the file is in one of the locations above
- Make sure it's named exactly `credentials.json`
- Check file permissions: `ls -la ~/Downloads/credentials.json`

**Authentication fails**
- Make sure you enabled Gmail API
- Check you're using the correct Google account
- Try deleting `credentials/gmail_token.json` and restarting

**Browser doesn't open**
- Check terminal for a URL to copy/paste into browser
- Make sure you're logged into Google in your browser

## 📞 Need Help?

If you get stuck at any step, I can guide you through it. Just show me:
1. Which step you're on
2. Any error messages you see
3. Screenshots if possible

The system is 100% ready - we just need those credentials to start downloading real emails! 🎯