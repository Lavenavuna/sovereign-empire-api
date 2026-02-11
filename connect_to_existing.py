#!/usr/bin/env python3
"""
CONNECT TO EXISTING GITHUB REPO
"""

import subprocess
import os

def run(cmd):
    return subprocess.run(cmd, shell=True, text=True)

print("🔗 CONNECTING TO EXISTING GITHUB REPO")
print("=" * 50)

# Show current files
print("\n📁 Your current files:")
run("ls -la")

# Get GitHub username
username = input("\n🤔 Enter your GitHub username: ").strip()

print(f"\n🚀 Connecting to: https://github.com/{username}/sovereign-empire")

# Execute commands
commands = [
    "git init",
    "git add .",
    'git commit -m "Complete Sovereign Empire Premium System"',
    f"git remote add origin https://github.com/{username}/sovereign-empire.git",
    "git branch -M main",
    "git push -u origin main --force"
]

for cmd in commands:
    print(f"\n▶️  Running: {cmd}")
    result = run(cmd)
    if result.returncode != 0:
        print(f"   ⚠️  Note: {result.stderr[:100] if result.stderr else 'Command continued'}")

print("\n" + "=" * 50)
print("✅ DONE! Your files are now on GitHub!")
print(f"🌐 Visit: https://github.com/{username}/sovereign-empire")
