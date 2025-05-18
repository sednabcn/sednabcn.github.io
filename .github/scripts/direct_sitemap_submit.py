#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    """
    Simple wrapper to call submit_status_sitemap.py in the same directory
    """
    print("Starting direct sitemap submission...")
    
    # Define the site and sitemap URL
    site_url = "https://sednabcn.github.io/"
    sitemap_url = "https://sednabcn.github.io/sitemap.xml"
    
    # Print current directory for debugging
    cwd = os.getcwd()
    print(f"Working directory: {cwd}")
    
    # List the current directory contents
    print("Directory contents:")
    try:
        result = subprocess.run(['ls', '-la'], text=True, capture_output=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error listing directory: {e}")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")
    
    # Define target script path (in the same directory)
    submit_script = os.path.join(script_dir, "submit_status_sitemap.py")
    
    # Verify the script exists
    if not os.path.exists(submit_script):
        print(f"ERROR: Submit script not found at {submit_script}")
        print("Looking for script in current directory...")
        if os.path.exists("submit_status_sitemap.py"):
            submit_script = "./submit_status_sitemap.py"
            print(f"Found script in current directory")
        else:
            print("Script not found in current directory either")
            sys.exit(1)
    
    # Execute the script
    print(f"Executing script: {submit_script}")
    cmd = [sys.executable, submit_script, '--site', site_url, '--sitemaps', sitemap_url]
    
    try:
        result = subprocess.run(cmd, text=True, capture_output=True)
        print(f"Output: {result.stdout}")
        
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
        if result.returncode != 0:
            print(f"Script failed with exit code {result.returncode}")
            sys.exit(result.returncode)
        else:
            print("Sitemap submission completed successfully")
    except Exception as e:
        print(f"Error executing script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
