#!/usr/bin/env python3
import os
import sys
import platform
import subprocess

def main():
    """Print diagnostic information about the environment"""
    print("=== Environment Diagnostic ===")
    
    # Python information
    print(f"Python version: {platform.python_version()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
    
    # Operating system information
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()}")
    print(f"Release: {platform.release()}")
    
    # Environment variables
    print("\nEnvironment Variables:")
    for key, value in os.environ.items():
        # Skip sensitive information
        if "SECRET" in key or "TOKEN" in key or "PASSWORD" in key or "CREDENTIAL" in key:
            print(f"{key}: [REDACTED]")
        else:
            print(f"{key}: {value}")
    
    # Check if client_secret.json exists
    print("\nChecking for credentials file:")
    if os.path.exists("client_secret.json"):
        size = os.path.getsize("client_secret.json")
        print(f"client_secret.json exists: {size} bytes")
    else:
        print("client_secret.json not found")
    
    # Installed packages
    print("\nInstalled packages:")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "freeze"], 
                                capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error checking installed packages: {e}")
    
    print("=== End of Diagnostic ===")

if __name__ == "__main__":
    main()
