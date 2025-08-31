#!/usr/bin/env python3
"""
Sitemap generator script for GitHub Actions workflow.
Generates XML sitemaps from repository content.
"""

import os
import sys
import json
import argparse
import subprocess
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET


class SitemapGenerator:
    def __init__(self, base_url, config):
        self.base_url = base_url.rstrip('/')
        self.config = config
        self.urls = []
        
    def get_git_last_modified(self, file_path):
        """Get the last modification date of a file from Git history."""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%ct', '--', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                timestamp = int(result.stdout.strip())
                return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S+00:00')
            return None
        except (subprocess.CalledProcessError, ValueError):
            return None
    
    def get_file_priority(self, file_path):
        """Determine priority based on file path and name."""
        priority_rules = self.config.get('priority_rules', {})
        file_name = os.path.basename(file_path).lower()
        
        # Remove extension for checking
        name_without_ext = os.path.splitext(file_name)[0]
        
        # Check specific priority rules
        for keyword, priority in priority_rules.items():
            if keyword == 'default':
                continue
            if keyword in name_without_ext or keyword in file_path.lower():
                return priority
        
        return priority_rules.get('default', 0.5)
    
    def get_change_frequency(self, file_path):
        """Determine change frequency based on file path and type."""
        changefreq_rules = self.config.get('changefreq_rules', {})
        file_path_lower = file_path.lower()
        
        for keyword, freq in changefreq_rules.items():
            if keyword == 'default':
                continue
            if keyword in file_path_lower:
                return freq
        
        return changefreq_rules.get('default', 'weekly')
    
    def should_exclude_file(self, file_path):
        """Check if file should be excluded based on patterns."""
        exclude_patterns = self.config.get('exclude_patterns', [])
        
        for pattern in exclude_patterns:
            # Convert glob-like pattern to regex
            regex_pattern = pattern.replace('.*', '.*').replace('*', '[^/]*')
            if re.search(regex_pattern, file_path):
                return True
        
        return False
    
    def convert_path_to_url(self, file_path):
        """Convert file path to URL."""
        # Normalize path separators
        url_path = file_path.replace('\\', '/').lstrip('./')
        
        # Handle special cases
        if url_path == 'README.md' and self.config.get('auto_detect', {}).get('readme_as_index', True):
            url_path = ''
        elif url_path.endswith('/index.html') or url_path.endswith('/index.htm'):
            url_path = url_path.rsplit('/index.', 1)[0] + '/'
        elif url_path == 'index.html' or url_path == 'index.htm':
            url_path = ''
        elif url_path.endswith('.md'):
            # Convert markdown to HTML URL
            url_path = url_path[:-3] + '.html'
        
        # Ensure URL starts with /
        if url_path and not url_path.startswith('/'):
            url_path = '/' + url_path
        elif not url_path:
            url_path = '/'
        
        return urljoin(self.base_url, url_path)
    
    def scan_directory(self):
        """Scan directory for content files."""
        extensions = self.config.get('file_extensions', ['.html', '.htm', '.php', '.md'])
        
        print(f"🔍 Scanning for files with extensions: {', '.join(extensions)}")
        
        for root, dirs, files in os.walk('.'):
            # Skip hidden directories and common build/dependency directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', '.venv', 'venv', '.git'
            ]]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, '.')
                
                # Check if file has valid extension
                if not any(file.lower().endswith(ext) for ext in extensions):
                    continue
                
                # Check exclude patterns
                if self.should_exclude_file(relative_path):
                    continue
                
                # Get file metadata
                url = self.convert_path_to_url(relative_path)
                lastmod = self.get_git_last_modified(relative_path)
                priority = self.get_file_priority(relative_path)
                changefreq = self.get_change_frequency(relative_path)
                
                # Fallback to file system mtime if git fails
                if lastmod is None:
                    try:
                        mtime = os.path.getmtime(file_path)
                        lastmod = datetime.fromtimestamp(mtime).strftime('%Y-%m-%dT%H:%M:%S+00:00')
                    except OSError:
                        lastmod = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
                
                self.urls.append({
                    'loc': url,
                    'lastmod': lastmod,
                    'changefreq': changefreq,
                    'priority': priority,
                    'file_path': relative_path
                })
        
        print(f"📊 Found {len(self.urls)} URLs to include in sitemap")
    
    def generate_xml(self):
        """Generate the XML sitemap."""
        # Create root element
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Sort URLs by priority (descending) then by URL
        self.urls.sort(key=lambda x: (-x['priority'], x['loc']))
        
        for url_data in self.urls:
            url_elem = ET.SubElement(urlset, 'url')
            
            # Location (required)
            loc_elem = ET.SubElement(url_elem, 'loc')
            loc_elem.text = url_data['loc']
            
            # Last modified (optional)
            if url_data.get('lastmod'):
                lastmod_elem = ET.SubElement(url_elem, 'lastmod')
                lastmod_elem.text = url_data['lastmod']
            
            # Change frequency (optional)
            if url_data.get('changefreq'):
                changefreq_elem = ET.SubElement(url_elem, 'changefreq')
                changefreq_elem.text = url_data['changefreq']
            
            # Priority (optional)
            if url_data.get('priority') is not None:
                priority_elem = ET.SubElement(url_elem, 'priority')
                priority_elem.text = f"{url_data['priority']:.1f}"
        
        return urlset
    
    def write_sitemap(self, output_file):
        """Write the sitemap to file."""
        if not self.urls:
            print("⚠️ No URLs found to include in sitemap")
            return False
        
        xml_root = self.generate_xml()
        
        # Create XML declaration and pretty format
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_str += ET.tostring(xml_root, encoding='unicode', method='xml')
        
        # Basic pretty printing
        xml_str = xml_str.replace('><', '>\n<')
        lines = xml_str.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            if line.strip():
                if line.strip().startswith('</') and not line.strip().startswith('</url>'):
                    indent_level -= 1
                
                formatted_lines.append('  ' * indent_level + line.strip())
                
                if line.strip().startswith('<') and not line.strip().startswith('</') and not line.strip().endswith('/>'):
                    if not any(tag in line for tag in ['<loc>', '<lastmod>', '<changefreq>', '<priority>']):
                        indent_level += 1
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(formatted_lines))
            
            print(f"✅ Sitemap written to {output_file}")
            return True
        except IOError as e:
            print(f"❌ Error writing sitemap: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Generate sitemap for website')
    parser.add_argument('--base-url', required=True, help='Base URL for the sitemap')
    parser.add_argument('--output', default='sitemap.xml', help='Output sitemap file')
    parser.add_argument('--config', required=True, help='Configuration file path')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)
    
    if args.verbose:
        print(f"🌐 Base URL: {args.base_url}")
        print(f"📁 Output file: {args.output}")
        print(f"⚙️ Config file: {args.config}")
    
    # Generate sitemap
    generator = SitemapGenerator(args.base_url, config)
    generator.scan_directory()
    
    if generator.write_sitemap(args.output):
        print(f"🎉 Successfully generated sitemap with {len(generator.urls)} URLs")
        
        # Print sample URLs if verbose
        if args.verbose and generator.urls:
            print("\n📋 Sample URLs:")
            for url_data in generator.urls[:10]:
                print(f"   {url_data['loc']} (priority: {url_data['priority']:.1f})")
            
            if len(generator.urls) > 10:
                print(f"   ... and {len(generator.urls) - 10} more URLs")
    else:
        print("❌ Failed to generate sitemap")
        sys.exit(1)


if __name__ == '__main__':
    main()
