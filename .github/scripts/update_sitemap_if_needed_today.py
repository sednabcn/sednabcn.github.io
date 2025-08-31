#!/usr/bin/env python3
"""
Conditional sitemap updater - only generates if needed.
This script checks if content has changed since last sitemap generation.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime


def get_git_last_modified(file_path):
    """Get the last modification date of a file from Git history."""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ct', '--', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            return int(result.stdout.strip())
        return None
    except (subprocess.CalledProcessError, ValueError):
        return None


def find_content_files(config):
    """Find all content files that should be tracked."""
    content_files = []
    extensions = config.get('file_extensions', ['.html', '.htm', '.php', '.md', '.markdown'])
    exclude_patterns = config.get('exclude_patterns', [])
    
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories early
        dirs[:] = [d for d in dirs if not any(
            pattern.replace('.*', '') in os.path.join(root, d) 
            for pattern in exclude_patterns
        ) and not d.startswith('.')]
        
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), '.')
            
            # Check if file has valid extension
            if any(file.lower().endswith(ext) for ext in extensions):
                # Check exclude patterns
                if not any(pattern.replace('.*', '') in file_path for pattern in exclude_patterns):
                    content_files.append(file_path)
    
    return content_files


def should_regenerate_sitemap(config, force=False):
    """Check if sitemap needs regeneration."""
    if force:
        print("🔄 Force regeneration requested")
        return True
    
    sitemap_path = 'sitemap.xml'
    
    # Always regenerate if sitemap doesn't exist
    if not os.path.exists(sitemap_path):
        print("🆕 Sitemap doesn't exist, generating new one")
        return True
    
    # Get sitemap last modified time
    try:
        sitemap_mtime = get_git_last_modified(sitemap_path)
        if sitemap_mtime is None:
            sitemap_mtime = int(os.path.getmtime(sitemap_path))
        print(f"📅 Sitemap last modified: {datetime.fromtimestamp(sitemap_mtime).isoformat()}")
    except OSError:
        print("❓ Cannot determine sitemap age, regenerating")
        return True
    
    # Find content files and check modification times
    content_files = find_content_files(config)
    print(f"🔍 Checking {len(content_files)} content files...")
    
    newer_files = []
    for file_path in content_files:
        try:
            file_mtime = get_git_last_modified(file_path)
            if file_mtime is None:
                file_mtime = int(os.path.getmtime(file_path))
            
            if file_mtime > sitemap_mtime:
                newer_files.append((file_path, file_mtime))
        except OSError:
            continue
    
    if newer_files:
        print(f"🔄 Found {len(newer_files)} files newer than sitemap:")
        for file_path, mtime in newer_files[:5]:  # Show first 5
            modified_date = datetime.fromtimestamp(mtime).isoformat()
            print(f"   📝 {file_path} ({modified_date})")
        if len(newer_files) > 5:
            print(f"   ➕ ... and {len(newer_files) - 5} more")
        return True
    
    print("✅ Sitemap is up to date, no regeneration needed")
    return False


def run_sitemap_generator(base_url, config_file, output_file):
    """Run the main sitemap generator."""
    try:
        cmd = [
            sys.executable, 'generate_sitemap.py',
            base_url,
            '--config', config_file,
            '--output', output_file,
            '--verbose'
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("📤 Generator output:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("⚠️ Warnings/Errors:")
            print(result.stderr)
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Sitemap generator failed with exit code {e.returncode}")
        if e.stdout:
            print("📤 stdout:", e.stdout)
        if e.stderr:
            print("📤 stderr:", e.stderr)
        return False
    except FileNotFoundError:
        print("❌ generate_sitemap.py script not found")
        return False


def main():
    parser = argparse.ArgumentParser(description='Conditionally update sitemap if needed')
    parser.add_argument('--base-url', required=True, help='Base URL for the sitemap')
    parser.add_argument('--output', default='sitemap.xml', help='Output sitemap file')
    parser.add_argument('--config', required=True, help='Configuration file path')
    parser.add_argument('--force', action='store_true', help='Force regeneration')
    
    args = parser.parse_args()
    
    print("🗺️ Sitemap Update Checker")
    print("=" * 50)
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
        print(f"⚙️ Loaded config from {args.config}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)
    
    # Check if regeneration is needed
    if should_regenerate_sitemap(config, args.force):
        print("\n🔄 Regeneration needed, calling main generator...")
        
        if run_sitemap_generator(args.base_url, args.config, args.output):
            print("✅ Sitemap generation completed successfully")
        else:
            print("❌ Sitemap generation failed")
            sys.exit(1)
    else:
        print("⏭️ No regeneration needed, sitemap is current")
        
        # Ensure sitemap exists (create minimal one if missing)
        if not os.path.exists(args.output):
            print("🔧 Creating minimal sitemap file...")
            minimal_sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{args.base_url}/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>'''
            
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(minimal_sitemap)
                print(f"✅ Created minimal sitemap at {args.output}")
            except IOError as e:
                print(f"❌ Failed to create minimal sitemap: {e}")
                sys.exit(1)


if __name__ == '__main__':
    main()
