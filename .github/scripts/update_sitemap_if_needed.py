#!/usr/bin/env python3
import os
import sys
import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
import requests
import argparse

# -----------------------------
# Arguments
# -----------------------------
parser = argparse.ArgumentParser(description="Update sitemap if needed")
parser.add_argument("--base-url", type=str, required=True, help="Base URL of the site")
parser.add_argument("--output", type=str, default="sitemap.xml", help="Output sitemap file")
parser.add_argument("--config", type=str, help="Optional sitemap config JSON")
args = parser.parse_args()

BASE_URL = args.base_url.rstrip("/")
SITEMAP_FILE = args.output

# -----------------------------
# Read existing URLs from sitemap
# -----------------------------
def read_existing_urls():
    urls = set()
    if not os.path.exists(SITEMAP_FILE):
        return urls
    try:
        tree = ET.parse(SITEMAP_FILE)
        root = tree.getroot()
        ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for loc in root.findall(".//ns:loc", ns):
            urls.add(loc.text.strip())
    except Exception as e:
        print(f"⚠️ Could not parse existing sitemap: {e}")
    return urls

# -----------------------------
# Generate sitemap
# -----------------------------
def generate_sitemap():
    visited = set()
    urls_to_visit = {BASE_URL}

    while urls_to_visit:
        url = urls_to_visit.pop()
        if url in visited:
            continue
        visited.add(url)

        try:
            r = requests.get(url)
            r.raise_for_status()
        except Exception as e:
            print(f"❌ Could not fetch {url}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.find_all("a", href=True):
            abs_url = urljoin(BASE_URL, link["href"])
            abs_url, _ = urldefrag(abs_url)
            if abs_url.startswith(BASE_URL) and abs_url not in visited:
                urls_to_visit.add(abs_url)

    lastmod = datetime.date.today().isoformat()
    sitemap_entries = [
        f"""
        <url>
            <loc>{url}</loc>
            <lastmod>{lastmod}</lastmod>
        </url>
        """ for url in sorted(visited)
    ]

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(sitemap_entries)}
</urlset>
"""

    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    print(f"✅ Sitemap updated with {len(visited)} URLs → {SITEMAP_FILE}")
    return visited

# -----------------------------
# Main
# -----------------------------
existing_urls = read_existing_urls()
sitemap_needs_update = False

# Check lastmod
today = datetime.date.today().isoformat()
try:
    tree = ET.parse(SITEMAP_FILE)
    root = tree.getroot()
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    lastmod_tags = root.findall(".//ns:lastmod", ns)
    if not lastmod_tags or all(tag.text != today for tag in lastmod_tags):
        sitemap_needs_update = True
except Exception:
    sitemap_needs_update = True

# Generate new sitemap
new_urls = generate_sitemap() if sitemap_needs_update else set()
if not sitemap_needs_update:
    # If lastmod is up-to-date, check URL differences
    new_urls = generate_sitemap()
    if new_urls != existing_urls:
        print("🔄 URL changes detected, sitemap will be updated")
        sitemap_needs_update = True
    else:
        print("✅ Sitemap is up to date, no URL changes detected")

# Output for GitHub Actions
if sitemap_needs_update:
    print("changed=true")
else:
    print("changed=false")
