#!/usr/bin/env python3
import os
import requests
import argparse
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def submit_sitemap(site_url, sitemap_url):
    """
    Submit a sitemap to Google using the Indexing API
    
    Args:
        site_url (str): The website URL (e.g., https://example.com/)
        sitemap_url (str): The sitemap URL (e.g., https://example.com/sitemap.xml)
    
    Returns:
        bool: True if submission was successful, False otherwise
    """
    try:
        # Path to the service account JSON key file
        key_file = "client_secret.json"
        
        if not os.path.exists(key_file):
            print(f"Error: Service account key file {key_file} not found")
            return False
        
        # Print the key file contents (for debugging)
        with open(key_file, 'r') as f:
            key_data = json.load(f)
            print(f"Found key for service account: {key_data.get('client_email', 'unknown')}")
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_file(
            key_file, 
            scopes=['https://www.googleapis.com/auth/indexing']
        )
        
        # Build the service
        service = build('indexing', 'v3', credentials=credentials)
        
        # Notify Google of the sitemap
        print(f"Submitting sitemap {sitemap_url} for site {site_url}")
        
        # Use the Search Console API to submit sitemap
        # Note: This requires different permissions than the Indexing API
        # If you have the right scopes, you could use:
        # webmasters_service = build('webmasters', 'v3', credentials=credentials)
        # webmasters_service.sitemaps().submit(siteUrl=site_url, feedpath=sitemap_url).execute()
        
        # Alternative approach: Submit sitemap URL directly to the Indexing API
        response = service.urlNotifications().publish(
            body={"url": sitemap_url, "type": "URL_UPDATED"}
        ).execute()
        
        print(f"Response: {response}")
        return True
        
    except HttpError as error:
        print(f"An HTTP error occurred: {error}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Submit sitemap to Google Search Console.')
    parser.add_argument('--site', required=True, help='The site URL (e.g., https://example.com/)')
    parser.add_argument('--sitemaps', required=True, help='The sitemap URL (e.g., https://example.com/sitemap.xml)')
    
    args = parser.parse_args()
    
    # Submit the sitemap
    success = submit_sitemap(args.site, args.sitemaps)
    
    # Exit with appropriate status code
    if success:
        print("Sitemap submission completed successfully")
        exit(0)
    else:
        print("Sitemap submission failed")
        exit(1)

if __name__ == "__main__":
    main()
