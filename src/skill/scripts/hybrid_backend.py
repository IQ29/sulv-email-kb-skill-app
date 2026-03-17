#!/usr/bin/env python3
"""
SULV Google Workspace Hybrid Backend
Combines google-workspace MCP and gog CLI with automatic fallback.
"""

import subprocess
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/hybrid_operations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GoogleWorkspaceHybrid:
    """Unified interface for Google Workspace operations with fallback."""
    
    def __init__(self, timeout_seconds: int = 30):
        self.timeout = timeout_seconds
        self.backend_status = {
            'google-workspace': self._check_google_workspace(),
            'gog': self._check_gog()
        }
        
        logger.info(f"Backend status: {self.backend_status}")
    
    def _check_google_workspace(self) -> bool:
        """Check if google-workspace MCP is available."""
        try:
            result = subprocess.run(
                ['mcporter', 'config', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return 'google-workspace' in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_gog(self) -> bool:
        """Check if gog CLI is available."""
        try:
            result = subprocess.run(
                ['which', 'gog'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    
    def _run_mcporter(self, tool: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute google-workspace MCP command."""
        if not self.backend_status['google-workspace']:
            return None
        
        # Build command
        cmd = ['mcporter', 'call', '--server', 'google-workspace', '--tool', tool]
        for key, value in params.items():
            if isinstance(value, bool):
                cmd.extend([f'--{key}', str(value).lower()])
            else:
                cmd.extend([f'--{key}', str(value)])
        
        try:
            logger.debug(f"Running mcporter: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {'output': result.stdout}
            else:
                logger.error(f"mcporter failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.warning(f"mcporter timeout for tool: {tool}")
            return None
        except Exception as e:
            logger.error(f"mcporter error: {e}")
            return None
    
    def _run_gog(self, service: str, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute gog CLI command."""
        if not self.backend_status['gog']:
            return None
        
        # Build command based on service and action
        if service == 'gmail' and action == 'search':
            query = params.get('query', '')
            max_results = params.get('maxResults', 10)
            account = params.get('account', '')
            
            cmd = ['gog', 'gmail', 'search', query, '--max', str(max_results), '--json']
            if account:
                cmd.extend(['--account', account])
        
        elif service == 'gmail' and action == 'send':
            # Handle email sending
            to = params.get('to', '')
            subject = params.get('subject', '')
            body = params.get('body', '')
            
            # Create temp file for body if needed
            if len(body) > 100:  # Long body, use file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(body)
                    body_file = f.name
                
                cmd = ['gog', 'gmail', 'send', '--to', to, '--subject', subject, '--body-file', body_file]
            else:
                cmd = ['gog', 'gmail', 'send', '--to', to, '--subject', subject, '--body', body]
        
        elif service == 'drive' and action == 'search':
            query = params.get('query', '')
            max_results = params.get('maxResults', 10)
            cmd = ['gog', 'drive', 'search', query, '--max', str(max_results), '--json']
        
        else:
            logger.warning(f"Unsupported gog action: {service}.{action}")
            return None
        
        try:
            logger.debug(f"Running gog: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {'output': result.stdout}
            else:
                logger.error(f"gog failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.warning(f"gog timeout for {service}.{action}")
            return None
        except Exception as e:
            logger.error(f"gog error: {e}")
            return None
    
    # Public API Methods
    
    def get_chat_messages(self, space_id: str, max_results: int = 50) -> Optional[Dict[str, Any]]:
        """Get messages from Google Chat space (google-workspace only)."""
        logger.info(f"Getting chat messages from space: {space_id}")
        return self._run_mcporter('chat.getMessages', {
            'spaceId': space_id,
            'maxResults': max_results
        })
    
    def send_chat_message(self, space_id: str, text: str) -> Optional[Dict[str, Any]]:
        """Send message to Google Chat space (google-workspace only)."""
        logger.info(f"Sending chat message to space: {space_id}")
        return self._run_mcporter('chat.sendMessage', {
            'spaceId': space_id,
            'text': text
        })
    
    def search_emails(self, query: str, max_results: int = 100, account: str = '') -> Optional[Dict[str, Any]]:
        """
        Search emails with fallback.
        Primary: google-workspace, Fallback: gog
        """
        logger.info(f"Searching emails with query: {query}")
        
        # Try google-workspace first
        result = self._run_mcporter('gmail.search', {
            'query': query,
            'maxResults': max_results
        })
        
        if result is not None:
            logger.info("Email search succeeded via google-workspace")
            return result
        
        # Fallback to gog
        logger.info("Falling back to gog for email search")
        result = self._run_gog('gmail', 'search', {
            'query': query,
            'maxResults': max_results,
            'account': account
        })
        
        if result is not None:
            logger.info("Email search succeeded via gog (fallback)")
        
        return result
    
    def send_email(self, to: str, subject: str, body: str) -> Optional[Dict[str, Any]]:
        """
        Send email with fallback.
        Primary: google-workspace, Fallback: gog
        """
        logger.info(f"Sending email to: {to}, subject: {subject}")
        
        # Try google-workspace first
        result = self._run_mcporter('gmail.send', {
            'to': to,
            'subject': subject,
            'body': body
        })
        
        if result is not None:
            logger.info("Email send succeeded via google-workspace")
            return result
        
        # Fallback to gog
        logger.info("Falling back to gog for email send")
        result = self._run_gog('gmail', 'send', {
            'to': to,
            'subject': subject,
            'body': body
        })
        
        if result is not None:
            logger.info("Email send succeeded via gog (fallback)")
        
        return result
    
    def search_drive(self, query: str, max_results: int = 50) -> Optional[Dict[str, Any]]:
        """
        Search Drive files with fallback.
        Primary: gog, Fallback: google-workspace
        """
        logger.info(f"Searching Drive with query: {query}")
        
        # Try gog first (better Drive support)
        result = self._run_gog('drive', 'search', {
            'query': query,
            'maxResults': max_results
        })
        
        if result is not None:
            logger.info("Drive search succeeded via gog")
            return result
        
        # Fallback to google-workspace
        logger.info("Falling back to google-workspace for Drive search")
        result = self._run_mcporter('drive.search', {
            'query': query,
            'maxResults': max_results
        })
        
        if result is not None:
            logger.info("Drive search succeeded via google-workspace (fallback)")
        
        return result
    
    def get_backend_status(self) -> Dict[str, bool]:
        """Get current backend availability."""
        return self.backend_status.copy()

# Example usage
if __name__ == "__main__":
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Initialize hybrid backend
    hybrid = GoogleWorkspaceHybrid()
    
    print("=== SULV Google Workspace Hybrid Backend ===")
    print(f"Backend status: {hybrid.get_backend_status()}")
    
    # Example: Check backends
    if hybrid.backend_status['google-workspace']:
        print("✓ google-workspace MCP is available")
    else:
        print("✗ google-workspace MCP is not available")
    
    if hybrid.backend_status['gog']:
        print("✓ gog CLI is available")
    else:
        print("✗ gog CLI is not available")
    
    # Example: Test email search (if at least one backend available)
    if hybrid.backend_status['google-workspace'] or hybrid.backend_status['gog']:
        print("\nTesting email search...")
        result = hybrid.search_emails("newer_than:1d", max_results=5)
        if result:
            print(f"✓ Email search successful: {len(result.get('messages', []))} messages")
        else:
            print("✗ Email search failed")
    
    print("\nReady for SULV operations!")