#!/usr/bin/env python3
"""
Enhanced Google Sitemap Submission Tool
Combines checking and submission functionality into a single script.
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET
import requests
from typing import List, Dict, Optional, Tuple
import json
import time

# Set up global constants
USER_AGENT = "Mozilla/5.0 (compatible; SitemapSubmitter/1.0; +https://github.com/sitemap-tools)"
SEARCH_CONSOLE_API_BASE = "https://www.googleapis.com/webmasters/v3"
SITEMAP_NAMESPACE = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class SitemapTool:
    def __init__(self, site_url: str, sitemap_path: str, credentials_path: Optional[str] = None, verbose: bool = False):
        self.site_url = site_url.rstrip('/')
        self.sitemap_path = sitemap_path
        self.credentials_path = credentials_path
        self.verbose = verbose
        
        # Determine full sitemap URL
        if not sitemap_path.startswith('http'):
            self.sitemap_url = f"{self.site_url}/{sitemap_path.lstrip('/')}"
        else:
            self.sitemap_url = sitemap_path
            
        # Pre-initialize tokens to None
        self.access_token = None
    
    def log(self, message: str) -> None:
        """Print messages if verbose mode is enabled"""
        if self.verbose:
            print(message)
    
    def get_auth_token(self) -> Optional[str]:
        """Get auth token from credentials file or environment"""
        if not self.credentials_path:
            return None
            
        if not os.path.exists(self.credentials_path):
            print(f"Error: Credentials file not found at {self.credentials_path}")
            return None
            
        try:
            with open(self.credentials_path, 'r') as f:
                creds = json.load(f)
                
            if 'private_key' in creds:
                # This is a service account credentials file
                # For simplicity, we'll assume the token is already properly set up
                # In a real implementation, you'd use google-auth library to get a token
                print("Service account credentials found. In a real implementation, we'd use")
                print("google-auth to acquire a token. For this example, please use")
                print("an access token directly.")
                return None
            elif 'access_token' in creds:
                return creds['access_token']
                
        except Exception as e:
            print(f"Error reading credentials: {e}")
            
        return None
        
    def validate_sitemap(self) -> Tuple[bool, List[str]]:
        """Validate sitemap exists and contains valid URLs"""
        urls = []
        
        # If sitemap is a URL, try to download it first
        if self.sitemap_path.startswith('http'):
            try:
                response = requests.get(self.sitemap_path, headers={'User-Agent': USER_AGENT})
                if response.status_code != 200:
                    print(f"Error: Could not download sitemap. Status code: {response.status_code}")
                    return False, []
                    
                sitemap_content = response.text
                root = ET.fromstring(sitemap_content)
            except Exception as e:
                print(f"Error downloading sitemap: {e}")
                return False, []
        else:
            # Local file
            if not os.path.exists(self.sitemap_path):
                print(f"Error: Sitemap file not found at {self.sitemap_path}")
                return False, []
            
            try:
                tree = ET.parse(self.sitemap_path)
                root = tree.getroot()
            except Exception as e:
                print(f"Error parsing sitemap: {e}")
                return False, []
        
        # Find all URLs
        try:
            for url in root.findall('.//sitemap:loc', SITEMAP_NAMESPACE):
                urls.append(url.text)
                
            if not urls:
                print("Error: No URLs found in sitemap")
                return False, []
                
            print(f"Found {len(urls)} URLs in sitemap")
            return True, urls
        except Exception as e:
            print(f"Error parsing sitemap URLs: {e}")
            return False, []
    
    def check_links(self, urls: List[str]) -> List[Dict]:
        """Check all links in the sitemap for broken URLs"""
        broken_links = []
        
        print(f"Checking {len(urls)} links for availability...")
        for index, url in enumerate(urls):
            try:
                response = requests.head(url, headers={'User-Agent': USER_AGENT}, timeout=10, allow_redirects=True)
                
                if response.status_code >= 400:
                    print(f"❌ Broken link ({response.status_code}): {url}")
                    broken_links.append({
                        'url': url,
                        'status': response.status_code,
                        'error': f"HTTP {response.status_code}"
                    })
                else:
                    self.log(f"✅ Valid link: {url}")
                    
                # Add small delay to avoid rate limiting
                if index > 0 and index % 10 == 0:
                    time.sleep(1)
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Error checking: {url}")
                print(f"   {str(e)}")
                broken_links.append({
                    'url': url,
                    'status': -1,
                    'error': str(e)
                })
        
        return broken_links
    
    def check_sitemap_status(self) -> Dict:
        """Check if sitemap is already submitted and indexed by Google"""
        if not self.access_token:
            self.access_token = self.get_auth_token()
            
        if not self.access_token:
            return {
                'success': False,
                'status': 'UNKNOWN',
                'message': 'No valid authentication token available'
            }
        
        sitemap_basename = os.path.basename(self.sitemap_url)
        
        # Format site for API (add sc-domain: prefix if needed)
        api_site_url = self.site_url
        if not api_site_url.startswith('sc-domain:') and not api_site_url.startswith('http'):
            api_site_url = f"https://{api_site_url}"
        
        if 'github.io' in api_site_url and not api_site_url.startswith('sc-domain:'):
            api_site_url = f"sc-domain:{api_site_url.split('://')[1]}"
        
        # Google Search Console API endpoint for sitemaps
        api_url = f"{SEARCH_CONSOLE_API_BASE}/sites/{requests.utils.quote(api_site_url)}/sitemaps/{requests.utils.quote(sitemap_basename)}"
        
        headers = {
            'Authorization': f"Bearer {self.access_token}",
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                sitemap_data = response.json()
                return {
                    'success': True,
                    'status': sitemap_data.get('lastSubmitted', 'UNKNOWN'),
                    'lastDownloaded': sitemap_data.get('lastDownloaded', 'NEVER'),
                    'isPending': sitemap_data.get('isPending', False),
                    'message': 'Sitemap found in Google Search Console'
                }
            elif response.status_code == 404:
                return {
                    'success': True,
                    'status': 'NOT_FOUND',
                    'message': 'Sitemap not found in Google Search Console'
                }
            else:
                return {
                    'success': False,
                    'status': 'ERROR',
                    'message': f"API Error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'status': 'ERROR',
                'message': f"Exception: {str(e)}"
            }
    
    def submit_sitemap(self) -> Dict:
        """Submit sitemap to Google Search Console"""
        if not self.access_token:
            self.access_token = self.get_auth_token()
            
        if not self.access_token:
            return {
                'success': False,
                'message': 'No valid authentication token available'
            }
        
        sitemap_basename = os.path.basename(self.sitemap_url)
        
        # Format site for API (add sc-domain: prefix if needed)
        api_site_url = self.site_url
        if not api_site_url.startswith('sc-domain:') and not api_site_url.startswith('http'):
            api_site_url = f"https://{api_site_url}"
        
        if 'github.io' in api_site_url and not api_site_url.startswith('sc-domain:'):
            api_site_url = f"sc-domain:{api_site_url.split('://')[1]}"
        
        # Google Search Console API endpoint for submitting sitemaps
        api_url = f"{SEARCH_CONSOLE_API_BASE}/sites/{requests.utils.quote(api_site_url)}/sitemaps/{requests.utils.quote(sitemap_basename)}"
        
        headers = {
            'Authorization': f"Bearer {self.access_token}",
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/json'
        }
        
        try:
            # This is a PUT request for sitemap submission
            response = requests.put(api_url, headers=headers)
            
            if response.status_code in (200, 204):
                return {
                    'success': True,
                    'message': f"Sitemap {sitemap_basename} successfully submitted"
                }
            else:
                return {
                    'success': False,
                    'message': f"API Error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Exception: {str(e)}"
            }

def detect_github_site_url() -> Optional[str]:
    """Auto-detect site URL from GitHub Actions environment variables"""
    github_repo_owner = os.environ.get('GITHUB_REPOSITORY_OWNER')
    github_repo = os.environ.get('GITHUB_REPOSITORY')
    
    if github_repo and github_repo_owner:
        # Extract repository name from the full repository path (owner/repo)
        repo_name = github_repo.split('/')[-1]
        site_url = f"https://{github_repo_owner}.github.io/{repo_name}"
        return site_url
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Check and submit sitemap to Google Search Console')
    parser.add_argument('--site', help='Site URL (e.g., https://example.com)')
    parser.add_argument('--sitemap', default='sitemap.xml', help='Sitemap path or URL (e.g., sitemap.xml)')
    parser.add_argument('--credentials', help='Path to Google API credentials JSON file')
    parser.add_argument('--check-only', action='store_true', help='Only check sitemap status without submitting')
    parser.add_argument('--validate-links', action='store_true', help='Validate all URLs in the sitemap')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Auto-detect site URL if not provided
    site_url = args.site
    if not site_url:
        site_url = detect_github_site_url()
        if site_url:
            print(f"Auto-detected site URL: {site_url}")
        else:
            print("Error: Site URL not provided and could not be auto-detected")
            print("Please specify --site parameter or run this in a GitHub Actions environment")
            sys.exit(1)
    
    # Initialize sitemap tool
    tool = SitemapTool(
        site_url=site_url,
        sitemap_path=args.sitemap,
        credentials_path=args.credentials,
        verbose=args.verbose
    )
    
    # Validate sitemap structure
    is_valid, urls = tool.validate_sitemap()
    if not is_valid:
        print("Error: Invalid sitemap")
        sys.exit(1)
    
    # Check links if requested
    if args.validate_links:
        broken_links = tool.check_links(urls)
        if broken_links:
            print(f"\n❌ Found {len(broken_links)} broken links:")
            for link in broken_links:
                print(f"  - {link['url']} (Error: {link['error']})")
            print("\nFix broken links before submitting sitemap to Google.")
            sys.exit(1)
        else:
            print("✅ All links in sitemap are valid")
    
    # Check current sitemap status
    print(f"\nChecking sitemap status for {tool.sitemap_url}...")
    status = tool.check_sitemap_status()
    
    if status['success']:
        print(f"Sitemap status: {status['status']}")
        if 'lastDownloaded' in status:
            print(f"Last downloaded: {status['lastDownloaded']}")
        
        if status['status'] == 'NOT_FOUND' or status.get('lastDownloaded') == 'NEVER':
            if args.check_only:
                print("Sitemap not found or never downloaded. Use without --check-only to submit.")
            else:
                print("\nSubmitting sitemap to Google Search Console...")
                result = tool.submit_sitemap()
                if result['success']:
                    print(f"✅ {result['message']}")
                else:
                    print(f"❌ {result['message']}")
        else:
            print("✅ Sitemap already submitted and indexed by Google")
    else:
        print(f"❌ Error checking sitemap status: {status['message']}")
        if args.credentials:
            print(f"Check that your credentials file at {args.credentials} is valid")
        else:
            print("No credentials provided. Use --credentials to specify Google API credentials file")

if __name__ == "__main__":
    main()
