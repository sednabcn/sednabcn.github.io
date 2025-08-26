#!/usr/bin/env python3
"""
Sitemap CLI Management Tool
A companion script for manual sitemap management and diagnostics
"""

import os
import sys
import json
import argparse
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from tabulate import tabulate
    import colorama
    from colorama import Fore, Style, Back
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Install with: pip install google-api-python-client google-auth-oauthlib tabulate colorama")
    sys.exit(1)

colorama.init()

class SitemapCLI:
    def __init__(self, service_account_path: str):
        self.service_account_path = service_account_path
        self.service = None
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Google Search Console API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=['https://www.googleapis.com/auth/webmasters']
            )
            self.service = build('webmasters', 'v3', credentials=credentials)
            self.authenticated = True
            print(f"{Fore.GREEN}✅ Successfully authenticated with Google Search Console{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Authentication failed: {e}{Style.RESET_ALL}")
            return False
    
    def list_sites(self):
        """List all verified sites in Search Console"""
        if not self.authenticated and not self.authenticate():
            return
        
        try:
            sites = self.service.sites().list().execute()
            site_list = sites.get('siteEntry', [])
            
            if not site_list:
                print(f"{Fore.YELLOW}No sites found in Search Console{Style.RESET_ALL}")
                return
            
            print(f"\n{Fore.CYAN}📊 Verified Sites in Google Search Console{Style.RESET_ALL}")
            print("="*60)
            
            table_data = []
            for site in site_list:
                site_url = site.get('siteUrl', '')
                permission_level = site.get('permissionLevel', 'Unknown')
                table_data.append([site_url, permission_level])
            
            print(tabulate(table_data, headers=['Site URL', 'Permission Level'], tablefmt='grid'))
            
        except HttpError as e:
            print(f"{Fore.RED}❌ Failed to list sites: {e}{Style.RESET_ALL}")
    
    def list_sitemaps(self, site_url: str):
        """List all sitemaps for a specific site"""
        if not self.authenticated and not self.authenticate():
            return
        
        try:
            sitemaps = self.service.sitemaps().list(siteUrl=site_url).execute()
            sitemap_list = sitemaps.get('sitemap', [])
            
            if not sitemap_list:
                print(f"{Fore.YELLOW}No sitemaps found for {site_url}{Style.RESET_ALL}")
                return
            
            print(f"\n{Fore.CYAN}🗺️ Sitemaps for {site_url}{Style.RESET_ALL}")
            print("="*80)
            
            table_data = []
            for sitemap in sitemap_list:
                path = sitemap.get('path', '')
                last_submitted = sitemap.get('lastSubmitted', 'Never')
                last_downloaded = sitemap.get('lastDownloaded', 'Never')
                is_pending = '⏳ Yes' if sitemap.get('isPending', False) else '✅ No'
                warnings = sitemap.get('warnings', 0)
                errors = sitemap.get('errors', 0)
                
                status = f"{Fore.GREEN}✅ OK{Style.RESET_ALL}"
                if errors > 0:
                    status = f"{Fore.RED}❌ {errors} errors{Style.RESET_ALL}"
                elif warnings > 0:
                    status = f"{Fore.YELLOW}⚠️ {warnings} warnings{Style.RESET_ALL}"
                
                table_data.append([
                    path, status, is_pending, last_submitted, last_downloaded
                ])
            
            print(tabulate(table_data, headers=[
                'Sitemap Path', 'Status', 'Pending', 'Last Submitted', 'Last Downloaded'
            ], tablefmt='grid'))
            
        except HttpError as e:
            print(f"{Fore.RED}❌ Failed to list sitemaps: {e}{Style.RESET_ALL}")
    
    def validate_sitemap(self, sitemap_url: str) -> tuple:
        """Validate sitemap URL and content"""
        print(f"{Fore.CYAN}🔍 Validating sitemap: {sitemap_url}{Style.RESET_ALL}")
        
        try:
            response = requests.get(sitemap_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; SitemapValidator/1.0)'
            })
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}: {response.reason}"
            
            # Parse XML
            try:
                root = ET.fromstring(response.content)
                namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                # Check if it's a sitemap or sitemap index
                if root.tag.endswith('sitemapindex'):
                    sitemaps = root.findall('.//sm:sitemap', namespace)
                    return True, f"Valid sitemap index with {len(sitemaps)} sitemaps"
                elif root.tag.endswith('urlset'):
                    urls = root.findall('.//sm:url', namespace)
                    return True, f"Valid sitemap with {len(urls)} URLs"
                else:
                    return False, "Not a valid sitemap XML format"
                    
            except ET.ParseError as e:
                return False, f"XML parsing error: {e}"
                
        except requests.RequestException as e:
            return False, f"Request failed: {e}"
    
    def analyze_sitemap(self, sitemap_url: str):
        """Perform detailed sitemap analysis"""
        print(f"\n{Fore.CYAN}📊 Analyzing sitemap: {sitemap_url}{Style.RESET_ALL}")
        print("="*60)
        
        is_valid, message = self.validate_sitemap(sitemap_url)
        
        if not is_valid:
            print(f"{Fore.RED}❌ Validation failed: {message}{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        
        try:
            response = requests.get(sitemap_url, timeout=30)
            root = ET.fromstring(response.content)
            namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            analysis = {
                'total_urls': 0,
                'urls_with_lastmod': 0,
                'urls_with_priority': 0,
                'urls_with_changefreq': 0,
                'url_protocols': {},
                'issues': []
            }
            
            if root.tag.endswith('urlset'):
                urls = root.findall('.//sm:url', namespace)
                analysis['total_urls'] = len(urls)
                
                for url in urls:
                    loc = url.find('sm:loc', namespace)
                    lastmod = url.find('sm:lastmod', namespace)
                    priority = url.find('sm:priority', namespace)
                    changefreq = url.find('sm:changefreq', namespace)
                    
                    if loc is not None:
                        parsed_url = urlparse(loc.text)
                        protocol = parsed_url.scheme
                        analysis['url_protocols'][protocol] = analysis['url_protocols'].get(protocol, 0) + 1
                        
                        if not parsed_url.scheme in ['http', 'https']:
                            analysis['issues'].append(f"Invalid URL protocol: {loc.text}")
                    
                    if lastmod is not None:
                        analysis['urls_with_lastmod'] += 1
                    
                    if priority is not None:
                        analysis['urls_with_priority'] += 1
                        try:
                            priority_val = float(priority.text)
                            if not 0.0 <= priority_val <= 1.0:
                                analysis['issues'].append(f"Invalid priority value: {priority.text}")
                        except ValueError:
                            analysis['issues'].append(f"Invalid priority format: {priority.text}")
                    
                    if changefreq is not None:
                        analysis['urls_with_changefreq'] += 1
                        valid_changefreq = ['always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never']
                        if changefreq.text not in valid_changefreq:
                            analysis['issues'].append(f"Invalid changefreq value: {changefreq.text}")
            
            # Display analysis results
            print(f"\n{Fore.YELLOW}📈 Analysis Results:{Style.RESET_ALL}")
            print(f"Total URLs: {analysis['total_urls']}")
            print(f"URLs with lastmod: {analysis['urls_with_lastmod']} ({analysis['urls_with_lastmod']/analysis['total_urls']*100:.1f}%)")
            print(f"URLs with priority: {analysis['urls_with_priority']} ({analysis['urls_with_priority']/analysis['total_urls']*100:.1f}%)")
            print(f"URLs with changefreq: {analysis['urls_with_changefreq']} ({analysis['urls_with_changefreq']/analysis['total_urls']*100:.1f}%)")
            
            if analysis['url_protocols']:
                print(f"\nURL Protocols:")
                for protocol, count in analysis['url_protocols'].items():
                    print(f"  {protocol}: {count}")
            
            # Recommendations
            recommendations = []
            if analysis['urls_with_lastmod'] < analysis['total_urls'] * 0.8:
                recommendations.append("Consider adding <lastmod> tags to more URLs")
            if analysis['urls_with_priority'] < analysis['total_urls'] * 0.5:
                recommendations.append("Consider adding <priority> tags to important URLs")
            if analysis['total_urls'] > 50000:
                recommendations.append("Sitemap exceeds 50k URLs, consider splitting")
            if 'http' in analysis['url_protocols']:
                recommendations.append("Consider migrating HTTP URLs to HTTPS")
            
            if recommendations:
                print(f"\n{Fore.CYAN}💡 Recommendations:{Style.RESET_ALL}")
                for rec in recommendations:
                    print(f"  • {rec}")
            
            if analysis['issues']:
                print(f"\n{Fore.RED}⚠️ Issues Found:{Style.RESET_ALL}")
                for issue in analysis['issues']:
                    print(f"  • {issue}")
            else:
                print(f"\n{Fore.GREEN}✅ No issues found!{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}❌ Analysis failed: {e}{Style.RESET_ALL}")
    
    def submit_sitemap(self, site_url: str, sitemap_url: str):
        """Submit sitemap to Google Search Console"""
        if not self.authenticated and not self.authenticate():
            return
        
        print(f"{Fore.CYAN}📤 Submitting sitemap to Google Search Console...{Style.RESET_ALL}")
        print(f"Site: {site_url}")
        print(f"Sitemap: {sitemap_url}")
        
        # Validate first
        is_valid, message = self.validate_sitemap(sitemap_url)
        if not is_valid:
            print(f"{Fore.RED}❌ Validation failed: {message}{Style.RESET_ALL}")
            print("Cannot submit invalid sitemap")
            return
        
        try:
            self.service.sitemaps().submit(
                siteUrl=site_url,
                feedpath=sitemap_url
            ).execute()
            print(f"{Fore.GREEN}✅ Successfully submitted sitemap!{Style.RESET_ALL}")
            
        except HttpError as e:
            print(f"{Fore.RED}❌ Failed to submit sitemap: {e}{Style.RESET_ALL}")
    
    def delete_sitemap(self, site_url: str, sitemap_url: str):
        """Delete sitemap from Google Search Console"""
        if not self.authenticated and not self.authenticate():
            return
        
        print(f"{Fore.YELLOW}🗑️ Deleting sitemap from Google Search Console...{Style.RESET_ALL}")
        print(f"Site: {site_url}")
        print(f"Sitemap: {sitemap_url}")
        
        confirm = input(f"{Fore.YELLOW}Are you sure? (y/N): {Style.RESET_ALL}")
        if confirm.lower() != 'y':
            print("Cancelled")
            return
        
        try:
            self.service.sitemaps().delete(
                siteUrl=site_url,
                feedpath=sitemap_url
            ).execute()
            print(f"{Fore.GREEN}✅ Successfully deleted sitemap!{Style.RESET_ALL}")
            
        except HttpError as e:
            print(f"{Fore.RED}❌ Failed to delete sitemap: {e}{Style.RESET_ALL}")
    
    def get_sitemap_status(self, site_url: str, sitemap_url: str):
        """Get detailed sitemap status"""
        if not self.authenticated and not self.authenticate():
            return
        
        try:
            result = self.service.sitemaps().get(
                siteUrl=site_url,
                feedpath=sitemap_url
            ).execute()
            
            print(f"\n{Fore.CYAN}📊 Sitemap Status for {sitemap_url}{Style.RESET_ALL}")
            print("="*60)
            
            status_data = [
                ['Type', result.get('type', 'Unknown')],
                ['Is Pending', '⏳ Yes' if result.get('isPending', False) else '✅ No'],
                ['Is Sitemap Index', '📑 Yes' if result.get('isSitemapsIndex', False) else '📄 No'],
                ['Last Submitted', result.get('lastSubmitted', 'Never')],
                ['Last Downloaded', result.get('lastDownloaded', 'Never')],
                ['Warnings', result.get('warnings', 0)],
                ['Errors', result.get('errors', 0)]
            ]
            
            print(tabulate(status_data, headers=['Property', 'Value'], tablefmt='grid'))
            
            # Show contents if available
            contents = result.get('contents', [])
            if contents:
                print(f"\n{Fore.CYAN}📄 Content Summary:{Style.RESET_ALL}")
                content_data = []
                for content in contents:
                    content_type = content.get('type', 'Unknown')
                    submitted = content.get('submitted', 0)
                    indexed = content.get('indexed', 0)
                    content_data.append([content_type, submitted, indexed])
                
                print(tabulate(content_data, headers=['Content Type', 'Submitted', 'Indexed'], tablefmt='grid'))
            
        except HttpError as e:
            print(f"{Fore.RED}❌ Failed to get sitemap status: {e}{Style.RESET_ALL}")
    
    def monitor_sitemaps(self, site_url: str, interval: int = 300):
        """Monitor sitemap processing status"""
        if not self.authenticated and not self.authenticate():
            return
        
        print(f"{Fore.CYAN}👀 Monitoring sitemaps for {site_url}{Style.RESET_ALL}")
        print(f"Check interval: {interval} seconds")
        print("Press Ctrl+C to stop monitoring\n")
        
        try:
            while True:
                try:
                    sitemaps = self.service.sitemaps().list(siteUrl=site_url).execute()
                    sitemap_list = sitemaps.get('sitemap', [])
                    
                    if not sitemap_list:
                        print(f"{Fore.YELLOW}No sitemaps found{Style.RESET_ALL}")
                        break
                    
                    current_time = datetime.now().strftime("%H:%M:%S")
                    print(f"{Fore.CYAN}[{current_time}] Sitemap Status:{Style.RESET_ALL}")
                    
                    table_data = []
                    for sitemap in sitemap_list:
                        path = sitemap.get('path', '').split('/')[-1]  # Show only filename
                        is_pending = '⏳' if sitemap.get('isPending', False) else '✅'
                        errors = sitemap.get('errors', 0)
                        warnings = sitemap.get('warnings', 0)
                        
                        status_icon = '✅'
                        if errors > 0:
                            status_icon = '❌'
                        elif warnings > 0:
                            status_icon = '⚠️'
                        
                        table_data.append([path, status_icon, is_pending, errors, warnings])
                    
                    print(tabulate(table_data, headers=['Sitemap', 'Status', 'Pending', 'Errors', 'Warnings'], tablefmt='simple'))
                    print("-" * 50)
                    
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}Monitoring stopped by user{Style.RESET_ALL}")
                    break
                except Exception as e:
                    print(f"{Fore.RED}Error during monitoring: {e}{Style.RESET_ALL}")
                    time.sleep(interval)
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Monitoring failed: {e}{Style.RESET_ALL}")
    
    def export_sitemap_report(self, site_url: str, output_file: str):
        """Export detailed sitemap report to JSON"""
        if not self.authenticated and not self.authenticate():
            return
        
        print(f"{Fore.CYAN}📊 Generating sitemap report for {site_url}{Style.RESET_ALL}")
        
        try:
            sitemaps = self.service.sitemaps().list(siteUrl=site_url).execute()
            sitemap_list = sitemaps.get('sitemap', [])
            
            if not sitemap_list:
                print(f"{Fore.YELLOW}No sitemaps found{Style.RESET_ALL}")
                return
            
            report = {
                'site_url': site_url,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_sitemaps': len(sitemap_list),
                'sitemaps': []
            }
            
            for sitemap in sitemap_list:
                sitemap_data = {
                    'path': sitemap.get('path', ''),
                    'type': sitemap.get('type', 'Unknown'),
                    'is_pending': sitemap.get('isPending', False),
                    'is_sitemaps_index': sitemap.get('isSitemapsIndex', False),
                    'last_submitted': sitemap.get('lastSubmitted', None),
                    'last_downloaded': sitemap.get('lastDownloaded', None),
                    'warnings': sitemap.get('warnings', 0),
                    'errors': sitemap.get('errors', 0),
                    'contents': sitemap.get('contents', [])
                }
                
                # Add validation results
                is_valid, validation_msg = self.validate_sitemap(sitemap.get('path', ''))
                sitemap_data['validation'] = {
                    'is_valid': is_valid,
                    'message': validation_msg
                }
                
                report['sitemaps'].append(sitemap_data)
            
            # Write to file
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"{Fore.GREEN}✅ Report exported to {output_file}{Style.RESET_ALL}")
            
        except HttpError as e:
            print(f"{Fore.RED}❌ Failed to generate report: {e}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Error writing report: {e}{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(
        description='Sitemap CLI Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --auth service-account.json list-sites
  %(prog)s --auth service-account.json list-sitemaps https://example.com/
  %(prog)s --auth service-account.json analyze https://example.com/sitemap.xml
  %(prog)s --auth service-account.json submit https://example.com/ https://example.com/sitemap.xml
  %(prog)s --auth service-account.json monitor https://example.com/ --interval 60
  %(prog)s --auth service-account.json export https://example.com/ report.json
        """
    )
    
    parser.add_argument('--auth', required=True, metavar='PATH',
                      help='Path to Google service account JSON file')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List sites command
    subparsers.add_parser('list-sites', help='List all verified sites')
    
    # List sitemaps command
    list_parser = subparsers.add_parser('list-sitemaps', help='List sitemaps for a site')
    list_parser.add_argument('site_url', help='Site URL (e.g., https://example.com/)')
    
    # Analyze sitemap command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a sitemap')
    analyze_parser.add_argument('sitemap_url', help='Sitemap URL')
    
    # Submit sitemap command
    submit_parser = subparsers.add_parser('submit', help='Submit sitemap to Search Console')
    submit_parser.add_argument('site_url', help='Site URL (e.g., https://example.com/)')
    submit_parser.add_argument('sitemap_url', help='Sitemap URL')
    
    # Delete sitemap command
    delete_parser = subparsers.add_parser('delete', help='Delete sitemap from Search Console')
    delete_parser.add_argument('site_url', help='Site URL (e.g., https://example.com/)')
    delete_parser.add_argument('sitemap_url', help='Sitemap URL')
    
    # Get status command
    status_parser = subparsers.add_parser('status', help='Get sitemap status')
    status_parser.add_argument('site_url', help='Site URL (e.g., https://example.com/)')
    status_parser.add_argument('sitemap_url', help='Sitemap URL')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor sitemap processing')
    monitor_parser.add_argument('site_url', help='Site URL (e.g., https://example.com/)')
    monitor_parser.add_argument('--interval', type=int, default=300, 
                              help='Check interval in seconds (default: 300)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export sitemap report to JSON')
    export_parser.add_argument('site_url', help='Site URL (e.g., https://example.com/)')
    export_parser.add_argument('output_file', help='Output JSON file path')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a sitemap (no auth required)')
    validate_parser.add_argument('sitemap_url', help='Sitemap URL')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Special case for validate command (doesn't need auth)
    if args.command == 'validate':
        cli = SitemapCLI('')  # Empty auth path
        is_valid, message = cli.validate_sitemap(args.sitemap_url)
        if is_valid:
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
            cli.analyze_sitemap(args.sitemap_url)
        else:
            print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
        sys.exit(0)
    
    # Check if service account file exists
    if not os.path.exists(args.auth):
        print(f"{Fore.RED}❌ Service account file not found: {args.auth}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Initialize CLI
    cli = SitemapCLI(args.auth)
    
    # Execute commands
    try:
        if args.command == 'list-sites':
            cli.list_sites()
            
        elif args.command == 'list-sitemaps':
            cli.list_sitemaps(args.site_url)
            
        elif args.command == 'analyze':
            cli.analyze_sitemap(args.sitemap_url)
            
        elif args.command == 'submit':
            cli.submit_sitemap(args.site_url, args.sitemap_url)
            
        elif args.command == 'delete':
            cli.delete_sitemap(args.site_url, args.sitemap_url)
            
        elif args.command == 'status':
            cli.get_sitemap_status(args.site_url, args.sitemap_url)
            
        elif args.command == 'monitor':
            cli.monitor_sitemaps(args.site_url, args.interval)
            
        elif args.command == 'export':
            cli.export_sitemap_report(args.site_url, args.output_file)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == '__main__':
    main()

#Complete main() function with full argument parsing for all commands:

# list-sites - List verified sites
# list-sitemaps - List sitemaps for a site
# analyze - Analyze sitemap structure and content
# submit - Submit sitemap to Search Console
# delete - Delete sitemap from Search Console
# status - Get detailed sitemap status
# monitor - Monitor sitemap processing in real-time
# export - Export detailed JSON reports
# validate - Validate sitemap (no auth required)
