#!/usr/bin/env python3
import os
import subprocess
import sys
import logging
import requests
import time
import json
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

def run_command(command):
    """Run a shell command and return the result"""
    try:
        logger.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Command failed with exit code {result.returncode}")
            logger.error(f"Error output:\n{result.stderr}")
            return False
        logger.info("Command completed successfully")
        return True
    except Exception as e:
        logger.error(f"Exception running command: {e}")
        return False

def list_directory(path="."):
    """List the contents of a directory for debugging"""
    try:
        result = subprocess.run(['ls', '-la', path], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error listing directory: {e}"

def submit_to_google_search_console(sitemap_url):
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
        
        # Get site property
        site_url = "https://sednabcn.github.io/"
        
        try:
            # Check if site is verified
            sites = service.sites().list().execute()
            verified = False
            
            logger.info(f"Available sites: {sites}")
            
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
            logger.error(f"Response content: {error.content}")
            return False
    
    except Exception as e:
        logger.error(f"Error submitting to Google Search Console: {e}")
        return False

def direct_submission(sitemap_url):
    """Direct submission to search engines via ping URLs"""
    success = True
    
    # Google submission
    google_url = f"https://www.google.com/ping?sitemap={sitemap_url}"
    try:
        logger.info(f"Submitting to Google via ping URL: {google_url}")
        response = requests.get(google_url, timeout=30)
        if response.status_code == 200:
            logger.info("Successfully pinged Google")
        else:
            logger.error(f"Failed to ping Google. Status code: {response.status_code}")
            success = False
    except Exception as e:
        logger.error(f"Error pinging Google: {e}")
        success = False
    
    # Bing submission
    bing_url = f"https://www.bing.com/ping?sitemap={sitemap_url}"
    try:
        logger.info(f"Submitting to Bing via ping URL: {bing_url}")
        response = requests.get(bing_url, timeout=30)
        if response.status_code == 200:
            logger.info("Successfully pinged Bing")
        else:
            logger.error(f"Failed to ping Bing. Status code: {response.status_code}")
            success = False
    except Exception as e:
        logger.error(f"Error pinging Bing: {e}")
        success = False
    
    return success

def main():
    """Main function to submit sitemap to search engines"""
    logger.info("Starting direct sitemap submission...")
    
    site_url = "https://sednabcn.github.io/"
    sitemap_url = "https://sednabcn.github.io/sitemap.xml"
    
    # Get current directory for debugging
    current_dir = os.getcwd()
    logger.info(f"Current working directory: {current_dir}")
    
    # List contents of current directory
    logger.info(f"Directory contents:\n{list_directory()}")
    
    # List contents of .github/scripts
    if os.path.exists(".github/scripts"):
        logger.info(f"Scripts directory contents:\n{list_directory('.github/scripts')}")
    else:
        logger.error("Scripts directory .github/scripts not found!")
    
    # Try Google Search Console API submission first
    logger.info("Attempting to submit via Google Search Console API...")
    if submit_to_google_search_console(sitemap_url):
        logger.info("Successfully submitted via Google Search Console API")
    else:
        logger.warning("Google Search Console API submission failed, trying direct submission...")
        # Fall back to direct submission
        direct_submission(sitemap_url)
    
    logger.info("Sitemap submission process completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
