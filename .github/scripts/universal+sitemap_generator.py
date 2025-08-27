#!/usr/bin/env python3
"""
Universal Sitemap Generator
Automatically generates sitemap.xml for any project by scanning files and detecting URLs.
Supports static sites, documentation, GitHub Pages, and more.
"""

import os
import sys
import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from xml.dom import minidom


class SitemapGenerator:
    def __init__(self, base_url, project_path=".", config_file=None):
        self.base_url = base_url.rstrip('/')
        self.project_path = Path(project_path).resolve()
        self.config = self.load_config(config_file)
        self.urls = set()
        self.file_extensions = self.config.get('file_extensions', [
            '.html', '.htm', '.php', '.asp', '.aspx', '.jsp',
            '.md', '.markdown', '.txt', '.pdf'
        ])
        self.exclude_patterns = self.config.get('exclude_patterns', [
            r'.*\.git.*', r'.*node_modules.*', r'.*\.venv.*', 
            r'.*__pycache__.*', r'.*\.DS_Store.*', r'.*\.tmp.*',
            r'.*404\.html$', r'.*error\.html$'
        ])
        self.include_patterns = self.config.get('include_patterns', [])
        
    def load_config(self, config_file):
        """Load configuration from JSON file if provided."""
        default_config = {
            "file_extensions": [".html", ".htm", ".php", ".md", ".pdf"],
            "exclude_patterns": [r".*\.git.*", r".*node_modules.*"],
            "include_patterns": [],
            "priority_rules": {
                "index": 1.0,
                "home": 1.0,
                "main": 0.9,
                "about": 0.8,
                "contact": 0.8,
                "default": 0.5
            },
            "changefreq_rules": {
                "index": "daily",
                "blog": "weekly",
                "news": "daily",
                "static": "monthly",
                "default": "weekly"
            },
            "auto_detect": {
                "readme_as_index": True,
                "detect_project_type": True,
                "scan_html_links": True,
                "include_markdown": True
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    print(f"✅ Loaded configuration from {config_file}")
            except Exception as e:
                print(f"⚠️ Warning: Could not load config file {config_file}: {e}")
        
        return default_config
    
    def detect_project_type(self):
        """Detect the type of project to optimize sitemap generation."""
        project_indicators = {
            'react': ['package.json', 'src/App.js', 'public/index.html'],
            'vue': ['package.json', 'src/App.vue'],
            'angular': ['package.json', 'angular.json'],
            'jekyll': ['_config.yml', '_posts/', '_layouts/'],
            'hugo': ['config.toml', 'config.yaml', 'config.yml', 'content/'],
            'gatsby': ['gatsby-config.js', 'src/pages/'],
            'next': ['next.config.js', 'pages/'],
            'nuxt': ['nuxt.config.js', 'pages/'],
            'static': ['index.html'],
            'docs': ['docs/', 'documentation/', 'README.md'],
            'github_pages': ['.github/', 'docs/', '_config.yml']
        }
        
        detected_types = []
        
        for project_type, indicators in project_indicators.items():
            for indicator in indicators:
                path = self.project_path / indicator
                if path.exists():
                    detected_types.append(project_type)
                    break
        
        # Remove duplicates and return primary type
        detected_types = list(set(detected_types))
        primary_type = detected_types[0] if detected_types else 'unknown'
        
        print(f"🔍 Detected project type(s): {', '.join(detected_types) if detected_types else 'unknown'}")
        return primary_type, detected_types
    
    def should_include_file(self, file_path):
        """Check if a file should be included based on patterns."""
        file_str = str(file_path)
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if re.match(pattern, file_str, re.IGNORECASE):
                return False
        
        # If include patterns are specified, file must match one
        if self.include_patterns:
            for pattern in self.include_patterns:
                if re.match(pattern, file_str, re.IGNORECASE):
                    return True
            return False
        
        # Check file extension
        return file_path.suffix.lower() in [ext.lower() for ext in self.file_extensions]
    
    def extract_links_from_html(self, html_file):
        """Extract internal links from HTML files."""
        links = set()
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Find href attributes
            href_pattern = r'href=["\']([^"\']+)["\']'
            matches = re.findall(href_pattern, content, re.IGNORECASE)
            
            for match in matches:
                # Skip external links, anchors, mailto, etc.
                if (not match.startswith(('http://', 'https://', 'mailto:', 'tel:', '#')) 
                    and not match.startswith('//')):
                    # Convert relative paths to absolute
                    if match.startswith('/'):
                        links.add(match)
                    else:
                        # Relative to current file
                        rel_path = Path(html_file).parent / match
                        try:
                            abs_path = rel_path.resolve().relative_to(self.project_path)
                            links.add('/' + str(abs_path).replace('\\', '/'))
                        except ValueError:
                            # Path is outside project
                            pass
                            
        except Exception as e:
            print(f"⚠️ Warning: Could not extract links from {html_file}: {e}")
        
        return links
    
    def get_file_priority(self, file_path):
        """Determine priority based on file path and name."""
        path_str = str(file_path).lower()
        filename = file_path.stem.lower()
        
        priority_rules = self.config.get('priority_rules', {})
        
        # Check specific filename matches
        for key, priority in priority_rules.items():
            if key == 'default':
                continue
            if key in filename or key in path_str:
                return priority
        
        # Special cases
        if filename in ['index', 'home', 'main']:
            return 1.0
        elif 'index' in filename:
            return 0.9
        elif any(word in path_str for word in ['about', 'contact', 'services']):
            return 0.8
        elif any(word in path_str for word in ['blog', 'news', 'posts']):
            return 0.7
        
        return priority_rules.get('default', 0.5)
    
    def get_change_frequency(self, file_path):
        """Determine change frequency based on file path and type."""
        path_str = str(file_path).lower()
        
        changefreq_rules = self.config.get('changefreq_rules', {})
        
        if 'index' in path_str or 'home' in path_str:
            return changefreq_rules.get('index', 'weekly')
        elif any(word in path_str for word in ['blog', 'news', 'posts']):
            return changefreq_rules.get('blog', 'weekly')
        elif any(word in path_str for word in ['about', 'contact', 'terms', 'privacy']):
            return changefreq_rules.get('static', 'monthly')
        
        return changefreq_rules.get('default', 'weekly')
    
    def get_last_modified(self, file_path):
        """Get last modified time of file."""
        try:
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except:
            return datetime.now(tz=timezone.utc)
    
    def scan_files(self):
        """Scan project directory for files to include in sitemap."""
        print(f"📁 Scanning directory: {self.project_path}")
        
        found_files = []
        html_links = set()
        
        # Walk through all files
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file() and self.should_include_file(file_path):
                found_files.append(file_path)
                
                # Extract links from HTML files
                if (file_path.suffix.lower() in ['.html', '.htm'] and 
                    self.config.get('auto_detect', {}).get('scan_html_links', True)):
                    links = self.extract_links_from_html(file_path)
                    html_links.update(links)
        
        print(f"📄 Found {len(found_files)} files")
        if html_links:
            print(f"🔗 Extracted {len(html_links)} internal links")
        
        return found_files, html_links
    
    def convert_path_to_url(self, file_path):
        """Convert file system path to URL."""
        try:
            # Get path relative to project root
            rel_path = file_path.relative_to(self.project_path)
            url_path = str(rel_path).replace('\\', '/')
            
            # Handle special cases
            if url_path == 'index.html':
                url_path = ''
            elif url_path.endswith('/index.html'):
                url_path = url_path[:-11]  # Remove /index.html
            elif url_path.endswith('.md'):
                # Convert markdown to html
                url_path = url_path[:-3] + '.html'
            elif url_path.endswith('.markdown'):
                url_path = url_path[:-9] + '.html'
            
            # Ensure URL starts with /
            if url_path and not url_path.startswith('/'):
                url_path = '/' + url_path
            elif not url_path:
                url_path = '/'
                
            return urljoin(self.base_url, url_path)
            
        except ValueError:
            # File is outside project directory
            return None
    
    def generate_sitemap_data(self):
        """Generate sitemap data structure."""
        print("🔄 Generating sitemap data...")
        
        # Detect project type for optimization
        project_type, all_types = self.detect_project_type()
        
        # Scan for files
        files, html_links = self.scan_files()
        
        sitemap_entries = []
        processed_urls = set()
        
        # Process files
        for file_path in files:
            url = self.convert_path_to_url(file_path)
            if url and url not in processed_urls:
                processed_urls.add(url)
                
                entry = {
                    'loc': url,
                    'lastmod': self.get_last_modified(file_path).isoformat(),
                    'changefreq': self.get_change_frequency(file_path),
                    'priority': self.get_file_priority(file_path)
                }
                sitemap_entries.append(entry)
        
        # Process HTML links that might not correspond to files
        for link in html_links:
            url = urljoin(self.base_url, link)
            if url not in processed_urls:
                processed_urls.add(url)
                
                entry = {
                    'loc': url,
                    'lastmod': datetime.now(tz=timezone.utc).isoformat(),
                    'changefreq': 'weekly',
                    'priority': 0.5
                }
                sitemap_entries.append(entry)
        
        # Sort by priority (descending) then by URL
        sitemap_entries.sort(key=lambda x: (-x['priority'], x['loc']))
        
        print(f"✅ Generated {len(sitemap_entries)} sitemap entries")
        return sitemap_entries
    
    def create_sitemap_xml(self, entries, output_path='sitemap.xml'):
        """Create sitemap.xml file."""
        print(f"📝 Creating sitemap.xml with {len(entries)} URLs...")
        
        # Create root element
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Add URLs
        for entry in entries:
            url_elem = ET.SubElement(urlset, 'url')
            
            loc_elem = ET.SubElement(url_elem, 'loc')
            loc_elem.text = entry['loc']
            
            lastmod_elem = ET.SubElement(url_elem, 'lastmod')
            lastmod_elem.text = entry['lastmod']
            
            changefreq_elem = ET.SubElement(url_elem, 'changefreq')
            changefreq_elem.text = entry['changefreq']
            
            priority_elem = ET.SubElement(url_elem, 'priority')
            priority_elem.text = f"{entry['priority']:.1f}"
        
        # Format XML nicely
        rough_string = ET.tostring(urlset, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent='  ')
        
        # Remove extra blank lines
        pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
        
        # Write to file
        output_path = Path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"✅ Sitemap saved to {output_path.absolute()}")
        return output_path
    
    def validate_sitemap(self, sitemap_path):
        """Basic validation of generated sitemap."""
        try:
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            
            url_count = len(root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'))
            
            print(f"✅ Sitemap validation passed: {url_count} URLs")
            
            # Check for common issues
            warnings = []
            if url_count > 50000:
                warnings.append("Sitemap has more than 50,000 URLs (consider splitting)")
            if url_count == 0:
                warnings.append("Sitemap contains no URLs")
            
            for warning in warnings:
                print(f"⚠️ Warning: {warning}")
            
            return True, warnings
            
        except Exception as e:
            print(f"❌ Sitemap validation failed: {e}")
            return False, [str(e)]
    
    def generate(self, output_path='sitemap.xml'):
        """Main method to generate sitemap."""
        print("🚀 Starting sitemap generation...")
        print(f"Base URL: {self.base_url}")
        print(f"Project path: {self.project_path}")
        
        try:
            # Generate sitemap data
            entries = self.generate_sitemap_data()
            
            if not entries:
                print("❌ No URLs found to include in sitemap")
                return False
            
            # Create XML file
            sitemap_path = self.create_sitemap_xml(entries, output_path)
            
            # Validate
            is_valid, warnings = self.validate_sitemap(sitemap_path)
            
            if is_valid:
                print(f"🎉 Sitemap generation completed successfully!")
                print(f"📍 Location: {sitemap_path.absolute()}")
                return True
            else:
                print("❌ Sitemap generation failed validation")
                return False
                
        except Exception as e:
            print(f"❌ Error generating sitemap: {e}")
            return False


def create_sample_config():
    """Create a sample configuration file."""
    sample_config = {
        "file_extensions": [".html", ".htm", ".php", ".asp", ".aspx", ".md", ".pdf"],
        "exclude_patterns": [
            r".*\.git.*",
            r".*node_modules.*",
            r".*\.venv.*",
            r".*__pycache__.*",
            r".*\.DS_Store.*",
            r".*\.tmp.*",
            r".*404\.html$",
            r".*error\.html$"
        ],
        "include_patterns": [],
        "priority_rules": {
            "index": 1.0,
            "home": 1.0,
            "main": 0.9,
            "about": 0.8,
            "contact": 0.8,
            "blog": 0.7,
            "default": 0.5
        },
        "changefreq_rules": {
            "index": "daily",
            "blog": "weekly",
            "news": "daily", 
            "static": "monthly",
            "default": "weekly"
        },
        "auto_detect": {
            "readme_as_index": True,
            "detect_project_type": True,
            "scan_html_links": True,
            "include_markdown": True
        }
    }
    
    with open('sitemap-config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print("✅ Sample configuration saved to sitemap-config.json")


def main():
    parser = argparse.ArgumentParser(
        description='Universal Sitemap Generator - Automatically generate sitemap.xml for any project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python generate_sitemap.py https://mysite.com
  
  # Specify project directory
  python generate_sitemap.py https://mysite.com --path ./my-project
  
  # Use custom configuration
  python generate_sitemap.py https://mysite.com --config sitemap-config.json
  
  # Output to specific file
  python generate_sitemap.py https://mysite.com --output public/sitemap.xml
  
  # Create sample configuration file
  python generate_sitemap.py --create-config
        """
    )
    
    parser.add_argument('base_url', nargs='?', help='Base URL of your website (e.g., https://example.com)')
    parser.add_argument('--path', '-p', default='.', help='Project directory path (default: current directory)')
    parser.add_argument('--output', '-o', default='sitemap.xml', help='Output file path (default: sitemap.xml)')
    parser.add_argument('--config', '-c', help='Configuration file path (JSON format)')
    parser.add_argument('--create-config', action='store_true', help='Create a sample configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Create sample config and exit
    if args.create_config:
        create_sample_config()
        return
    
    # Validate required arguments
    if not args.base_url:
        parser.error('Base URL is required unless using --create-config')
    
    try:
        # Create and run generator
        generator = SitemapGenerator(
            base_url=args.base_url,
            project_path=args.path,
            config_file=args.config
        )
        
        success = generator.generate(args.output)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
