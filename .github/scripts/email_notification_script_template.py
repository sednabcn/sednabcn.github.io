#!/usr/bin/env python3
"""
Sitemap submission script with email notifications
"""
import os
import sys
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

def send_email(subject, body, to_email, from_email, password, smtp_server="smtp.gmail.com", smtp_port=587):
    """Send email notification"""
    try:
        print(f"Attempting to send email to {to_email}...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Gmail SMTP configuration
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable security
        server.login(from_email, password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

def parse_sitemap(sitemap_path):
    """Parse sitemap.xml and extract URLs"""
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        
        # Handle namespace
        namespace = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = []
        
        # Extract URLs
        for url_elem in root.findall('.//sitemap:url', namespace):
            loc_elem = url_elem.find('sitemap:loc', namespace)
            if loc_elem is not None:
                urls.append(loc_elem.text)
        
        return urls
    except Exception as e:
        print(f"❌ Error parsing sitemap: {e}")
        return []

def submit_to_bing(urls, api_key, site_url):
    """Submit URLs to Bing Webmaster Tools"""
    if not api_key:
        print("❌ No Bing API key provided")
        return False, "No API key"
    
    try:
        # Bing URL Submission API endpoint
        endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch?apikey={api_key}"
        
        # Prepare payload
        payload = {
            "siteUrl": site_url,
            "urlList": urls[:10]  # Bing allows max 10 URLs per request
        }
        
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
        }
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Successfully submitted URLs to Bing")
            return True, f"Submitted {len(payload['urlList'])} URLs"
        else:
            error_msg = f"Bing API returned status {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error submitting to Bing: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def main():
    parser = argparse.ArgumentParser(description='Submit sitemap to Bing and send email notification')
    parser.add_argument('--sitemap', required=True, help='Path to sitemap.xml')
    parser.add_argument('--site', required=True, help='Site URL')
    args = parser.parse_args()
    
    # Get environment variables
    email_from = os.getenv('EMAIL_FROM')
    email_password = os.getenv('EMAIL_PASSWORD')
    notification_email = os.getenv('NOTIFICATION_EMAIL')
    bing_api_key = os.getenv('BING_API_KEY')
    
    print("Starting sitemap submission process...")
    print(f"Sitemap: {args.sitemap}")
    print(f"Site: {args.site}")
    
    # Check if email credentials are available
    if not all([email_from, email_password, notification_email]):
        print("❌ Missing email configuration:")
        print(f"  EMAIL_FROM: {'✅' if email_from else '❌'}")
        print(f"  EMAIL_PASSWORD: {'✅' if email_password else '❌'}")
        print(f"  NOTIFICATION_EMAIL: {'✅' if notification_email else '❌'}")
        sys.exit(1)
    
    # Parse sitemap
    urls = parse_sitemap(args.sitemap)
    if not urls:
        print("❌ No URLs found in sitemap")
        sys.exit(1)
    
    print(f"Found {len(urls)} URLs in sitemap")
    
    # Submit to Bing
    success, result_msg = submit_to_bing(urls, bing_api_key, args.site)
    
    # Prepare email content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    if success:
        subject = f"✅ Sitemap Submission Successful - {args.site}"
        body = f"""
Sitemap submission completed successfully!

Site: {args.site}
Timestamp: {timestamp}
URLs processed: {len(urls)}
Result: {result_msg}

URLs submitted:
{chr(10).join(f"• {url}" for url in urls[:10])}
{"..." if len(urls) > 10 else ""}

This is an automated notification from GitHub Actions.
        """.strip()
    else:
        subject = f"❌ Sitemap Submission Failed - {args.site}"
        body = f"""
Sitemap submission encountered an error!

Site: {args.site}
Timestamp: {timestamp}
URLs found: {len(urls)}
Error: {result_msg}

Please check the GitHub Actions logs for more details.

This is an automated notification from GitHub Actions.
        """.strip()
    
    # Send email notification
    email_sent = send_email(
        subject=subject,
        body=body,
        to_email=notification_email,
        from_email=email_from,
        password=email_password
    )
    
    if email_sent:
        print("✅ Process completed with email notification")
    else:
        print("⚠️ Process completed but email notification failed")
        # Don't exit with error code if only email failed
    
    # Exit with appropriate code based on main operation
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
