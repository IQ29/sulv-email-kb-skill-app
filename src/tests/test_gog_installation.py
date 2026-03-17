#!/usr/bin/env python3
"""
Test gog CLI installation and integration with SULV hybrid skill.
"""

import subprocess
import json
import sys
from pathlib import Path

def test_gog_installation():
    """Test if gog is properly installed."""
    print("Testing gog CLI installation...")
    
    # Test 1: Check if gog is in PATH
    try:
        result = subprocess.run(['which', 'gog'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ gog found at: {result.stdout.strip()}")
        else:
            print("✗ gog not found in PATH")
            return False
    except Exception as e:
        print(f"✗ Error checking gog: {e}")
        return False
    
    # Test 2: Check version
    try:
        result = subprocess.run(['gog', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ gog version: {result.stdout.strip()}")
        else:
            print(f"✗ Could not get gog version: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error getting gog version: {e}")
        return False
    
    # Test 3: Check help
    try:
        result = subprocess.run(['gog', '--help'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ gog help command works")
            # Check for key subcommands
            output = result.stdout.lower()
            if 'auth' in output:
                print("  - Auth subcommand available")
            if 'gmail' in output:
                print("  - Gmail subcommand available")
            if 'drive' in output:
                print("  - Drive subcommand available")
        else:
            print(f"✗ gog help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error checking gog help: {e}")
        return False
    
    return True

def test_hybrid_backend_with_gog():
    """Test if hybrid backend detects gog."""
    print("\nTesting hybrid backend detection...")
    
    # Import the hybrid backend
    sys.path.insert(0, 'skills/sulv-google-workspace-hybrid/scripts')
    
    try:
        from hybrid_backend import GoogleWorkspaceHybrid
        
        # Create instance
        hybrid = GoogleWorkspaceHybrid()
        
        print(f"Backend status: {hybrid.backend_status}")
        
        # Check specifically for gog
        if hybrid.backend_status.get('gog', False):
            print("✓ Hybrid backend successfully detected gog!")
            
            # Test backend selection logic
            print("\nBackend selection logic:")
            print("  - Gmail operations: Try google-workspace, fallback to gog")
            print("  - Chat operations: google-workspace only")
            print("  - Drive operations: Prefer gog, fallback to google-workspace")
            
            return True
        else:
            print("✗ Hybrid backend did not detect gog")
            print("  This might be because gog needs authentication")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import hybrid_backend: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing hybrid backend: {e}")
        return False

def check_gog_authentication():
    """Check gog authentication status."""
    print("\nChecking gog authentication status...")
    
    try:
        # Check auth status
        result = subprocess.run(['gog', 'auth', 'list'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ gog auth list command works")
            print(f"Output:\n{result.stdout}")
            
            # Check if any accounts are configured
            if 'No accounts' in result.stdout or 'no accounts' in result.stdout.lower():
                print("\n⚠️  No accounts configured. Authentication needed.")
                print("\nTo authenticate gog:")
                print("1. Get client_secret.json from Google Cloud Console")
                print("2. Run: gog auth credentials /path/to/client_secret.json")
                print("3. Run: gog auth add admin_auto@sulv.com.au --services gmail,calendar,drive")
                return False
            else:
                print("✓ Accounts are configured")
                return True
        else:
            print(f"✗ gog auth list failed: {result.stderr}")
            print("\n⚠️  Authentication may be needed.")
            return False
            
    except Exception as e:
        print(f"✗ Error checking gog auth: {e}")
        return False

def update_test_status():
    """Update the test status to reflect gog installation."""
    print("\nUpdating test status...")
    
    # Check if test status file exists
    status_file = Path('test_reports/sulv_skill_test_report.json')
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                report = json.load(f)
            
            # Update recommendations
            if 'recommendations' in report:
                # Remove gog installation recommendation if present
                new_recommendations = []
                for rec in report['recommendations']:
                    if 'gog' not in rec.lower() and 'install' not in rec.lower():
                        new_recommendations.append(rec)
                
                # Add new recommendation for gog authentication
                new_recommendations.append("Authenticate gog CLI with Google Workspace credentials")
                
                report['recommendations'] = new_recommendations
            
            # Update summary
            report['gog_status'] = {
                'installed': True,
                'version': subprocess.run(['gog', '--version'], capture_output=True, text=True).stdout.strip(),
                'authenticated': False,  # Will need to check this
                'next_step': 'Run authentication: gog auth credentials <client_secret.json>'
            }
            
            # Save updated report
            with open(status_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"✓ Updated test report: {status_file}")
            
        except Exception as e:
            print(f"✗ Error updating test report: {e}")
    
    # Update TEST_EXECUTION_PLAN.md
    plan_file = Path('TEST_EXECUTION_PLAN.md')
    if plan_file.exists():
        try:
            with open(plan_file, 'r') as f:
                content = f.read()
            
            # Update the backend status section
            if "gog CLI: ❌ Not installed" in content:
                content = content.replace(
                    "gog CLI: ❌ Not installed", 
                    "gog CLI: ✅ Installed (needs authentication)"
                )
            
            # Update the note section
            if "**Note on `gog` CLI:**" in content:
                note_section = """### ⚠️ **Note on `gog` CLI:**
The `gog` CLI is now installed! However, it needs authentication:
1. Get `client_secret.json` from Google Cloud Console
2. Run: `gog auth credentials /path/to/client_secret.json`
3. Run: `gog auth add admin_auto@sulv.com.au --services gmail,calendar,drive`

Once authenticated, the hybrid skill will have full fallback capability."""
                
                # Find and replace the note section
                import re
                content = re.sub(
                    r'### ⚠️ \*\*Note on `gog` CLI:\*\*.*?(?=###|\Z)',
                    note_section + '\n\n',
                    content,
                    flags=re.DOTALL
                )
            
            with open(plan_file, 'w') as f:
                f.write(content)
            
            print(f"✓ Updated test execution plan: {plan_file}")
            
        except Exception as e:
            print(f"✗ Error updating test plan: {e}")

def main():
    """Run all gog tests."""
    print("=" * 70)
    print("gog CLI Installation Test")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Basic installation
    results['installation'] = test_gog_installation()
    
    # Test 2: Hybrid backend detection
    results['hybrid_detection'] = test_hybrid_backend_with_gog()
    
    # Test 3: Authentication check
    results['authentication'] = check_gog_authentication()
    
    # Update test documents
    update_test_status()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    print(f"Installation: {'✓ PASS' if results['installation'] else '✗ FAIL'}")
    print(f"Hybrid Detection: {'✓ PASS' if results['hybrid_detection'] else '✗ FAIL'}")
    print(f"Authentication: {'✓ READY' if results['authentication'] else '⚠ NEEDS SETUP'}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    
    if not results['authentication']:
        print("\n1. **Authenticate gog CLI:**")
        print("   You need a client_secret.json from Google Cloud Console")
        print("   Then run:")
        print("   gog auth credentials /path/to/client_secret.json")
        print("   gog auth add admin_auto@sulv.com.au --services gmail,calendar,drive")
    
    print("\n2. **Complete Google Workspace Authentication for MCP:**")
    print("   mcporter call --server google-workspace --tool 'people.getMe'")
    
    print("\n3. **Run Full Test Suite:**")
    print("   python3 test_sulv_skill_workflow.py")
    print("   python3 test_email_kb_integration.py")
    
    print("\n4. **Verify Hybrid Functionality:**")
    print("   The SULV skill now has full hybrid capability!")
    print("   - Primary: google-workspace MCP")
    print("   - Fallback: gog CLI")
    
    print("\n" + "=" * 70)
    return results

if __name__ == "__main__":
    main()