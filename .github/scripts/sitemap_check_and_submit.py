#!/usr/bin/env python3
"""
Improved GitHub Actions workflow script for sitemap submission.
This script should be placed in .github/workflows/scripts/ directory.
"""

import os
import sys
import argparse
import subprocess
import json

def run_command(args, description=None):
    """Run a command and handle errors appropriately for GitHub Actions environment"""
    if description:
        print(f"::group::{description}")
    
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        output = result.stdout.strip()
        if output:
            print(output)
        if description:
            print(f"::endgroup::")
        return output
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.strip()
        print(f"::error::Command failed: {' '.join(args)}")
        print(f"Error output: {error_output}")
        if description:
            print(f"::endgroup::")
        sys.exit(1)

def get_repo_info():
    """Get repository information from GitHub Actions environment variables"""
    # Get the repository name from GITHUB_REPOSITORY env var (e.g., "username/repo-name")
    repo_fullname = os.environ.get('GITHUB_REPOSITORY', '')
    
    if not repo_fullname:
        print("::warning::GITHUB_REPOSITORY environment variable not found")
        return None, None
    
    try:
        username, repo_name = repo_fullname.split('/')
        # Standard GitHub Pages URL format
        site_url = f"https://{username}.github.io/{repo_name}/"
        return site_url, repo_name
    except ValueError:
        print(f"::warning::Could not parse repository name from '{repo_fullname}'")
        return None, None

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Check and submit sitemap to Google Search Console')
    parser.add_argument('--site', help='Site URL (e.g., https://username.github.io/repo/)')
    parser.add_argument('--sitemap', default='sitemap.xml', help='Sitemap filename (default: sitemap.xml)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Get repository information if not provided
    site_url = args.site
    if not site_url:
        auto_site_url, repo_name = get_repo_info()
        if auto_site_url:
            site_url = auto_site_url
            print(f"::notice::Auto-detected site URL: {site_url}")
        else:
            print("::error::Site URL not provided and could not be auto-detected")
            print("Please specify --site parameter or run this in a GitHub Actions environment")
            sys.exit(1)
    
    # Ensure site URL ends with slash
    if not site_url.endswith('/'):
        site_url += '/'
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Calculate the path to submit_status_sitemap.py
    # Look in the same directory first, then try a relative path
    submit_script_paths = [
        os.path.join(script_dir, "submit_status_sitemap.py"),
        os.path.join(script_dir, "..", "scripts", "submit_status_sitemap.py"),
        "./submit_status_sitemap.py"
    ]
    
    submit_script = None
    for path in submit_script_paths:
        if os.path.exists(path):
            submit_script = path
            break
    
    if not submit_script:
        print("::error::Could not find submit_status_sitemap.py script")
        print("Paths checked:")
        for path in submit_script_paths:
            print(f"- {path}")
        sys.exit(1)
    
    print(f"::notice::Using submit script at: {submit_script}")
    print(f"::notice::Checking sitemap for: {site_url}")
    print(f"::notice::Sitemap file: {args.sitemap}")
    
    # Step 1: List all sitemaps in Search Console
    print("🔍 Checking current sitemaps in Google Search Console...")
    try:
        list_cmd = ["python", submit_script, "--site", site_url, "--list"]
        list_output = run_command(list_cmd, "List current sitemaps")
    except Exception as e:
        print(f"::warning::Failed to list sitemaps: {str(e)}")
        list_output = ""
    
    # Step 2: Check specific sitemap status
    print(f"🔍 Checking status for sitemap: {args.sitemap}")
    try:
        check_cmd = ["python", submit_script, "--site", site_url, "--check", args.sitemap]
        status_output = run_command(check_cmd, "Check sitemap status")
        
        # Determine if we need to submit based on status output
        needs_submit = True
        if "Status: OK" in status_output:
            print(f"::notice::Sitemap {args.sitemap} already has status OK")
            needs_submit = False
        else:
            # Look for specific indicators that we need to submit
            if "Not fetched" in status_output or "Error" in status_output:
                print(f"::warning::Sitemap {args.sitemap} needs submission - status issues detected")
            elif "Sitemap not found" in status_output:
                print(f"::warning::Sitemap {args.sitemap} not found in Search Console")
            else:
                # If we can't determine status clearly, submit anyway
                print(f"::notice::Could not clearly determine sitemap status - will submit anyway")
    except Exception as e:
        print(f"::warning::Failed to check sitemap status: {str(e)}")
        needs_submit = True
    
    # Step 3: Submit the sitemap if needed
    if needs_submit:
        print(f"📤 Submitting sitemap: {args.sitemap}")
        submit_cmd = ["python", submit_script, "--site", site_url, "--sitemaps", args.sitemap]
        submit_output = run_command(submit_cmd, "Submit sitemap")
        print(f"::notice::Sitemap {args.sitemap} submission completed")
    else:
        print(f"::notice::Sitemap {args.sitemap} already properly submitted and indexed")
    
    print("✅ Sitemap processing completed")

if __name__ == "__main__":
    main()
