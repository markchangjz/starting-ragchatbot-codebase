#!/usr/bin/env python3
"""
Quality check script that runs all code quality tools.
"""
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"Running {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {description}: {e}", file=sys.stderr)
        return False


def main():
    """Run all quality checks."""
    checks = [
        ("python3 -m black --check backend/ main.py", "Black format check"),
    ]
    
    all_passed = True
    
    for command, description in checks:
        success = run_command(command, description)
        if not success:
            all_passed = False
            print(f"❌ {description} failed")
        else:
            print(f"✅ {description} passed")
        print("-" * 50)
    
    if all_passed:
        print("🎉 All quality checks passed!")
        return 0
    else:
        print("💥 Some quality checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())