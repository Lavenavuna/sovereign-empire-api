#!/usr/bin/env python3
"""
verify_setup.py - Verify the app setup before deploying to Railway
Run this locally to catch issues early.
"""

import sys
import os


def check_files():
    """Check that all required files exist"""
    required_files = [
        "api.py",
        "database.py",
        "Dockerfile",
        "requirements.txt",
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print("✅ All required files present")
    return True


def check_imports():
    """Check that all imports work"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import psycopg2
        print("✅ All Python imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Run: pip install -r requirements.txt")
        return False


def check_dockerfile():
    """Check Dockerfile for common issues"""
    try:
        with open("Dockerfile", "r") as f:
            content = f.read()
        
        # Check for PORT variable usage
        if "${PORT" not in content:
            print("⚠️  Warning: Dockerfile doesn't use $PORT variable")
            print("   This may cause 502 errors on Railway")
            return False
        
        # Check for hardcoded ports in CMD
        if "--port 8000" in content and "${PORT" not in content:
            print("❌ Dockerfile has hardcoded port 8000 without $PORT fallback")
            return False
        
        if "--port 8080" in content and "${PORT" not in content:
            print("❌ Dockerfile has hardcoded port 8080 without $PORT fallback")
            return False
        
        print("✅ Dockerfile looks good")
        return True
        
    except FileNotFoundError:
        print("❌ Dockerfile not found")
        return False


def check_api_file():
    """Check api.py for common issues"""
    try:
        with open("api.py", "r") as f:
            content = f.read()
        
        # Check for FastAPI app
        if "app = FastAPI" not in content:
            print("❌ api.py doesn't define FastAPI app")
            return False
        
        # Check for health endpoint
        if "@app.get(\"/health\")" not in content and "@app.get('/health')" not in content:
            print("⚠️  Warning: No /health endpoint found")
            print("   Railway uses this for health checks")
        
        print("✅ api.py looks good")
        return True
        
    except FileNotFoundError:
        print("❌ api.py not found")
        return False


def check_database_url_handling():
    """Check that database URL normalization exists"""
    try:
        with open("database.py", "r") as f:
            content = f.read()
        
        if "postgres://" in content and "postgresql://" in content:
            print("✅ Database URL normalization present")
            return True
        else:
            print("⚠️  Warning: No database URL normalization found")
            print("   Railway provides 'postgres://' but SQLAlchemy needs 'postgresql://'")
            return True  # Non-critical
        
    except FileNotFoundError:
        print("❌ database.py not found")
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("🔍 Verifying Railway Setup")
    print("=" * 60)
    print()
    
    checks = [
        ("File structure", check_files),
        ("Python imports", check_imports),
        ("Dockerfile", check_dockerfile),
        ("API file", check_api_file),
        ("Database handling", check_database_url_handling),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking: {name}")
        print("-" * 60)
        results.append(check_func())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All checks passed! Ready to deploy to Railway.")
        print("\nNext steps:")
        print("1. Commit these files to Git")
        print("2. Push to GitHub")
        print("3. Deploy on Railway")
        print("4. Add PostgreSQL database in Railway")
        print("5. Visit https://your-app.up.railway.app/health")
        return 0
    else:
        print("❌ Some checks failed. Fix the issues above before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
