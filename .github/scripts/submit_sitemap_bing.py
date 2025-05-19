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


# --- Email notification config ---
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587  # TLS port

EMAIL_FROM = os.getenv('EMAIL_FROM')           # Your Gmail address
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')   # Gmail App Password
EMAIL_TO = os.getenv('NOTIFICATION_EMAIL')     # Where to send notification


def send_email(subject: str, body: str):
    """Send email notification using Gmail SMTP."""
    if not all([EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO]):
        print("⚠️ Email not sent: Missing email config environment variables.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 Notification email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email notification: {e}")


def parse_sitemap(file_path: str) -> List[str]:
    """Parse sitemap.xml and extract list of URLs."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('ns:url/ns:loc', namespace)]
        return urls
    except Exception as e:
        print(f"❌ Failed to parse sitemap: {e}")
        return []


def submit_url_to_bing(api_key: str, site_url: str, url: str) -> bool:
    """Submit a single URL to Bing Webmaster API."""
    endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrl?apikey={api_key}"
    payload = {
        "siteUrl": site_url,
        "url": url
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
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
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("BING_API_KEY")
    if not api_key:
        print("❌ Bing API key not provided. Use --api-key or set BING_API_KEY environment variable.")
        sys.exit(1)

    urls = parse_sitemap(args.sitemap)
    if not urls:
        print("❌ No URLs found in sitemap. Exiting.")
        sys.exit(1)

    print(f"📦 Submitting {len(urls)} URLs from sitemap '{args.sitemap}' to Bing...")

    success_count = 0
    failed_urls = []

    for url in urls:
        if submit_url_to_bing(api_key, args.site, url):
            success_count += 1
        else:
            failed_urls.append(url)

    # Compose email summary
    subject = f"Bing Sitemap Submission Report for {args.site}"
    body = (
        f"Sitemap file: {args.sitemap}\n"
        f"Total URLs processed: {len(urls)}\n"
        f"Successfully submitted: {success_count}\n"
        f"Failed submissions: {len(failed_urls)}\n"
    )

    if failed_urls:
        body += "\nFailed URLs:\n" + "\n".join(failed_urls)

    send_email(subject, body)


if __name__ == "__main__":
    main()
