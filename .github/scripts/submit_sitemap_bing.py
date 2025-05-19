#!/usr/bin/env python3
"""
Extract URLs from sitemap.xml and submit them to Bing.
"""

import argparse
import xml.etree.ElementTree as ET
import requests
import os
import sys
from typing import List

def parse_sitemap(file_path: str) -> List[str]:
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
    endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrl?apikey={api_key}"
    payload = {
        "siteUrl": site_url,
        "url": url
    }
    try:
        response = requests.post(endpoint, json=payload, headers={'Content-Type': 'application/json'})
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--sitemap', default='sitemap.xml', help='Path to sitemap.xml')
    parser.add_argument('--site', required=True, help='Base site URL (e.g., https://sednabcn.github.io)')
    parser.add_argument('--api-key', help='Bing Webmaster API key')
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("BING_API_KEY")
    if not api_key:
        print("❌ Bing API key not provided. Use --api-key or set BING_API_KEY.")
        sys.exit(1)

    urls = parse_sitemap(args.sitemap)
    if not urls:
        print("❌ No URLs found. Exiting.")
        sys.exit(1)

    print(f"📦 Submitting {len(urls)} URLs to Bing...")
    for url in urls:
        submit_url_to_bing(api_key, args.site, url)

if __name__ == "__main__":
    main()
