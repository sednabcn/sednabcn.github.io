#!/usr/bin/env python3

import os
import subprocess
import sys

def main():
    site_url = "https://sednabcn.github.io/"
    sitemap_url = "https://sednabcn.github.io/sitemap.xml"
    
    print("Starting direct sitemap submission...")
    
    # Since we know the submit_status_sitemap.py is in the same directory,
    # call it directly without trying multiple paths
    script_path = os.path.join(os.path.dirname(__file__), 'submit_status_sitemap.py')
    
    print(f"Using script path: {script_path}")
    command = ['python', script_path, '--site', site_url, '--sitemaps', sitemap_url]
    print(f"Running command: {' '.join(command)}")
    
    try:
        # Use capture_output to capture both stdout and stderr
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print("Command executed successfully")
            print(result.stdout)
        else:
            print(f"Command failed with exit code {result.returncode}")
            print(f"Error output:")
            print(result.stderr)
            print("\nAttempting to debug further:")
            # List directory contents to check if the script is there
            dir_path = os.path.dirname(__file__)
            list_result = subprocess.run(['ls', '-la', dir_path], capture_output=True, text=True)
            print(f"Directory contents of {dir_path}:")
            print(list_result.stdout)
            sys.exit(1)
    except Exception as e:
        print(f"Exception running command: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
