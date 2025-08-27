#!/usr/bin/env python3
import os, sys, json, argparse
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import requests
import xml.etree.ElementTree as ET
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class SitemapMonitor:
    def __init__(self, service_account_path: str):
        self.service_account_path = service_account_path
        self.service = None
        self.site_url = None
        self.results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'site_url': None,
            'sitemaps': [],
            'issues_found': [],
            'fixes_applied': [],
            'summary': {}
        }

    def authenticate(self) -> bool:
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=['https://www.googleapis.com/auth/webmasters']
            )
            self.service = build('webmasters', 'v3', credentials=credentials)
            print("✅ Authenticated with Google Search Console")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            self.results['issues_found'].append(f"Authentication failed: {e}")
            return False

    def validate_sitemap_url(self, sitemap_url: str) -> Tuple[bool, str]:
        try:
            response = requests.get(sitemap_url, timeout=30, headers={
                'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)'
            })
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}: {response.reason}"
            try:
                root = ET.fromstring(response.content)
                if root.tag.endswith('sitemapindex') or root.tag.endswith('urlset'):
                    url_count = len(root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'))
                    sitemap_count = len(root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'))
                    if url_count > 0:
                        return True, f"Valid sitemap with {url_count} URLs"
                    elif sitemap_count > 0:
                        return True, f"Valid sitemap index with {sitemap_count} sitemaps"
                    else:
                        return False, "Sitemap contains no URLs"
                else:
                    return False, "Not a valid sitemap format"
            except ET.ParseError as e:
                return False, f"XML parsing error: {e}"
        except requests.RequestException as e:
            return False, f"Request failed: {e}"

    def get_sitemap_status(self, site_url: str, sitemap_url: str) -> Dict:
        try:
            result = self.service.sitemaps().get(
                siteUrl=site_url,
                feedpath=sitemap_url
            ).execute()
            return {
                'url': sitemap_url,
                'status': 'submitted',
                'errors': result.get('errors', 0),
                'warnings': result.get('warnings', 0),
                'isPending': result.get('isPending', False),
                'lastDownloaded': result.get('lastDownloaded'),
            }
        except HttpError as e:
            if e.resp.status == 404:
                return {'url': sitemap_url, 'status': 'not_submitted', 'error': 'Not in GSC'}
            else:
                return {'url': sitemap_url, 'status': 'error', 'error': str(e)}

    def submit_sitemap(self, site_url: str, sitemap_url: str) -> bool:
        try:
            self.service.sitemaps().submit(siteUrl=site_url, feedpath=sitemap_url).execute()
            self.results['fixes_applied'].append(f"Submitted {sitemap_url}")
            return True
        except HttpError as e:
            self.results['issues_found'].append(f"Submit failed: {e}")
            return False

    def monitor_sitemaps(self, site_url: str, sitemap_urls: List[str], force_resubmit: bool = False):
        self.site_url = site_url
        self.results['site_url'] = site_url
        if not self.authenticate(): return self.results

        for sitemap_url in sitemap_urls:
            valid, msg = self.validate_sitemap_url(sitemap_url)
            entry = {'url': sitemap_url, 'validation': {'is_valid': valid, 'message': msg}}
            if not valid:
                entry['status'] = 'validation_failed'
                self.results['issues_found'].append(f"Validation failed {sitemap_url}: {msg}")
            else:
                status = self.get_sitemap_status(site_url, sitemap_url)
                entry.update(status)
                if status['status'] == 'not_submitted' or force_resubmit:
                    if self.submit_sitemap(site_url, sitemap_url):
                        entry['action'] = 'submitted'
                elif status['status'] == 'submitted' and status['errors'] > 0:
                    self.submit_sitemap(site_url, sitemap_url)
                    entry['action'] = f're-submitted (errors={status["errors"]})'
                else:
                    entry['action'] = 'healthy'
            self.results['sitemaps'].append(entry)

        self.results['summary'] = {
            'total_sitemaps': len(self.results['sitemaps']),
            'issues_found': len(self.results['issues_found']),
            'fixes_applied': len(self.results['fixes_applied']),
            'overall_status': 'healthy' if not self.results['issues_found'] else 'issues_detected'
        }
        return self.results

    def generate_report(self, detailed=True):
        s = self.results['summary']
        report = [f"# Sitemap Report", f"Generated: {self.results['timestamp']}", ""]
        report.append(f"## Status: {s['overall_status'].upper()}")
        report.append(f"- Total sitemaps: {s['total_sitemaps']}")
        report.append(f"- Issues found: {s['issues_found']}")
        report.append(f"- Fixes applied: {s['fixes_applied']}")
        if detailed:
            for sm in self.results['sitemaps']:
                report.append(f"### {sm['url']}")
                report.append(f"Status: {sm.get('status')}")
                report.append(f"Action: {sm.get('action')}")
        return "\n".join(report)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--site', required=True)
    p.add_argument('--sitemaps', required=True, nargs='+')
    p.add_argument('--force-resubmit', action='store_true')
    p.add_argument('--detailed-report', dest='detailed_report', action='store_true')
    p.add_argument('--no-detailed-report', dest='detailed_report', action='store_false')
    p.set_defaults(detailed_report=True)
    p.add_argument('--service-account', default='service-account.json')
    p.add_argument('--output-json')
    p.add_argument('--output-report')
    a = p.parse_args()

    monitor = SitemapMonitor(a.service_account)
    results = monitor.monitor_sitemaps(a.site, a.sitemaps, a.force_resubmit)
    if a.output_json:
        with open(a.output_json, 'w') as f: json.dump(results, f, indent=2)
    report = monitor.generate_report(a.detailed_report)
    if a.output_report:
        with open(a.output_report, 'w') as f: f.write(report)
    print(report)
    sys.exit(0 if results['summary']['overall_status'] == 'healthy' else 1)

if __name__ == "__main__": main()
