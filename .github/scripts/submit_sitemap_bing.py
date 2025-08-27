#!/usr/bin/env python3
"""
submit_sitemap_bing.py
Extract URLs from sitemap.xml and submit each to Bing Webmaster API.
Send a summary email notification after processing.
"""

import argparse
import xml.etree.ElementTree as ET
import requests
import os
import sys
import smtplib
from email.mime.text import MIMEText
from typing import List
from datetime import datetime


# --- Email notification config ---
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587  # TLS port

EMAIL_FROM = os.getenv('EMAIL_FROM')           # Your Gmail address
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')   # Gmail App Password
EMAIL_TO = os.getenv('NOTIFICATION_EMAIL')     # Where to send notification


def check_email_config():
    """Check and display email configuration status."""
    print("\n=== Email Configuration Check ===")
    print(f"EMAIL_FROM: {'✅ Set' if EMAIL_FROM else '❌ Missing'}")
    print(f"EMAIL_PASSWORD: {'✅ Set' if EMAIL_PASSWORD else '❌ Missing'}")
    print(f"EMAIL_TO: {'✅ Set' if EMAIL_TO else '❌ Missing'}")
    
    if EMAIL_FROM:
        print(f"From email: {EMAIL_FROM}")
    if EMAIL_TO:
        print(f"To email: {EMAIL_TO}")
    
    return all([EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO])


def send_email(subject: str, body: str):
    """Send email notification using Gmail SMTP with detailed error handling."""
    print("\n=== Attempting to Send Email ===")
    
    if not check_email_config():
        print("❌ Cannot send email: Missing required environment variables")
        print("Required: EMAIL_FROM, EMAIL_PASSWORD, NOTIFICATION_EMAIL")
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    try:
        print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print("Starting TLS...")
            server.starttls()
            
            print(f"Logging in as {EMAIL_FROM}...")
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            
            print("Sending message...")
            server.send_message(msg)
            
        print("✅ Email sent successfully!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print("💡 Make sure you're using an App Password, not your regular Gmail password")
        print("💡 Enable 2FA and generate an App Password at: https://myaccount.google.com/apppasswords")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error sending email: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def parse_sitemap(file_path: str) -> List[str]:
    """Parse sitemap.xml and extract list of URLs."""
    print(f"\n=== Parsing Sitemap: {file_path} ===")
    
    if not os.path.exists(file_path):
        print(f"❌ Sitemap file not found: {file_path}")
        return []
        
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Handle different possible namespaces
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('ns:url/ns:loc', namespace)]
        
        # If no URLs found with namespace, try without
        if not urls:
            urls = [elem.text for elem in root.findall('.//loc')]
            
        print(f"✅ Found {len(urls)} URLs in sitemap")
        return urls
        
    except Exception as e:
        print(f"❌ Failed to parse sitemap: {e}")
        return []


def submit_urls_to_bing_batch(api_key: str, site_url: str, urls: List[str]) -> tuple:
    """Submit URLs to Bing using batch API (more efficient)."""
    print(f"\n=== Submitting {len(urls)} URLs to Bing (Batch) ===")
    
    # Bing batch API allows up to 10 URLs per request
    batch_size = 10
    total_success = 0
    failed_urls = []
    
    for i in range(0, len(urls), batch_size):
        batch_urls = urls[i:i + batch_size]
        print(f"Submitting batch {i//batch_size + 1}: {len(batch_urls)} URLs")
        
        endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch?apikey={api_key}"
        payload = {
            "siteUrl": site_url,
            "urlList": batch_urls
        }
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Batch submitted successfully")
                total_success += len(batch_urls)
            else:
                print(f"❌ Batch failed ({response.status_code}): {response.text}")
                failed_urls.extend(batch_urls)
                
        except requests.exceptions.Timeout:
            print(f"❌ Batch timed out")
            failed_urls.extend(batch_urls)
        except Exception as e:
            print(f"❌ Error submitting batch: {e}")
            failed_urls.extend(batch_urls)
    
    return total_success, failed_urls


def submit_url_to_bing(api_key: str, site_url: str, url: str) -> bool:
    """Submit a single URL to Bing Webmaster API (fallback method)."""
    endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrl?apikey={api_key}"
    payload = {
        "siteUrl": site_url,
        "url": url
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            print(f"✅ Submitted: {url}")
            return True
        else:
            print(f"❌ Failed ({response.status_code}): {url} — {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error submitting {url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Submit sitemap URLs to Bing and send email notification.")
    parser.add_argument('--sitemap', default='sitemap.xml', help='Path to sitemap.xml file')
    parser.add_argument('--site', required=True, help='Base site URL (e.g., https://example.com)')
    parser.add_argument('--api-key', help='Bing Webmaster API key (or set BING_API_KEY env var)')
    parser.add_argument('--use-batch', action='store_true', default=True, help='Use batch API (default: True)')
    args = parser.parse_args()

    print("=== Starting Bing Sitemap Submission ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Site: {args.site}")
    print(f"Sitemap: {args.sitemap}")

    # Check API key
    api_key = args.api_key or os.environ.get("BING_API_KEY")
    if not api_key:
        print("❌ Bing API key not provided. Use --api-key or set BING_API_KEY environment variable.")
        sys.exit(1)
    print("✅ Bing API key found")

    # Parse sitemap
    urls = parse_sitemap(args.sitemap)
    if not urls:
        print("❌ No URLs found in sitemap. Exiting.")
        # Still try to send email about the failure
        send_email(
            f"❌ Sitemap Processing Failed - {args.site}",
            f"No URLs found in sitemap file: {args.sitemap}\n"
            f"Please check the sitemap file exists and is valid.\n"
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        sys.exit(1)

    # Submit to Bing
    if args.use_batch:
        success_count, failed_urls = submit_urls_to_bing_batch(api_key, args.site, urls)
    else:
        # Individual submission (slower but more detailed feedback)
        success_count = 0
        failed_urls = []
        for url in urls:
            if submit_url_to_bing(api_key, args.site, url):
                success_count += 1
            else:
                failed_urls.append(url)

    # Compose email summary
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    subject = f"📊 Bing Sitemap Submission Report - {args.site}"
    
    body = f"""Bing Sitemap Submission Complete

Site: {args.site}
Sitemap file: {args.sitemap}
Timestamp: {timestamp}

RESULTS:
• Total URLs processed: {len(urls)}
• Successfully submitted: {success_count}
• Failed submissions: {len(failed_urls)}
• Success rate: {(success_count/len(urls)*100):.1f}%

"""

    if failed_urls:
        body += f"\nFAILED URLs ({len(failed_urls)}):\n"
        body += "\n".join(f"• {url}" for url in failed_urls[:20])
        if len(failed_urls) > 20:
            body += f"\n... and {len(failed_urls) - 20} more"

    body += f"\n\nThis notification was sent from GitHub Actions."

    # Send email (this will now show detailed debug info)
    email_sent = send_email(subject, body)
    
    print(f"\n=== Summary ===")
    print(f"URLs processed: {len(urls)}")
    print(f"Successfully submitted: {success_count}")
    print(f"Failed: {len(failed_urls)}")
    print(f"Email notification: {'✅ Sent' if email_sent else '❌ Failed'}")

    # Always try to send email, but don't fail the whole job if email fails
    if success_count > 0:
        print("✅ Bing submission completed successfully")
        sys.exit(0)
    else:
        print("❌ All Bing submissions failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
