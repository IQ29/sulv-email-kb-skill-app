#!/usr/bin/env python3
"""
Test script for 100 emails and attachments with KB + SULV economised skill.
This simulates the workflow without requiring actual Google API access.
"""

import os
import json
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailAttachmentSimulator:
    """Simulates email and attachment generation for testing."""
    
    def __init__(self, output_dir: str = './test_data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / 'emails').mkdir(exist_ok=True)
        (self.output_dir / 'attachments').mkdir(exist_ok=True)
        (self.output_dir / 'kb_processed').mkdir(exist_ok=True)
        
        logger.info(f"Test data will be saved to: {self.output_dir}")
    
    def generate_random_string(self, length: int = 10) -> str:
        """Generate random string for test data."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def generate_email(self, email_id: int) -> dict:
        """Generate a simulated email."""
        subjects = [
            "SULV Project Update",
            "Build Progress Report",
            "Client Meeting Notes",
            "Design Review Feedback",
            "Budget Approval Request",
            "Site Inspection Photos",
            "Contract Amendment",
            "Team Weekly Summary",
            "Risk Assessment Report",
            "Quality Control Checklist"
        ]
        
        senders = [
            "admin_auto@sulv.com.au",
            "project.manager@sulv.com.au",
            "design.team@sulv.com.au",
            "construction@sulv.com.au",
            "client.relations@sulv.com.au"
        ]
        
        # Generate random date in last 30 days
        days_ago = random.randint(0, 30)
        email_date = datetime.now() - timedelta(days=days_ago)
        
        email = {
            'id': f'test_email_{email_id:03d}',
            'threadId': f'test_thread_{random.randint(1, 20):03d}',
            'labelIds': ['INBOX', 'UNREAD'],
            'snippet': f'This is a test email snippet for email {email_id}',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': random.choice(senders)},
                    {'name': 'To', 'value': 'recipient@sulv.com.au'},
                    {'name': 'Subject', 'value': f'{random.choice(subjects)} #{email_id}'},
                    {'name': 'Date', 'value': email_date.strftime('%a, %d %b %Y %H:%M:%S %z')}
                ],
                'body': {
                    'data': f'This is the body of test email {email_id}. It contains important information about SULV project activities.'
                }
            },
            'sizeEstimate': random.randint(1024, 51200),  # 1KB to 50KB
            'internalDate': str(int(email_date.timestamp() * 1000))
        }
        
        return email
    
    def generate_attachment(self, email_id: int, attachment_num: int) -> dict:
        """Generate simulated attachment metadata."""
        file_types = [
            {'ext': 'pdf', 'type': 'application/pdf', 'desc': 'Document'},
            {'ext': 'jpg', 'type': 'image/jpeg', 'desc': 'Photo'},
            {'ext': 'png', 'type': 'image/png', 'desc': 'Diagram'},
            {'ext': 'docx', 'type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'desc': 'Word Document'},
            {'ext': 'xlsx', 'type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'desc': 'Spreadsheet'}
        ]
        
        file_type = random.choice(file_types)
        file_size = random.randint(1024, 10485760)  # 1KB to 10MB
        
        attachment = {
            'attachmentId': f'attachment_{email_id:03d}_{attachment_num:02d}',
            'filename': f'sulv_document_{email_id:03d}_{attachment_num:02d}.{file_type["ext"]}',
            'mimeType': file_type['type'],
            'size': file_size,
            'description': f'{file_type["desc"]} for email {email_id}'
        }
        
        return attachment
    
    def create_test_files(self, num_emails: int = 100, max_attachments_per_email: int = 3):
        """Create test email and attachment files."""
        logger.info(f"Generating {num_emails} test emails...")
        
        all_emails = []
        total_attachments = 0
        
        for i in range(1, num_emails + 1):
            # Generate email
            email = self.generate_email(i)
            
            # Generate attachments (0-3 per email)
            num_attachments = random.randint(0, max_attachments_per_email)
            attachments = []
            
            for j in range(1, num_attachments + 1):
                attachment = self.generate_attachment(i, j)
                attachments.append(attachment)
                
                # Create dummy attachment file
                attachment_file = self.output_dir / 'attachments' / attachment['filename']
                with open(attachment_file, 'wb') as f:
                    # Write random bytes to simulate file content
                    f.write(os.urandom(min(attachment['size'], 1024)))  # Max 1KB for test
            
            # Add attachments to email metadata
            if attachments:
                email['attachments'] = attachments
                total_attachments += len(attachments)
            
            # Save email metadata
            email_file = self.output_dir / 'emails' / f'{email["id"]}.json'
            with open(email_file, 'w') as f:
                json.dump(email, f, indent=2)
            
            all_emails.append(email)
            
            if i % 10 == 0:
                logger.info(f"Generated {i}/{num_emails} emails...")
        
        # Save summary
        summary = {
            'test_run': {
                'timestamp': datetime.now().isoformat(),
                'num_emails': num_emails,
                'total_attachments': total_attachments,
                'output_dir': str(self.output_dir)
            },
            'email_ids': [email['id'] for email in all_emails]
        }
        
        summary_file = self.output_dir / 'test_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Test data generation complete!")
        logger.info(f"- Emails: {num_emails}")
        logger.info(f"- Attachments: {total_attachments}")
        logger.info(f"- Data saved to: {self.output_dir}")
        
        return summary

class KBIntegrationTester:
    """Tests integration with Enterprise Knowledge Base."""
    
    def __init__(self, data_dir: str = './test_data'):
        self.data_dir = Path(data_dir)
        
    def simulate_kb_processing(self):
        """Simulate KB processing of emails and attachments."""
        logger.info("Simulating KB processing...")
        
        emails_dir = self.data_dir / 'emails'
        attachments_dir = self.data_dir / 'attachments'
        output_dir = self.data_dir / 'kb_processed'
        
        # Process each email
        processed_count = 0
        for email_file in emails_dir.glob('*.json'):
            try:
                with open(email_file, 'r') as f:
                    email_data = json.load(f)
                
                # Simulate KB extraction
                kb_entry = {
                    'source': 'email',
                    'email_id': email_data['id'],
                    'extracted_date': datetime.now().isoformat(),
                    'metadata': {
                        'sender': next((h['value'] for h in email_data['payload']['headers'] if h['name'] == 'From'), ''),
                        'subject': next((h['value'] for h in email_data['payload']['headers'] if h['name'] == 'Subject'), ''),
                        'date': next((h['value'] for h in email_data['payload']['headers'] if h['name'] == 'Date'), '')
                    },
                    'content_summary': email_data['payload']['body']['data'][:200] + '...',
                    'attachments': email_data.get('attachments', [])
                }
                
                # Save KB entry
                kb_file = output_dir / f'kb_{email_data["id"]}.json'
                with open(kb_file, 'w') as f:
                    json.dump(kb_entry, f, indent=2)
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {email_file}: {e}")
        
        logger.info(f"KB processing complete! Processed {processed_count} emails.")
        return processed_count

def run_comprehensive_test():
    """Run the complete test workflow."""
    print("=" * 60)
    print("SULV Email + KB Integration Test")
    print("=" * 60)
    
    # Step 1: Generate test data
    print("\n1. Generating test data...")
    simulator = EmailAttachmentSimulator()
    summary = simulator.create_test_files(num_emails=100)
    
    # Step 2: Simulate KB processing
    print("\n2. Simulating KB integration...")
    kb_tester = KBIntegrationTester()
    processed = kb_tester.simulate_kb_processing()
    
    # Step 3: Generate test report
    print("\n3. Generating test report...")
    report = {
        'test_name': 'SULV Email + KB Integration Test',
        'timestamp': datetime.now().isoformat(),
        'summary': summary['test_run'],
        'kb_processing': {
            'emails_processed': processed,
            'kb_entries_created': processed
        },
        'test_files': {
            'emails': str(simulator.output_dir / 'emails'),
            'attachments': str(simulator.output_dir / 'attachments'),
            'kb_processed': str(simulator.output_dir / 'kb_processed'),
            'summary': str(simulator.output_dir / 'test_summary.json')
        },
        'verification': {
            'email_count': summary['test_run']['num_emails'],
            'attachment_count': summary['test_run']['total_attachments'],
            'kb_entries': processed,
            'status': 'PASS' if processed == summary['test_run']['num_emails'] else 'PARTIAL'
        }
    }
    
    # Save report
    report_file = simulator.output_dir / 'test_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print(f"\nTest Results:")
    print(f"- Emails generated: {summary['test_run']['num_emails']}")
    print(f"- Attachments generated: {summary['test_run']['total_attachments']}")
    print(f"- KB entries created: {processed}")
    print(f"- Status: {report['verification']['status']}")
    print(f"\nData location: {simulator.output_dir}")
    print(f"Report: {report_file}")
    
    return report

if __name__ == "__main__":
    run_comprehensive_test()