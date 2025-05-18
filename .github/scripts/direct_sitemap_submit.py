#!/usr/bin/env python3
# Direct sitemap submission script that uses the exact working command pattern
import subprocess
import sys

def main():
    print("Starting direct sitemap submission...")
    
    # Try different script path options
    script_paths = [
        ".github/scripts/submit_status_sitemap.py",
        "./submit_status_sitemap.py",
        "submit_status_sitemap.py",
        "./.github/scripts/submit_status_sitemap.py",
        "../submit_status_sitemap.py"
    ]
    
    success = False
    
    for script_path in script_paths:
        print(f"\nTrying script path: {script_path}")
        cmd = [
            "python",
            script_path,
            "--site", "https://sednabcn.github.io/",
            "--sitemaps", "https://sednabcn.github.io/sitemap.xml"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            # Run the command and capture output
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Print the output
            print("Command succeeded!")
            print("Output:")
            print(result.stdout)
            
            success = True
            break
            
        except subprocess.CalledProcessError as e:
            # Print error details if the command fails
            print(f"Command failed with exit code {e.returncode}")
            print("Error output:")
            print(e.stderr)
            
        except FileNotFoundError:
            print(f"Script not found at path: {script_path}")
    
    if not success:
        # Print additional debug info
        print("\nAdditional debug information:")
        print(f"Working directory: {subprocess.run(['pwd'], capture_output=True, text=True).stdout.strip()}")
        print(f"Directory contents: {subprocess.run(['ls', '-la'], capture_output=True, text=True).stdout}")
        print(f"Scripts directory: {subprocess.run(['ls', '-la', '.github/scripts'], capture_output=True, text=True, stderr=subprocess.STDOUT).stdout}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
