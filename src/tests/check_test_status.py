#!/usr/bin/env python3
"""
Check the current test status and provide next steps.
"""

import json
from pathlib import Path
import sys

def check_test_data():
    """Check if test data was generated."""
    test_dir = Path('test_data')
    
    if not test_dir.exists():
        return {'exists': False, 'message': 'Test data not generated'}
    
    # Check for key files
    files = {
        'emails': len(list((test_dir / 'emails').glob('*.json'))),
        'attachments': len(list((test_dir / 'attachments').glob('*'))),
        'kb_processed': len(list((test_dir / 'kb_processed').glob('*.json'))),
        'summary': (test_dir / 'test_summary.json').exists(),
        'report': (test_dir / 'test_report.json').exists()
    }
    
    if files['summary']:
        with open(test_dir / 'test_summary.json', 'r') as f:
            summary = json.load(f)
        files['summary_data'] = summary['test_run']
    
    return {'exists': True, 'files': files}

def check_skill_status():
    """Check SULV skill status."""
    skill_dir = Path('skills/sulv-google-workspace-hybrid')
    
    if not skill_dir.exists():
        return {'exists': False, 'message': 'SULV skill not found'}
    
    scripts = {
        'email_sync.py': (skill_dir / 'scripts' / 'email_sync.py').exists(),
        'hybrid_backend.py': (skill_dir / 'scripts' / 'hybrid_backend.py').exists(),
        'chat_reporter.py': (skill_dir / 'scripts' / 'chat_reporter.py').exists()
    }
    
    return {'exists': True, 'scripts': scripts}

def check_kb_status():
    """Check KB system status."""
    kb_dir = Path('enterprise-kb')
    
    if not kb_dir.exists():
        return {'exists': False, 'message': 'KB system not found'}
    
    files = {
        'main.py': (kb_dir / 'main.py').exists(),
        'requirements.txt': (kb_dir / 'requirements.txt').exists(),
        'README.md': (kb_dir / 'README.md').exists()
    }
    
    return {'exists': True, 'files': files}

def check_mcporter():
    """Check mcporter availability."""
    import subprocess
    
    try:
        result = subprocess.run(['which', 'mcporter'], 
                              capture_output=True, text=True)
        mcp_available = result.returncode == 0
        
        if mcp_available:
            # Check google-workspace config
            result = subprocess.run(['mcporter', 'config', 'list'], 
                                  capture_output=True, text=True)
            google_ws_configured = 'google-workspace' in result.stdout
        else:
            google_ws_configured = False
            
        return {
            'mcporter_available': mcp_available,
            'google_workspace_configured': google_ws_configured
        }
        
    except Exception as e:
        return {'error': str(e)}

def main():
    """Check overall status."""
    print("=" * 70)
    print("SULV Email + KB Test Status Check")
    print("=" * 70)
    
    print("\n1. Test Data Status:")
    test_data = check_test_data()
    if test_data['exists']:
        files = test_data['files']
        print(f"   ✓ Test data generated:")
        print(f"     - Emails: {files.get('emails', 0)}")
        print(f"     - Attachments: {files.get('attachments', 0)}")
        print(f"     - KB entries: {files.get('kb_processed', 0)}")
        
        if 'summary_data' in files:
            summary = files['summary_data']
            print(f"     - Total emails: {summary.get('num_emails', 0)}")
            print(f"     - Total attachments: {summary.get('total_attachments', 0)}")
    else:
        print(f"   ✗ {test_data['message']}")
    
    print("\n2. SULV Skill Status:")
    skill_status = check_skill_status()
    if skill_status['exists']:
        scripts = skill_status['scripts']
        print(f"   ✓ SULV skill found:")
        for script, exists in scripts.items():
            status = "✓" if exists else "✗"
            print(f"     {status} {script}")
    else:
        print(f"   ✗ {skill_status['message']}")
    
    print("\n3. KB System Status:")
    kb_status = check_kb_status()
    if kb_status['exists']:
        files = kb_status['files']
        print(f"   ✓ KB system found:")
        for file, exists in files.items():
            status = "✓" if exists else "✗"
            print(f"     {status} {file}")
    else:
        print(f"   ✗ {kb_status['message']}")
    
    print("\n4. MCPorter Status:")
    mcp_status = check_mcporter()
    if 'error' in mcp_status:
        print(f"   ✗ Error: {mcp_status['error']}")
    else:
        print(f"   ✓ mcporter: {'Available' if mcp_status['mcporter_available'] else 'Not available'}")
        print(f"   ✓ google-workspace: {'Configured' if mcp_status['google_workspace_configured'] else 'Not configured'}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    
    print("\nA. Complete Google Workspace Authentication:")
    print("   Run: mcporter call --server google-workspace --tool 'people.getMe'")
    print("   This will open a browser for OAuth authentication.")
    
    print("\nB. Execute Test Workflow:")
    print("   1. Review TEST_EXECUTION_PLAN.md for detailed steps")
    print("   2. Start with Phase 2 tests (skill functionality)")
    print("   3. Proceed to Phase 3 (100 email scale test)")
    print("   4. Complete with Phase 4 (KB integration)")
    
    print("\nC. Verify Results:")
    print("   - Check test_data/test_report.json")
    print("   - Review test_reports/sulv_skill_test_report.json")
    print("   - Examine any error logs in logs/ directory")
    
    print("\nD. Optional Improvements:")
    print("   1. Install gog CLI for complete hybrid functionality")
    print("   2. Set up automated testing with cron")
    print("   3. Create production deployment pipeline")
    
    print("\n" + "=" * 70)
    print("Ready to test when authentication is complete!")
    print("=" * 70)
    
    return {
        'test_data': test_data,
        'skill_status': skill_status,
        'kb_status': kb_status,
        'mcp_status': mcp_status
    }

if __name__ == "__main__":
    main()