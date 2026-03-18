#!/usr/bin/env python3
"""
Check if Google credentials exist and are valid.
"""

from pathlib import Path

print("🔍 Checking for Google OAuth Credentials")
print("=" * 50)

# Check all possible locations
locations = [
    ("Home .credentials", Path.home() / '.credentials' / 'credentials.json'),
    ("Project credentials", Path.cwd() / 'credentials' / 'credentials.json'),
    ("Downloads", Path.home() / 'Downloads' / 'credentials.json'),
    ("Desktop", Path.home() / 'Desktop' / 'credentials.json'),
    ("Current directory", Path.cwd() / 'credentials.json'),
]

print("\n📁 Checking locations:")
found = False
for name, path in locations:
    if path.exists():
        print(f"✅ {name}: {path}")
        found = True
        # Check file content
        try:
            import json
            with open(path, 'r') as f:
                data = json.load(f)
            if 'installed' in data or 'web' in data:
                print(f"   ✓ Valid OAuth credentials format")
                print(f"   📏 File size: {path.stat().st_size} bytes")
            else:
                print(f"   ⚠️ Unexpected format")
        except Exception as e:
            print(f"   ❌ Error reading: {e}")
    else:
        print(f"❌ {name}: Not found")

print("\n" + "=" * 50)

if found:
    print("🎉 Credentials found! You can now run:")
    print("\ncd /Users/oppeinqin/Documents/trae_projects/Openclaw/temp_home/.openclaw/workspace/sulv-unified-kb")
    print("source venv/bin/activate")
    print("python test_email_kb_integration.py")
    print("\nThe system will:")
    print("1. Find your credentials automatically")
    print("2. Open browser for authentication")
    print("3. Download latest 10 emails with attachments")
    print("4. Process through knowledge base")
else:
    print("❌ No credentials found.")
    print("\n📋 To get credentials:")
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Follow steps in GET_GOOGLE_CREDENTIALS.md")
    print("3. Save credentials.json to any location above")
    print("\n💡 Easiest: Save to ~/Downloads/credentials.json")
    print("\n📄 Detailed guide: cat GET_GOOGLE_CREDENTIALS.md")

print("\n💰 Remember: All processing is LOCAL, $0 cost!")
print("   vs Cloud/LLM: ~$0.01 per email")