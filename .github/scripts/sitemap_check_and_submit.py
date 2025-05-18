import subprocess
import os
import sys
import argparse

def run_command(args):
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"::error ::Command failed:\n{e.stderr}")
        sys.exit(1)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Check and submit sitemap to Google')
    parser.add_argument('--site', required=True, help='Site URL (e.g., https://example.com/)')
    parser.add_argument('--sitemap', required=True, help='Sitemap filename (e.g., sitemap.xml)')
    
    args = parser.parse_args()
    
    # Construct full sitemap URL if it doesn't start with http
    if not args.sitemap.startswith('http'):
        # Ensure site URL ends with slash
        site_url = args.site if args.site.endswith('/') else args.site + '/'
        sitemap_url = site_url + args.sitemap.lstrip('/')
    else:
        sitemap_url = args.sitemap
        site_url = args.site
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Calculate the path to submit_status_sitemap.py
    # It should be in the same directory as this script
    submit_script = os.path.join(script_dir, "submit_status_sitemap.py")
    
    # Verify the submit script exists
    if not os.path.exists(submit_script):
        print(f"::error ::Submit script not found at: {submit_script}")
        sys.exit(1)
    
    # Step 1: Check current sitemap status
    print(f"🔍 Checking sitemap status for {sitemap_url}...")
    check_cmd = ["python", submit_script, "--site", site_url, "--check", args.sitemap]
    status_output = run_command(check_cmd)
    
    # Step 2: Parse status
    status_line = next((line for line in status_output.splitlines() if "Status:" in line), None)
    
    if status_line:
        status = status_line.split("Status:")[-1].strip().upper()
        print(f"::notice ::Sitemap status detected: {status}")
        
        if "NOT FETCHED" in status or "ERROR" in status:
            print("::warning ::Sitemap needs to be submitted — submitting now...")
            submit_cmd = ["python", submit_script, "--site", site_url, "--sitemaps", args.sitemap]
            submission_output = run_command(submit_cmd)
            print("::notice ::Sitemap submission completed.")
            print(submission_output)
        else:
            print("::notice ::Sitemap already submitted and fetched. No action required.")
    else:
        # If we can't find status, assume we need to submit
        print("::notice ::Could not determine sitemap status. Submitting sitemap...")
        submit_cmd = ["python", submit_script, "--site", site_url, "--sitemaps", args.sitemap]
        submission_output = run_command(submit_cmd)
        print("::notice ::Sitemap submission completed.")
        print(submission_output)

if __name__ == "__main__":
    main()
