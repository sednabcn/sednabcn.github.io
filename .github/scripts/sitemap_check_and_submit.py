#!/usr/bin/env python3
import subprocess
import os
import sys
import argparse

def run_command(args):
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed:\n{e.stderr}")
        sys.exit(1)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Check and submit sitemap to Google')
    parser.add_argument('--site', help='Site URL (e.g., https://example.com/)')
    parser.add_argument('--sitemap', default='sitemap.xml', help='Sitemap filename (e.g., sitemap.xml)')
    
    args = parser.parse_args()
    
    # If site URL is not provided, try to determine it from GitHub environment variables
    site_url = args.site
    if not site_url:
        # GitHub environment variables
        github_repo_owner = os.environ.get('GITHUB_REPOSITORY_OWNER')
        github_repo = os.environ.get('GITHUB_REPOSITORY')
        
        if github_repo and github_repo_owner:
            # Extract repository name from the full repository path (owner/repo)
            repo_name = github_repo.split('/')[-1]
            site_url = f"https://{github_repo_owner}.github.io/{repo_name}/"
            print(f"Auto-detected site URL: {site_url}")
        else:
            print("Error: Site URL not provided and could not be auto-detected")
            print("Please specify --site parameter or run this in a GitHub Actions environment")
            sys.exit(1)
    
    # Use default sitemap if not provided
    sitemap_path = args.sitemap or 'sitemap.xml'
    
    # Ensure site URL ends with slash
    if not site_url.endswith('/'):
        site_url += '/'
    
    # Construct full sitemap URL if it doesn't start with http
    if not sitemap_path.startswith('http'):
        sitemap_url = site_url + sitemap_path.lstrip('/')
    else:
        sitemap_url = sitemap_path
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Calculate the path to submit_status_sitemap.py
    # It should be in the same directory as this script
    submit_script = os.path.join(script_dir, "submit_status_sitemap.py")
    
    # Verify the submit script exists
    if not os.path.exists(submit_script):
        print(f"Error: Submit script not found at: {submit_script}")
        sys.exit(1)
    
    # Step 1: Check current sitemap status
    print(f"🔍 Checking sitemap status for {sitemap_url}...")
    check_cmd = ["python", submit_script, "--site", site_url, "--check", sitemap_url]
    status_output = run_command(check_cmd)
    
    # Step 2: Parse status
    status_line = next((line for line in status_output.splitlines() if "Status:" in line), None)
    
    if status_line:
        status = status_line.split("Status:")[-1].strip().upper()
        print(f"Sitemap status detected: {status}")
        
        if "NOT FETCHED" in status or "ERROR" in status:
            print("Warning: Sitemap needs to be submitted — submitting now...")
            submit_cmd = ["python", submit_script, "--site", site_url, "--sitemaps", sitemap_url]
            submission_output = run_command(submit_cmd)
            print("Sitemap submission completed.")
            print(submission_output)
        else:
            print("Sitemap already submitted and fetched. No action required.")
    else:
        # If we can't find status, assume we need to submit
        print("Could not determine sitemap status. Submitting sitemap...")
        submit_cmd = ["python", submit_script, "--site", site_url, "--sitemaps", sitemap_url]
        submission_output = run_command(submit_cmd)
        print("Sitemap submission completed.")
        print(submission_output)

if __name__ == "__main__":
    main()
