#!/usr/bin/env python3
# Google Search Console Indexing Status Monitor
# This script checks indexing status and sends notifications

import os
import sys
import argparse
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes required for Search Console API
SCOPES = ['https://www.googleapis.com/auth/webmasters']

def get_service_account_credentials():
    """Get credentials from a service account key file."""
    try:
        if os.path.exists('service-account.json'):
            print("Found key for service account")
            creds = ServiceAccountCredentials.from_service_account_file(
                'service-account.json', scopes=SCOPES)
            return creds
        else:
            print("ERROR: service-account.json file not found.")
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred with service account: {e}")
        sys.exit(1)

def check_indexing_status(service, site_url):
    """Get indexing status from Search Console API."""
    results = {
        'total_indexed': 0,
        'recently_indexed': 0,
        'crawl_errors': 0,
        'warnings': [],
        'errors': []
    }
    
    # Get overall index coverage stats
    try:
        # Get the current date and date from 7 days ago in ISO format
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Query index coverage data
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['device'],
            'rowLimit': 10
        }
        
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request
        ).execute()
        
        if 'rows' in response:
            for row in response['rows']:
                results['total_indexed'] += row.get('impressions', 0)
        
        # Get URL inspection details for recent pages (limited to 10 for demo)
        # In a real implementation, you'd want to check specific important URLs
        urls_to_check = [
            f"{site_url}sitemap.xml",
            f"{site_url}index.html",
            # Add more important URLs here
        ]
        
        for url in urls_to_check:
            try:
                inspection = service.urlInspection().index().inspect(
                    body={"inspectionUrl": url, "siteUrl": site_url}
                ).execute()
                
                index_status = inspection.get('inspectionResult', {}).get('indexStatusResult', {})
                verdict = index_status.get('verdict')
                
                if verdict == 'PASS':
                    results['recently_indexed'] += 1
                    if 'lastCrawlTime' in index_status:
                        last_crawl = index_status['lastCrawlTime']
                        print(f"URL {url} was last crawled at {last_crawl}")
                elif verdict == 'PARTIAL':
                    results['warnings'].append(f"URL {url} is partially indexed")
                elif verdict == 'FAIL':
                    results['errors'].append(f"URL {url} failed indexing: {index_status.get('verdict')}")
                    results['crawl_errors'] += 1
            except HttpError as error:
                print(f"Error inspecting URL {url}: {error}")
                
        # Check if sitemap has any errors
        try:
            sitemaps = service.sitemaps().list(siteUrl=site_url).execute()
            if 'sitemap' in sitemaps:
                for sitemap in sitemaps['sitemap']:
                    if 'errors' in sitemap and int(sitemap['errors']) > 0:
                        results['crawl_errors'] += int(sitemap['errors'])
                        results['errors'].append(f"Sitemap {sitemap.get('path')} has {sitemap['errors']} errors")
                    if 'warnings' in sitemap and int(sitemap['warnings']) > 0:
                        results['warnings'].append(f"Sitemap {sitemap.get('path')} has {sitemap['warnings']} warnings")
        except HttpError as error:
            print(f"Error checking sitemaps: {error}")
            
    except HttpError as error:
        print(f"Error checking indexing status: {error}")
        results['errors'].append(f"API error: {error}")
    
    return results

def send_notification(results, email_to, site_url):
    """Send email notification with indexing status."""
    if not os.environ.get('EMAIL_PASSWORD'):
        print("Email password not set in environment. Skipping email notification.")
        return False
    
    try:
        # Email configuration
        email_from = os.environ.get('EMAIL_FROM', 'your-email@gmail.com')
        email_password = os.environ.get('EMAIL_PASSWORD')
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = f"Google Indexing Status for {site_url}"
        
        # Create email body
        body = f"""
        <html>
        <body>
        <h2>Indexing Status Report for {site_url}</h2>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h3>Summary:</h3>
        <ul>
            <li>Total Indexed Pages (Impressions): {results['total_indexed']}</li>
            <li>Recently Checked URLs: {results['recently_indexed']}</li>
            <li>Crawl Errors: {results['crawl_errors']}</li>
        </ul>
        
        {f"<h3>Errors ({len(results['errors'])}):</h3><ul>" + "".join([f"<li>{error}</li>" for error in results['errors']]) + "</ul>" if results['errors'] else ""}
        
        {f"<h3>Warnings ({len(results['warnings'])}):</h3><ul>" + "".join([f"<li>{warning}</li>" for warning in results['warnings']]) + "</ul>" if results['warnings'] else ""}
        
        <p>For more details, please check your <a href="https://search.google.com/search-console">Google Search Console</a>.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_from, email_password)
            server.send_message(msg)
        
        print(f"Notification email sent to {email_to}")
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Monitor Google indexing status for a website')
    parser.add_argument('--site', '-s', required=True, help='Site URL (e.g., https://sednabcn.github.io/)')
    parser.add_argument('--email', '-e', help='Email to send notifications to')
    parser.add_argument('--output', '-o', help='Output file path for results (JSON format)')
    
    args = parser.parse_args()
    
    # Ensure site URL ends with trailing slash
    site_url = args.site
    if not site_url.endswith('/'):
        site_url += '/'
    
    # Get credentials and build service
    try:
        creds = get_service_account_credentials()
        service = build('searchconsole', 'v1', credentials=creds)
        print(f"Connected to Google Search Console API for site: {site_url}")
    except Exception as e:
        print(f"Failed to initialize service: {e}")
        sys.exit(1)
    
    # Check if the site is verified
    try:
        sites = service.sites().list().execute()
        site_found = False
        
        if 'siteEntry' in sites:
            for site in sites['siteEntry']:
                if site['siteUrl'] == site_url:
                    site_found = True
                    if site.get('permissionLevel') in ['siteOwner', 'siteFullUser']:
                        print(f"Site {site_url} is verified with permission level: {site.get('permissionLevel')}")
                    else:
                        print(f"WARNING: You only have {site.get('permissionLevel')} permission for this site.")
                    break
        
        if not site_found:
            print(f"WARNING: Site {site_url} is not found in your Search Console account.")
            print("You may need to verify ownership of this site first.")
            sys.exit(1)
    except HttpError as error:
        print(f"Error checking site verification: {error}")
    
    # Check indexing status
    results = check_indexing_status(service, site_url)
    
    # Print results to console
    print("\nIndexing Status Summary:")
    print(f"Total Indexed Pages (Impressions): {results['total_indexed']}")
    print(f"Recently Indexed URLs: {results['recently_indexed']}")
    print(f"Crawl Errors: {results['crawl_errors']}")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"- {error}")
    
    if results['warnings']:
        print("\nWarnings:")
        for warning in results['warnings']:
            print(f"- {warning}")
    
    # Save results to file if requested
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to {args.output}")
        except Exception as e:
            print(f"Error saving results to file: {e}")
    
    # Send email notification if requested
    if args.email:
        send_notification(results, args.email, site_url)

if __name__ == "__main__":
    main()
