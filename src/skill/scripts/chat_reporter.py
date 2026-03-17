#!/usr/bin/env python3
"""
SULV Chat Reporter Script
Posts reports and updates to Google Chat spaces.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.hybrid_backend import GoogleWorkspaceHybrid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/chat_reporter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatReporter:
    """Manages posting reports to Google Chat spaces."""
    
    def __init__(self):
        self.hybrid = GoogleWorkspaceHybrid()
        
        # Check if Chat is available (requires google-workspace)
        if not self.hybrid.backend_status['google-workspace']:
            raise RuntimeError("Google Chat requires google-workspace MCP, which is not available")
        
        logger.info("ChatReporter initialized")
    
    def post_report(self, space_id: str, report_text: str, thread_key: str = None) -> Dict[str, Any]:
        """
        Post a report to a Google Chat space.
        
        Args:
            space_id: Google Chat space ID (e.g., "spaces/xxx")
            report_text: Report content to post
            thread_key: Optional thread key to reply to existing thread
        
        Returns:
            Result of the post operation
        """
        logger.info(f"Posting report to space: {space_id}")
        
        # Format the report with header
        formatted_report = self._format_report(report_text)
        
        # Send message via hybrid backend
        result = self.hybrid.send_chat_message(space_id, formatted_report)
        
        if result:
            logger.info("Report posted successfully")
            return {
                'success': True,
                'space_id': space_id,
                'timestamp': datetime.now().isoformat()
            }
        else:
            logger.error("Failed to post report")
            return {
                'success': False,
                'error': 'Failed to send message',
                'space_id': space_id
            }
    
    def post_daily_report(self, space_id: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post a formatted daily report.
        
        Args:
            space_id: Google Chat space ID
            report_data: Dictionary with report sections
        
        Returns:
            Result of the post operation
        """
        report_text = self._build_daily_report(report_data)
        return self.post_report(space_id, report_text)
    
    def post_weekly_summary(self, space_id: str, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post a weekly summary report."""
        report_text = self._build_weekly_summary(summary_data)
        return self.post_report(space_id, report_text)
    
    def _format_report(self, report_text: str) -> str:
        """Format report with header."""
        header = f"📊 *SULV Build Report*\n"
        header += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        header += "─" * 30 + "\n\n"
        
        return header + report_text
    
    def _build_daily_report(self, data: Dict[str, Any]) -> str:
        """Build formatted daily report."""
        lines = [
            f"📋 *Daily Report: {data.get('date', datetime.now().strftime('%Y-%m-%d'))}*",
            "",
            "📈 *Key Metrics:*",
        ]
        
        # Add metrics
        metrics = data.get('metrics', {})
        for key, value in metrics.items():
            lines.append(f"  • {key}: {value}")
        
        # Add highlights
        highlights = data.get('highlights', [])
        if highlights:
            lines.extend(["", "✅ *Highlights:*"])
            for item in highlights:
                lines.append(f"  • {item}")
        
        # Add issues
        issues = data.get('issues', [])
        if issues:
            lines.extend(["", "⚠️ *Issues:*"])
            for item in issues:
                lines.append(f"  • {item}")
        
        # Add next steps
        next_steps = data.get('next_steps', [])
        if next_steps:
            lines.extend(["", "🎯 *Next Steps:*"])
            for item in next_steps:
                lines.append(f"  • {item}")
        
        return "\n".join(lines)
    
    def _build_weekly_summary(self, data: Dict[str, Any]) -> str:
        """Build formatted weekly summary."""
        lines = [
            f"📊 *Weekly Summary: {data.get('week', 'Week')}*",
            "",
            "📈 *Overall Progress:*",
        ]
        
        # Add progress items
        progress = data.get('progress', [])
        for item in progress:
            lines.append(f"  • {item}")
        
        # Add completed items
        completed = data.get('completed', [])
        if completed:
            lines.extend(["", "✅ *Completed:*"])
            for item in completed:
                lines.append(f"  • {item}")
        
        # Add upcoming items
        upcoming = data.get('upcoming', [])
        if upcoming:
            lines.extend(["", "📅 *Upcoming:*"])
            for item in upcoming:
                lines.append(f"  • {item}")
        
        return "\n".join(lines)
    
    def load_report_from_file(self, file_path: str) -> str:
        """Load report content from file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Report file not found: {file_path}")
        
        with open(path, 'r') as f:
            return f.read()
    
    def load_report_from_json(self, file_path: str) -> Dict[str, Any]:
        """Load report data from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        with open(path, 'r') as f:
            return json.load(f)

def main():
    parser = argparse.ArgumentParser(
        description='SULV Chat Reporter - Post reports to Google Chat spaces',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Post a simple text report
  python chat_reporter.py --space "spaces/xxx" --text "Daily report: All systems operational"
  
  # Post report from file
  python chat_reporter.py --space "spaces/xxx" --file ./reports/daily_report.md
  
  # Post daily report from JSON data
  python chat_reporter.py --space "spaces/xxx" --daily-json ./data/daily_report.json
  
  # Post weekly summary from JSON data
  python chat_reporter.py --space "spaces/xxx" --weekly-json ./data/weekly_summary.json
        """
    )
    
    parser.add_argument('--space', '-s', required=True,
                        help='Google Chat space ID (e.g., "spaces/xxx")')
    parser.add_argument('--text', '-t',
                        help='Report text to post directly')
    parser.add_argument('--file', '-f',
                        help='Path to report file (markdown or text)')
    parser.add_argument('--daily-json',
                        help='Path to JSON file with daily report data')
    parser.add_argument('--weekly-json',
                        help='Path to JSON file with weekly summary data')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Validate arguments
    input_methods = [args.text, args.file, args.daily_json, args.weekly_json]
    if sum(1 for m in input_methods if m is not None) != 1:
        parser.error("Please provide exactly one input method: --text, --file, --daily-json, or --weekly-json")
    
    try:
        # Initialize reporter
        reporter = ChatReporter()
        
        print(f"Posting report to space: {args.space}")
        print("-" * 50)
        
        # Determine report type and post
        if args.text:
            result = reporter.post_report(args.space, args.text)
        
        elif args.file:
            report_text = reporter.load_report_from_file(args.file)
            result = reporter.post_report(args.space, report_text)
        
        elif args.daily_json:
            report_data = reporter.load_report_from_json(args.daily_json)
            result = reporter.post_daily_report(args.space, report_data)
        
        elif args.weekly_json:
            summary_data = reporter.load_report_from_json(args.weekly_json)
            result = reporter.post_weekly_summary(args.space, summary_data)
        
        # Print result
        print("\n" + "=" * 50)
        print("POST RESULT")
        print("=" * 50)
        print(f"Success: {result['success']}")
        print(f"Space ID: {result['space_id']}")
        print(f"Timestamp: {result.get('timestamp', 'N/A')}")
        
        if not result['success']:
            print(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        print("\n✓ Report posted successfully!")
        
    except RuntimeError as e:
        logger.error(f"Initialization error: {e}")
        print(f"\n✗ Error: {e}")
        print("\nPlease ensure google-workspace MCP is configured:")
        print("  mcporter config add google-workspace --command \"npx\" --arg \"-y\" --arg \"@presto-ai/google-workspace-mcp\"")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()