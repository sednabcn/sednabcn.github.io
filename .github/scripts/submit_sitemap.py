#!/usr/bin/env python3
import argparse
import logging
import requests
import sys
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def submit_to_search_console(site_url, sitemap_url):
    """Submit sitemap to Google Search Console using API"""
    try:
        # Check if credentials file exists
        if not os.path.exists('client_secret.json'):
            logger.error("Google API credentials file not found")
            return False
        
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/webmasters']
        )
        
        # Build the service
        service = build('webmasters', 'v3', credentials=credentials)
        
        try:
            # Check if site is verified
            sites = service.sites().list().execute()
            verified = False
            
            for site in sites.get('siteEntry', []):
                if site['siteUrl'] == site_url:
                    verified = site['permissionLevel'] != 'siteUnverifiedUser'
                    break
            
            if not verified:
                logger.error(f"Site {site_url} is not verified in Search Console")
                return False
            
            # Submit sitemap
            service.sitemaps().submit(siteUrl=site_url, feedpath=sitemap_url).execute()
            logger.info(f"Successfully submitted sitemap to Google Search Console: {sitemap_url}")
            return True
        
        except HttpError as error:
            logger.error(f"Google API Error: {error}")
            return False
    
    except Exception as e:
        logger.error(f"Error submitting to Google Search Console: {e}")
        return False

def submit_via_ping(sitemap_url):
    """Submit sitemap using ping URLs"""
    success = True
    
    # Google submission
    google_url = f"https://www.google.com/ping?sitemap={sitemap_url}"
    try:
        logger.info("Submitting to Google...")
        response = requests.get(google_url, timeout=30)
        if response.status_code == 200:
            logger.info("Successfully submitted to Google")
        else:
            logger.error(f"Failed to submit to Google. Status code: {response.status_code}")
            success = False
    except Exception as e:
        logger.error(f"Error submitting to Google: {e}")
        success = False
    
    # Bing submission
    bing_url = f"https://www.bing.com/ping?sitemap={sitemap_url}"
    try:
        logger.info("Submitting to Bing...")
        response = requests.get(bing_url, timeout=30)
        if response.status_code == 200:
            logger.info("Successfully submitted to Bing")
        else:
            logger.error(f"Failed to submit to Bing. Status code: {response.status_code}")
            success = False
    except Exception as e:
        logger.error(f"Error submitting to Bing: {e}")
        success = False
    
    return success

def main():
    """Main function to parse arguments and submit sitemap"""
    parser = argparse.ArgumentParser(description="Submit sitemap to search engines")
    parser.add_argument("--site", required=True, help="Base site URL (e.g., https://example.com/)")
    parser.add_argument("--sitemaps", required=True, help="URL to the sitemap (e.g., https://example.com/sitemap.xml)")
    parser.add_argument("--api", action="store_true", help="Use Google Search Console API (requires client_secret.json)")
    
    args = parser.parse_args()
    
    # Validate URLs
    if not args.site.startswith(("http://", "https://")):
        logger.error("Site URL must start with http:// or https://")
        return 1
    
    if not args.sitemaps.startswith(("http://", "https://")):
        logger.error("Sitemap URL must start with http:// or https://")
        return 1
    
    if "sitemap" not in args.sitemaps.lower():
        logger.warning("Sitemap URL doesn't contain 'sitemap' - this might be incorrect")
    
    # Try API submission first if requested
    if args.api:
        logger.info("Attempting submission via Google Search Console API...")
        if submit_to_search_console(args.site, args.sitemaps):
            logger.info("API submission successful")
            return 0
        else:
            logger.warning("API submission failed, falling back to ping URLs")
    
    # Submit via ping URLs
    success = submit_via_ping(args.sitemaps)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
