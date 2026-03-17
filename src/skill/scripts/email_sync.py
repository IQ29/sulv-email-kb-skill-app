#!/usr/bin/env python3
"""
SULV Email Synchronization Script
Downloads emails and attachments from Gmail with hybrid backend support.
"""

import os
import sys
import json
import argparse
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.hybrid_backend import GoogleWorkspaceHybrid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmailSyncManager:
    """Manages email synchronization with attachment downloads."""
    
    def __init__(self, output_dir: str = './data/emails', account: str = ''):
        self.hybrid = GoogleWorkspaceHybrid()
        self.output_dir = Path(output_dir)
        self.account = account
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / 'attachments').mkdir(exist_ok=True)
        (self.output_dir / 'metadata').mkdir(exist_ok=True)
        
        logger.info(f"EmailSyncManager initialized. Output: {self.output_dir}")
    
    def sync_emails(self, query: str, max_results: int = 100, download_attachments: bool = True) -> Dict[str, Any]:
        """
        Sync emails matching query.
        
        Args:
            query: Gmail search query (e.g., "from:admin@sulv.com newer_than:1d")
            max_results: Maximum emails to fetch
            download_attachments: Whether to download attachments
        
        Returns:
            Summary of sync operation
        """
        logger.info(f"Starting email sync. Query: {query}, Max: {max_results}")
        
        # Search emails using hybrid backend
        search_result = self.hybrid.search_emails(query, max_results, self.account)
        
        if not search_result:
            logger.error("Email search failed")
            return {'success': False, 'error': 'Search failed', 'emails_synced': 0}
        
        # Extract message list
        messages = search_result.get('messages', [])
        if not messages:
            logger.info("No emails found matching query")
            return {'success': True, 'emails_synced': 0, 'attachments_downloaded': 0}
        
        logger.info(f"Found {len(messages)} emails")
        
        # Process each email
        synced_count = 0
        attachment_count = 0
        errors = []
        
        for msg in messages:
            try:
                result = self._process_email(msg, download_attachments)
                if result['success']:
                    synced_count += 1
                    attachment_count += result.get('attachments', 0)
            except Exception as e:
                logger.error(f"Error processing email {msg.get('id')}: {e}")
                errors.append({'message_id': msg.get('id'), 'error': str(e)})
        
        summary = {
            'success': True,
            'emails_synced': synced_count,
            'attachments_downloaded': attachment_count,
            'errors': errors,
            'query': query,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save summary
        summary_file = self.output_dir / 'metadata' / f'sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Sync complete. Emails: {synced_count}, Attachments: {attachment_count}")
        return summary
    
    def _process_email(self, message: Dict[str, Any], download_attachments: bool) -> Dict[str, Any]:
        """Process a single email."""
        msg_id = message.get('id')
        logger.debug(f"Processing email: {msg_id}")
        
        # Get full message details
        # Note: This would need to be implemented based on backend
        # For now, we'll save the metadata we have
        
        # Save email metadata
        email_file = self.output_dir / 'metadata' / f'{msg_id}.json'
        with open(email_file, 'w') as f:
            json.dump(message, f, indent=2)
        
        result = {
            'success': True,
            'message_id': msg_id,
            'attachments': 0
        }
        
        # Download attachments if requested
        if download_attachments:
            # This would require getting full message details
            # and extracting attachments
            # Placeholder for now
            pass
        
        return result
    
    def get_synced_emails(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get list of previously synced emails."""
        metadata_dir = self.output_dir / 'metadata'
        emails = []
        
        for json_file in metadata_dir.glob('*.json'):
            if json_file.name.startswith('sync_'):
                continue  # Skip summary files
            
            try:
                with open(json_file, 'r') as f:
                    email_data = json.load(f)
                    emails.append(email_data)
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")
        
        return emails
    
    def export_to_json(self, output_file: str = None) -> str:
        """Export all synced emails to a single JSON file."""
        if output_file is None:
            output_file = self.output_dir / f'emails_export_{datetime.now().strftime("%Y%m%d")}.json'
        
        emails = self.get_synced_emails()
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_emails': len(emails),
            'emails': emails
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(emails)} emails to {output_file}")
        return str(output_file)

def main():
    parser = argparse.ArgumentParser(
        description='SULV Email Synchronization Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync last 24 hours
  python email_sync.py --query "newer_than:1d"
  
  # Sync from specific sender with attachments
  python email_sync.py --query "from:admin@sulv.com" --download-attachments
  
  # Sync with custom output directory
  python email_sync.py --query "label:SULV-Build" --output-dir ./build_emails
  
  # Sync specific account
  python email_sync.py --query "newer_than:7d" --account admin_auto@sulv.com.au
        """
    )
    
    parser.add_argument('--query', '-q', required=True,
                        help='Gmail search query (e.g., "newer_than:1d from:admin@sulv.com")')
    parser.add_argument('--max-results', '-m', type=int, default=100,
                        help='Maximum number of emails to sync (default: 100)')
    parser.add_argument('--download-attachments', '-a', action='store_true',
                        help='Download email attachments')
    parser.add_argument('--output-dir', '-o', default='./data/emails',
                        help='Output directory for synced emails (default: ./data/emails)')
    parser.add_argument('--account', default='',
                        help='Gmail account to use (for gog backend)')
    parser.add_argument('--export-json', action='store_true',
                        help='Export all synced emails to JSON after sync')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Initialize sync manager
    sync_manager = EmailSyncManager(
        output_dir=args.output_dir,
        account=args.account
    )
    
    # Check backend availability
    status = sync_manager.hybrid.get_backend_status()
    if not (status['google-workspace'] or status['gog']):
        logger.error("No Google Workspace backends available!")
        logger.error("Please set up google-workspace MCP or gog CLI")
        sys.exit(1)
    
    print(f"Backends available: {status}")
    
    # Run sync
    print(f"\nSyncing emails with query: {args.query}")
    print(f"Max results: {args.max_results}")
    print(f"Download attachments: {args.download_attachments}")
    print(f"Output directory: {args.output_dir}")
    print("-" * 50)
    
    result = sync_manager.sync_emails(
        query=args.query,
        max_results=args.max_results,
        download_attachments=args.download_attachments
    )
    
    # Print summary
    print("\n" + "=" * 50)
    print("SYNC SUMMARY")
    print("=" * 50)
    print(f"Success: {result['success']}")
    print(f"Emails synced: {result['emails_synced']}")
    print(f"Attachments downloaded: {result.get('attachments_downloaded', 0)}")
    
    if result.get('errors'):
        print(f"Errors: {len(result['errors'])}")
        for error in result['errors'][:5]:  # Show first 5 errors
            print(f"  - {error['message_id']}: {error['error']}")
    
    # Export to JSON if requested
    if args.export_json and result['success']:
        export_file = sync_manager.export_to_json()
        print(f"\nExported to: {export_file}")
    
    if 'timestamp' in result:
        print(f"\nTimestamp: {result['timestamp']}")
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()