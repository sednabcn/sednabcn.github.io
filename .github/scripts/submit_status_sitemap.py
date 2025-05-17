#!/usr/bin/env python3
# Google Search Console Sitemap Submission Script
# This script uses the Google Search Console API to submit sitemaps

import os
import sys
import argparse
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import tabulate

# If modifying these scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/webmasters']

def get_credentials():
    """Get valid user credentials from storage or user authentication."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials don't exist or are invalid, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Look for client_secret.json first
            if os.path.exists('client_secret.json'):
                flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
                # Use port 8080 instead of a dynamic port
                creds = flow.run_local_server(port=8080)
            else:
                print("ERROR: No credentials found. Please create a client_secret.json file.")
                print("See: https://developers.google.com/search/apis/indexing-api/v3/quickstart")
                sys.exit(1)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def submit_sitemap(service, site_url, sitemap_url):
    """Submit a sitemap to Google Search Console."""
    try:
        service.sitemaps().submit(siteUrl=site_url, feedpath=sitemap_url).execute()
        print(f"Successfully submitted sitemap: {sitemap_url}")
        return True
    except HttpError as error:
        print(f"Error submitting sitemap {sitemap_url}: {error}")
        return False

def get_sitemap_details(sitemap):
    """Extract and format detailed information about a sitemap."""
    path = sitemap.get('path', 'Unknown')
    
    last_submitted = sitemap.get('lastSubmitted', 'Never')
    last_downloaded = sitemap.get('lastDownloaded', 'Never')
    
    # Process contents if available
    contents = sitemap.get('contents', [])
    total_urls = 0
    type_info = "Unknown"
    
    if contents:
        for content in contents:
            submitted_count = int(content.get('submitted', '0'))
            total_urls += submitted_count
            
            # Try to determine type from content
            if 'type' in content:
                type_info = content['type']
    
    # Process warnings if available
    warnings = sitemap.get('warnings', '0')
    errors = sitemap.get('errors', '0')
    
    # Check sitemap status
    if 'lastDownloaded' not in sitemap:
        status = "Not fetched"
    elif errors != '0':
        status = f"Errors: {errors}"
    elif warnings != '0':
        status = f"Warnings: {warnings}"
    else:
        status = "OK"
    
    return {
        'path': path,
        'type': type_info,
        'submitted': last_submitted,
        'last_read': last_downloaded,
        'status': status,
        'discovered_urls': total_urls,
        'warnings': warnings,
        'errors': errors
    }

def check_sitemap_status(service, site_url, sitemap_url=None, detailed=False):
    """Check status of sitemaps in Google Search Console."""
    try:
        response = service.sitemaps().list(siteUrl=site_url).execute()
        
        if 'sitemap' not in response or not response['sitemap']:
            print("No sitemaps found for this site.")
            return
        
        sitemaps = response['sitemap']
        
        # Filter for specific sitemap if requested
        if sitemap_url:
            sitemaps = [s for s in sitemaps if s['path'] == sitemap_url]
            if not sitemaps:
                print(f"Sitemap {sitemap_url} not found in Google Search Console.")
                return
        
        if detailed:
            # Create table data
            table_data = []
            headers = ["Sitemap", "Type", "Status", "Last Read", "Discovered URLs"]
            
            for sitemap in sitemaps:
                details = get_sitemap_details(sitemap)
                table_data.append([
                    details['path'],
                    details['type'],
                    details['status'],
                    details['last_read'],
                    details['discovered_urls']
                ])
            
            # Print table
            print("\nSitemap Status Details:")
            print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Print any warnings or errors
            for sitemap in sitemaps:
                details = get_sitemap_details(sitemap)
                if details['warnings'] != '0' or details['errors'] != '0':
                    print(f"\nIssues with {details['path']}:")
                    if details['errors'] != '0':
                        print(f"- Errors: {details['errors']}")
                    if details['warnings'] != '0':
                        print(f"- Warnings: {details['warnings']}")
        else:
            # Simple listing format
            print("\nCurrently submitted sitemaps:")
            for sitemap in sitemaps:
                details = get_sitemap_details(sitemap)
                status_text = f"Status: {details['status']}"
                if 'lastDownloaded' in sitemap:
                    status_text += f", Last fetched: {details['last_read']}"
                print(f"- {details['path']} ({status_text})")
        
    except HttpError as error:
        print(f"Error checking sitemap status: {error}")

def list_sitemaps(service, site_url):
    """List all sitemaps for a site in Search Console."""
    check_sitemap_status(service, site_url, detailed=False)

def main():
    parser = argparse.ArgumentParser(description='Submit and manage sitemaps in Google Search Console')
    parser.add_argument('--site', '-s', required=True, help='Site URL (e.g., https://sednabcn.github.io/)')
    parser.add_argument('--sitemaps', '-m', nargs='+', help='Sitemap URLs (e.g., sitemap.xml)')
    parser.add_argument('--list', '-l', action='store_true', help='List existing sitemaps')
    parser.add_argument('--status', action='store_true', help='Check detailed status of sitemaps')
    parser.add_argument('--check', help='Check status of a specific sitemap')
    
    args = parser.parse_args()
    
    # Get the site URL from args
    site_url = args.site
    
    # Ensure site URL ends with trailing slash
    if not site_url.endswith('/'):
        site_url += '/'
    
    # Get credentials and build service
    try:
        creds = get_credentials()
        service = build('searchconsole', 'v1', credentials=creds)
        print(f"Connected to Google Search Console API for site: {site_url}")
    except Exception as e:
        print(f"Failed to initialize service: {e}")
        sys.exit(1)
    
    # Check status of specific sitemap if requested
    if args.check:
        check_sitemap_status(service, site_url, args.check, detailed=True)
        sys.exit(0)
    
    # Check detailed status of all sitemaps if requested
    if args.status:
        check_sitemap_status(service, site_url, detailed=True)
        sys.exit(0)
    
    # List existing sitemaps if requested
    if args.list:
        list_sitemaps(service, site_url)
        if not args.sitemaps:
            sys.exit(0)
    
    # Submit sitemaps if provided
    if args.sitemaps:
        print(f"Submitting {len(args.sitemaps)} sitemap(s)...")
        
        success_count = 0
        for sitemap in args.sitemaps:
            # If sitemap doesn't start with http, assume it's a relative path
            if not sitemap.startswith('http'):
                # Strip leading slash if present
                if sitemap.startswith('/'):
                    sitemap = sitemap[1:]
                # No need to join with site_url as the API expects paths
            
            if submit_sitemap(service, site_url, sitemap):
                success_count += 1
        
        print(f"Sitemap submission completed! {success_count}/{len(args.sitemaps)} successful.")
        
        # List updated sitemaps
        list_sitemaps(service, site_url)
    elif not args.list and not args.status and not args.check:
        parser.print_help()

if __name__ == "__main__":
    main()
