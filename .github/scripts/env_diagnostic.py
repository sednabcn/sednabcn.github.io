#!/usr/bin/env python3
# Simple test script to verify Python environment and dependencies
import sys
import os
import subprocess

def run_check(description, check_fn):
    """Run a check and print results"""
    print(f"\n--- {description} ---")
    try:
        result = check_fn()
        print(f"SUCCESS: {result}")
        return True
    except Exception as e:
        print(f"FAILED: {str(e)}")
        return False

def check_python_version():
    """Check Python version"""
    return f"Python {sys.version}"

def check_module(module_name):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        return f"Module '{module_name}' is available"
    except ImportError as e:
        return f"Module '{module_name}' not found: {str(e)}"

def check_command(command):
    """Run a shell command and return output"""
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        raise Exception(f"Command failed with code {result.returncode}: {result.stderr}")
    return result.stdout.strip()

def main():
    print("===== PYTHON ENVIRONMENT DIAGNOSTIC =====")
    
    # Check Python version
    run_check("Python Version", check_python_version)
    
    # Check key modules needed by the scripts
    modules = [
        "google.oauth2.credentials", 
        "google_auth_oauthlib.flow",
        "google.auth.transport.requests",
        "googleapiclient.discovery",
        "pickle", 
        "tabulate", 
        "argparse", 
        "subprocess",
        "os",
        "sys"
    ]
    
    for module in modules:
        run_check(f"Import {module}", lambda m=module: check_module(m))
    
    # Check for credential files
    credential_files = ["client_secret.json", "token.pickle"]
    for file in credential_files:
        run_check(f"Check for {file}", lambda f=file: f"File exists: {os.path.exists(f)}")
    
    # Check file paths
    script_paths = [
        ".github/scripts/submit_status_sitemap.py",
        "submit_status_sitemap.py"
    ]
    for path in script_paths:
        run_check(f"Check script at {path}", lambda p=path: f"File exists: {os.path.exists(p)}")
    
    # Check environment variables
    env_vars = ["GITHUB_REPOSITORY", "GITHUB_REPOSITORY_OWNER", "GITHUB_WORKSPACE"]
    for var in env_vars:
        run_check(f"Environment variable {var}", lambda v=var: f"{v}={os.environ.get(v, 'Not set')}")
    
    # Check disk space
    run_check("Disk space", lambda: check_command("df -h ."))
    
    # Check memory
    run_check("Memory usage", lambda: check_command("free -m"))
    
    print("\n===== DIAGNOSTIC COMPLETE =====")

if __name__ == "__main__":
    main()
