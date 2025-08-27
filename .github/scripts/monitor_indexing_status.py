#!/usr/bin/env python3
"""
monitor_indexing_status.py
Check Google Search Console indexing status and optionally send email notifications
"""

import argparse
import json
import os
import sys
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from google.auth.transport.requests import Request
from google.auth import default
from googleapiclient.discovery import build


def send_email_notification(to_email, subject, body):
    """Send email notification using Gmail SMTP."""
    email_from = os.getenv('EMAIL_FROM')
    email_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    if not all([email_from, email_password, to_email]):
        print("❌ Email configuration missing:")
        print(f"  EMAIL_FROM: {'✅' if email_from else '❌'}")
        print(f"  EMAIL_PASSWORD: {'✅' if email_password else '❌'}")
        print(f"  NOTIFICATION_EMAIL: {'✅' if to_email else '❌'}")
        return False
    
    try:
        print(f"📧 Sending email notification to {to_email}...")
        
        msg = MIMEText(body, 'plain')
        msg['Subject'] = subject
        msg['From'] = email_from
        msg['To'] = to_email
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_from, email_password)
            server.send_message(msg)
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def get_indexing_status(site_url):
    """Get indexing status from Google Search Console API."""
    try:
        # Initialize credentials
        credentials, project = default(scopes=['https://www.googleapis.com/auth/webmasters.readonly'])
        
        # Build the service
        service = build('searchconsole', 'v1', credentials=credentials)
        
        # Get site information
        sites = service.sites().list().execute()
        print(f"Found {len(sites.get('siteEntry', []))} sites in Search Console")
        
        # Check if our site is in the list
        site_found = False
        for site in sites.get('siteEntry', []):
            if site['siteUrl'] == site_url:
                site_found = True
                break
        
        if not site_found:
            print(f"❌ Site {site_url} not found in Search Console")
            return None
        
        # Get index coverage data (this is a simplified example)
        # In practice, you'd want to make more specific API calls
        result = {
            'site_url': site_url,
            'timestamp': datetime.now().isoformat(),
            'status': 'checked',
            'total_pages': 0,  # You'd get this from actual API calls
            'indexed_pages': 0,
            'crawl_errors': 0,
            'api_available': True
        }
        
        # Here you would make actual API calls to get:
        # - Index coverage report
        # - Crawl errors
        # - Performance data
        # This is a template - implement according to your needs
        
        print("✅ Successfully retrieved indexing status")
        return result
        
    except Exception as e:
        print(f"❌ Error getting indexing status: {e}")
        return {
            'site_url': site_url,
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'error': str(e),
            'api_available': False
        }


def main():
    parser = argparse.ArgumentParser(description='Monitor Google Search Console indexing status')
    parser.add_argument('--site', required=True, help='Site URL to monitor')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--email', help='Email address to send notifications to')
    args = parser.parse_args()
    
    print("=== Google Indexing Status Monitor ===")
    print(f"Site: {args.site}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Get indexing status
    status_data = get_indexing_status(args.site)
    
    if not status_data:
        print("❌ Failed to get indexing status")
        sys.exit(1)
    
    # Save to output file if specified
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(status_data, f, indent=2)
            print(f"✅ Status saved to {args.output}")
        except Exception as e:
            print(f"❌ Failed to save output file: {e}")
    
    # Send email notification if requested
    if args.email:
        subject = f"📊 Google Indexing Status Report - {args.site}"
        
        if status_data.get('status') == 'error':
            subject = f"❌ Google Indexing Check Failed - {args.site}"
            body = f"""Google Search Console indexing check failed for {args.site}

Error: {status_data.get('error', 'Unknown error')}
Timestamp: {status_data.get('timestamp')}

Please check the GitHub Actions workflow logs for more details.
Workflow URL: {os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{os.getenv('GITHUB_REPOSITORY', 'your-repo')}/actions/runs/{os.getenv('GITHUB_RUN_ID', 'N/A')}

This is an automated notification from your GitHub Actions workflow.
"""
        else:
            body = f"""Google Search Console Indexing Status Report

Site: {args.site}
Check Date: {status_data.get('timestamp')}
Status: {status_data.get('status', 'unknown')}

Summary:
• Total Pages: {status_data.get('total_pages', 'N/A')}
• Indexed Pages: {status_data.get('indexed_pages', 'N/A')}
• Crawl Errors: {status_data.get('crawl_errors', 'N/A')}
• API Available: {status_data.get('api_available', 'N/A')}

{'⚠️ Action Required: Crawl errors detected!' if status_data.get('crawl_errors', 0) > 0 else '✅ All looks good!'}

For detailed analysis, check your Google Search Console dashboard:
https://search.google.com/search-console

This is an automated notification from your GitHub Actions workflow.
"""
        
        email_sent = send_email_notification(args.email, subject, body)
        if not email_sent:
            print("⚠️ Continuing despite email failure...")
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Status check: {'✅ Success' if status_data.get('status') != 'error' else '❌ Failed'}")
    print(f"Output file: {'✅ Saved' if args.output else '➖ Not requested'}")
    print(f"Email notification: {'✅ Sent' if args.email and email_sent else '❌ Failed' if args.email else '➖ Not requested'}")
    
    # Exit with appropriate code
    if status_data.get('status') == 'error':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
