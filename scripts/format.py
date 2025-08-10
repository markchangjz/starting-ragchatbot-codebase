#!/usr/bin/env python3
"""
Code formatting script using Black.
"""
import subprocess
import sys
from pathlib import Path


def run_black():
    """Run Black formatter on Python files."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "backend/", "main.py"],
            capture_output=True,
            text=True,
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error running Black: {e}", file=sys.stderr)
        return False


def check_formatting():
    """Check if code is properly formatted without making changes."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "backend/", "main.py"],
            capture_output=True,
            text=True,
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking formatting: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        print("Checking code formatting...")
        success = check_formatting()
        if success:
            print("✅ All code is properly formatted")
        else:
            print("❌ Code formatting issues found")
            sys.exit(1)
    else:
        print("Formatting code with Black...")
        success = run_black()
        if success:
            print("✅ Code formatting completed")
        else:
            print("❌ Code formatting failed")
            sys.exit(1)