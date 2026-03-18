#!/usr/bin/env python3
"""
SIMPLE ATTACHMENT DOWNLOAD - Just download attachments first, then process.
"""

import os
import sys
import base64
from pathlib import Path
from datetime import datetime

print("⬇️  SIMPLE ATTACHMENT DOWNLOAD")
print("=" * 50)
print("Time:", datetime.now().strftime("%H:%M:%S"))
print()

# Import Google API
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    print("✅ Google API loaded")
except ImportError as e:
    print(f"❌ Google API error: {e}")
    sys.exit(1)

# Create download directory
download_dir = Path("attachments_downloaded")
download_dir.mkdir(exist_ok=True)
print(f"📁 Download to: {download_dir.absolute()}")

def get_gmail_service():
    """Get authenticated Gmail service."""
    token_file = Path.cwd() / 'credentials' / 'gmail_token.json'
    
    if not token_file.exists():
        print(f"❌ No token file: {token_file}")
        print("   Run: python test_email_kb_integration.py first")
        return None
    
    try:
        creds = Credentials.from_authorized_user_file(
            str(token_file),
            ['https://www.googleapis.com/auth/gmail.readonly']
        )
        
        if not creds.valid:
            print("❌ Credentials expired")
            return None
        
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail service ready")
        return service
        
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return None

def find_attachments_in_parts(parts, path=""):
    """Find attachments in email parts."""
    attachments = []
    
    for i, part in enumerate(parts):
        # Check if this part has an attachment
        filename = part.get('filename')
        attachment_id = part.get('body', {}).get('attachmentId')
        
        if filename and attachment_id:
            attachments.append({
                'filename': filename,
                'attachmentId': attachment_id,
                'mimeType': part.get('mimeType', ''),
                'part_path': f"{path}{i}"
            })
        
        # Check nested parts
        if 'parts' in part:
            nested = find_attachments_in_parts(part['parts'], f"{path}{i}.")
            attachments.extend(nested)
    
    return attachments

def download_attachment(service, message_id, attachment_info):
    """Download a single attachment."""
    filename = attachment_info['filename']
    
    print(f"  📎 {filename}")
    
    try:
        # Download from Gmail
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=attachment_info['attachmentId']
        ).execute()
        
        # Decode and save
        file_data = base64.urlsafe_b64decode(attachment['data'])
        
        # Clean filename
        safe_name = "".join(c for c in filename if c.isalnum() or c in '.-_ ')
        filepath = download_dir / safe_name
        
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        size = filepath.stat().st_size
        print(f"    ✅ {size:,} bytes")
        
        return {
            'success': True,
            'filename': filename,
            'saved_as': safe_name,
            'size': size,
            'path': str(filepath)
        }
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        return {
            'success': False,
            'filename': filename,
            'error': str(e)
        }

def main():
    """Main download function."""
    print("\n🔐 Connecting to Gmail...")
    service = get_gmail_service()
    if not service:
        return
    
    print("\n🔍 Searching for emails with attachments...")
    
    try:
        # Get recent emails with attachments
        results = service.users().messages().list(
            userId='me',
            q="has:attachment newer_than:2d",
            maxResults=2  # Just 2 emails for testing
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("❌ No emails found")
            return
        
        print(f"✅ Found {len(messages)} emails")
        
        all_results = []
        
        for i, msg in enumerate(messages, 1):
            print(f"\n--- Email {i} ---")
            
            try:
                # Get full message
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Get subject
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                print(f"Subject: {subject[:50]}...")
                
                # Find attachments
                attachments = find_attachments_in_parts([message['payload']])
                
                if not attachments:
                    print("  No attachments found")
                    continue
                
                print(f"  Attachments: {len(attachments)}")
                
                # Download each attachment
                for att in attachments:
                    result = download_attachment(service, msg['id'], att)
                    all_results.append(result)
                    
            except Exception as e:
                print(f"❌ Error with email: {e}")
                continue
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 DOWNLOAD SUMMARY")
        print("=" * 50)
        
        successful = [r for r in all_results if r['success']]
        failed = [r for r in all_results if not r['success']]
        
        print(f"\n✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        
        if successful:
            total_size = sum(r['size'] for r in successful)
            print(f"📦 Total downloaded: {total_size:,} bytes")
            
            print("\n📄 Files downloaded:")
            for r in successful:
                print(f"  • {r['filename']} ({r['size']:,} bytes)")
        
        if failed:
            print("\n⚠️ Failed downloads:")
            for r in failed:
                print(f"  • {r['filename']}: {r['error']}")
        
        # Show what's in the directory
        print(f"\n📁 Directory contents: {download_dir.absolute()}")
        files = list(download_dir.glob("*"))
        if files:
            for f in files:
                print(f"  • {f.name} ({f.stat().st_size:,} bytes)")
        else:
            print("  (empty)")
        
        print(f"\n⏰ Completed: {datetime.now().strftime('%H:%M:%S')}")
        
        # Next steps
        if successful:
            print("\n🚀 NEXT: Process downloaded files with KB:")
            print("   source venv/bin/activate")
            print("   python3 -c \"")
            print("   from core.processor import ProcessingPipeline")
            print("   pipeline = ProcessingPipeline()")
            print("   for file in ['attachments_downloaded/FILE1', 'attachments_downloaded/FILE2']:")
            print("       result = pipeline.process(file)")
            print("       print(f'Processed {file}: {len(result[1])} chunks')")
            print("   \"")
        
    except Exception as e:
        print(f"❌ Main error: {e}")

if __name__ == "__main__":
    main()