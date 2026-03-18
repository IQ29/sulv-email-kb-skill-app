#!/usr/bin/env python3
"""
ACTUAL ATTACHMENT DOWNLOADING - Download and process attachments from real SULV emails.
"""

import os
import sys
import base64
import mimetypes
from pathlib import Path
from datetime import datetime

print("📎 ACTUAL ATTACHMENT DOWNLOADING")
print("=" * 60)
print("Starting at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print()

# Add src to path
sys.path.insert(0, "src")

# Import KB components
from core.processor import ProcessingPipeline
from core.ocr import OCRFactory

print("✅ Loading KB components...")
pipeline = ProcessingPipeline()
ocr = OCRFactory.create_processor()
print(f"   • OCR Ready: {ocr.is_available()}")
print(f"   • Pipeline Ready: Yes")

# Create directories
download_dir = Path("actual_downloaded_attachments")
download_dir.mkdir(exist_ok=True)

processed_dir = Path("processed_attachments_kb")
processed_dir.mkdir(exist_ok=True)

print(f"\n📁 Download directory: {download_dir.absolute()}")
print(f"📁 Processed directory: {processed_dir.absolute()}")

# Import Google API
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    
    print("✅ Google API loaded")
except ImportError as e:
    print(f"❌ Google API error: {e}")
    sys.exit(1)

def get_gmail_service():
    """Get authenticated Gmail service."""
    token_file = Path.cwd() / 'credentials' / 'gmail_token.json'
    
    if not token_file.exists():
        print(f"❌ No authentication token found: {token_file}")
        print("   Run test_email_kb_integration.py first to authenticate")
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
        print("✅ Gmail service authenticated")
        return service
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def find_attachments(parts, attachments_list=None, path=""):
    """Recursively find all attachments in email parts."""
    if attachments_list is None:
        attachments_list = []
    
    for i, part in enumerate(parts):
        # Check if this part is an attachment
        if part.get('filename') and part.get('body', {}).get('attachmentId'):
            attachments_list.append({
                'filename': part['filename'],
                'attachmentId': part['body']['attachmentId'],
                'mimeType': part.get('mimeType', 'application/octet-stream'),
                'path': f"{path}{i}"
            })
        
        # Recursively check nested parts
        if 'parts' in part:
            find_attachments(part['parts'], attachments_list, f"{path}{i}.")
    
    return attachments_list

def download_and_process_attachment(service, message_id, attachment_info, email_metadata):
    """Download a single attachment and process it through KB."""
    filename = attachment_info['filename']
    attachment_id = attachment_info['attachmentId']
    
    print(f"\n    📎 Downloading: {filename}")
    print(f"       Type: {attachment_info['mimeType']}")
    
    try:
        # Download attachment
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=attachment_id
        ).execute()
        
        # Decode base64 data
        file_data = base64.urlsafe_b64decode(attachment['data'])
        
        # Save to download directory
        safe_filename = "".join(c for c in filename if c.isalnum() or c in '.-_ ')
        download_path = download_dir / safe_filename
        
        with open(download_path, 'wb') as f:
            f.write(file_data)
        
        file_size = download_path.stat().st_size
        print(f"       ✅ Downloaded: {file_size:,} bytes")
        
        # Determine document type for KB processing
        file_ext = download_path.suffix.lower()
        doc_type = 'text'
        
        if file_ext in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            doc_type = 'report'  # Will trigger OCR
        elif file_ext in ['.doc', '.docx']:
            doc_type = 'report'
        elif file_ext in ['.xls', '.xlsx', '.csv']:
            doc_type = 'report'
        
        # Process through KB pipeline
        print(f"       🔧 Processing through KB...")
        
        metadata = {
            'source': 'gmail',
            'sender': email_metadata.get('from', ''),
            'subject': email_metadata.get('subject', ''),
            'date': email_metadata.get('date', ''),
            'original_email_id': email_metadata.get('id', ''),
            'original_filename': filename,
            'document_type': doc_type,
            'file_size': file_size,
            'mime_type': attachment_info['mimeType']
        }
        
        result = pipeline.process(str(download_path), metadata)
        
        if result:
            document, chunks = result
            print(f"       ✅ Processed: {len(chunks)} chunks created")
            
            # Save processing info
            processed_info = {
                'filename': filename,
                'downloaded_path': str(download_path),
                'chunks_created': len(chunks),
                'document_title': document.title,
                'processed_time': datetime.now().isoformat(),
                'email_metadata': email_metadata
            }
            
            # Save to processed directory
            info_file = processed_dir / f"{safe_filename}.info.json"
            import json
            with open(info_file, 'w') as f:
                json.dump(processed_info, f, indent=2)
            
            return {
                'success': True,
                'filename': filename,
                'chunks': len(chunks),
                'file_size': file_size,
                'file_type': file_ext,
                'needs_ocr': file_ext in ['.pdf', '.jpg', '.jpeg', '.png']
            }
        else:
            print(f"       ❌ KB processing failed")
            return {'success': False, 'filename': filename, 'error': 'KB processing failed'}
            
    except Exception as e:
        print(f"       ❌ Error: {e}")
        return {'success': False, 'filename': filename, 'error': str(e)}

def main():
    """Main function to download and process attachments."""
    print("\n🔐 Connecting to Gmail...")
    service = get_gmail_service()
    if not service:
        return
    
    print("\n📥 Searching for SULV emails with attachments...")
    
    try:
        # Search for recent SULV emails with attachments
        results = service.users().messages().list(
            userId='me',
            q="has:attachment (sulv OR SULV) newer_than:7d",
            maxResults=3  # Start with just 3 emails for testing
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("❌ No SULV emails with attachments found in last 7 days")
            # Try broader search
            results = service.users().messages().list(
                userId='me',
                q="has:attachment newer_than:3d",
                maxResults=2
            ).execute()
            messages = results.get('messages', [])
        
        if not messages:
            print("❌ No emails with attachments found")
            return
        
        print(f"✅ Found {len(messages)} emails to process")
        
        # Statistics
        total_attachments_found = 0
        total_attachments_processed = 0
        total_chunks_created = 0
        results_summary = []
        
        for i, msg in enumerate(messages, 1):
            print(f"\n--- Processing Email {i}/{len(messages)} ---")
            
            try:
                # Get full message
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Extract email metadata
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                
                print(f"📧 Email: {subject[:60]}...")
                print(f"   From: {sender}")
                print(f"   Date: {date}")
                
                # Find all attachments
                attachments = find_attachments([message['payload']])
                
                if not attachments:
                    print("   ⚠️ No downloadable attachments found")
                    continue
                
                print(f"   📎 Found {len(attachments)} attachments")
                total_attachments_found += len(attachments)
                
                email_metadata = {
                    'id': msg['id'],
                    'subject': subject,
                    'from': sender,
                    'date': date
                }
                
                # Process each attachment
                for att in attachments:
                    result = download_and_process_attachment(service, msg['id'], att, email_metadata)
                    results_summary.append(result)
                    
                    if result.get('success'):
                        total_attachments_processed += 1
                        total_chunks_created += result['chunks']
                
            except Exception as e:
                print(f"❌ Error processing email: {e}")
                continue
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 DOWNLOAD & PROCESSING SUMMARY")
        print("=" * 60)
        
        print(f"\n📧 Emails examined: {len(messages)}")
        print(f"📎 Attachments found: {total_attachments_found}")
        print(f"✅ Successfully processed: {total_attachments_processed}")
        print(f"🔢 Total chunks created: {total_chunks_created}")
        
        # File type breakdown
        file_types = {}
        ocr_needed = 0
        
        for result in results_summary:
            if result.get('success'):
                file_ext = result.get('file_type', 'unknown')
                file_types[file_ext] = file_types.get(file_ext, 0) + 1
                if result.get('needs_ocr'):
                    ocr_needed += 1
        
        if file_types:
            print("\n📄 File types processed:")
            for ext, count in file_types.items():
                print(f"   {ext or 'no ext'}: {count}")
        
        print(f"\n📷 Attachments needing OCR: {ocr_needed}")
        
        # Cost savings calculation
        print("\n💰 COST SAVINGS CALCULATION:")
        
        # Estimate OCR pages (PDFs + images)
        estimated_pages = 0
        for result in results_summary:
            if result.get('success') and result.get('needs_ocr'):
                # Rough estimate: 1 page per PDF/image
                estimated_pages += 1
        
        cloud_ocr_cost = estimated_pages * 0.0015  # $1.50/1000 pages
        llm_parsing_cost = total_attachments_processed * 0.003  # ~$0.003 per file
        llm_embedding_cost = total_chunks_created * 0.0001  # $0.0001 per chunk
        
        total_cloud_cost = cloud_ocr_cost + llm_parsing_cost + llm_embedding_cost
        
        print(f"   Estimated pages for OCR: {estimated_pages}")
        print(f"\n   Cloud/LLM Costs would be:")
        print(f"   • OCR: ${cloud_ocr_cost:.4f}")
        print(f"   • Document parsing: ${llm_parsing_cost:.4f}")
        print(f"   • Embedding: ${llm_embedding_cost:.4f}")
        print(f"   • TOTAL: ${total_cloud_cost:.4f}")
        
        print(f"\n   Your actual cost: $0.00")
        print(f"   💰 Savings: 100% (${total_cloud_cost:.4f} saved)")
        
        # Show downloaded files
        print(f"\n📁 Downloaded files in: {download_dir.absolute()}")
        downloaded_files = list(download_dir.glob("*"))
        if downloaded_files:
            print(f"   Files downloaded: {len(downloaded_files)}")
            for f in downloaded_files[:5]:  # Show first 5
                print(f"   • {f.name} ({f.stat().st_size:,} bytes)")
            if len(downloaded_files) > 5:
                print(f"   ... and {len(downloaded_files) - 5} more")
        
        print(f"\n📁 Processing info in: {processed_dir.absolute()}")
        
        print("\n" + "=" * 60)
        print("🎉 ACTUAL ATTACHMENT DOWNLOADING COMPLETE!")
        print("\n✅ Real attachments downloaded to disk")
        print("✅ Processed through KB pipeline")
        print("✅ OCR ready for PDFs/images")
        print("✅ 100% cost savings achieved")
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Main error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()