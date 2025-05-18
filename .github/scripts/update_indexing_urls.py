#!/usr/bin/env python3
"""
Script to extract all URLs from sitemap.xml and request Google to index them.
This script parses the sitemap.xml file and creates commands to request indexing
for all URLs found in the sitemap.
"""

import os
import sys
import xml.etree.ElementTree as ET
import subprocess
import argparse
from datetime import datetime
import time

def parse_sitemap(sitemap_path):
    """
    Parse the sitemap XML file and extract all URLs.
    
    Args:
        sitemap_path (str): Path to the sitemap.xml file
    
    Returns:
        list: List of all URLs found in the sitemap
    """
    try:
        # Define namespaces
        namespaces = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'image': 'http://www.google.com/schemas/sitemap-image/1.1'
        }
        
        # Parse the XML file
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        
        # Extract all URLs
        urls = []
        for url_element in root.findall(".//ns:url", namespaces):
            loc_element = url_element.find("ns:loc", namespaces)
            if loc_element is not None and loc_element.text:
                urls.append(loc_element.text)
        
        return urls
    
    except Exception as e:
        print(f"Error parsing sitemap: {e}")
        return []

def request_indexing(site, urls, delay=5, dry_run=False):
    """
    Request Google to index all provided URLs.
    
    Args:
        site (str): The site domain registered in Search Console
        urls (list): List of URLs to request indexing for
        delay (int): Delay between requests in seconds to avoid rate limiting
        dry_run (bool): If True, only print commands without executing
    """
    log_file = f"indexing_request_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print(f"Starting indexing requests for {len(urls)} URLs")
    print(f"Logging results to {log_file}")
    
    with open(log_file, "w") as log:
        log.write(f"Indexing request log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Site: {site}\n")
        log.write("-" * 80 + "\n\n")
        
        for i, url in enumerate(urls):
            command = f"python3.12 ./scripts/search_console_management_.py --site {site} request-indexing {url}"
            
            log.write(f"[{i+1}/{len(urls)}] {url}\n")
            log.write(f"Command: {command}\n")
            
            print(f"Processing [{i+1}/{len(urls)}]: {url}")
            
            if dry_run:
                print(f"DRY RUN: {command}")
                log.write("DRY RUN - Command not executed\n\n")
            else:
                try:
                    result = subprocess.run(
                        command, 
                        shell=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    log.write(f"Status: {result.returncode}\n")
                    log.write(f"Output: {result.stdout}\n")
                    
                    if result.stderr:
                        log.write(f"Error: {result.stderr}\n")
                    
                    log.write("\n")
                    
                    # Add delay between requests to prevent rate limiting
                    if i < len(urls) - 1:  # Don't delay after the last URL
                        time.sleep(delay)
                
                except Exception as e:
                    error_msg = f"Failed to execute command: {e}"
                    print(error_msg)
                    log.write(f"{error_msg}\n\n")
    
    print(f"Completed indexing requests. See {log_file} for detailed log.")

def main():
    parser = argparse.ArgumentParser(description="Request Google to index URLs from sitemap")
    parser.add_argument("--site", required=True, help="The site domain registered in Search Console")
    parser.add_argument("--sitemap", default="sitemap.xml", help="Path to sitemap.xml file")
    parser.add_argument("--delay", type=int, default=5, help="Delay between requests in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    args = parser.parse_args()
    
    # Parse sitemap to extract URLs
    urls = parse_sitemap(args.sitemap)
    
    if not urls:
        print("No URLs found in the sitemap. Exiting.")
        sys.exit(1)
    
    print(f"Found {len(urls)} URLs in sitemap")
    
    # Request indexing for each URL
    request_indexing(args.site, urls, delay=args.delay, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
