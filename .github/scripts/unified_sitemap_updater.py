#!/usr/bin/env python3
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz

def main():
    # Register the sitemap namespaces
    ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    ET.register_namespace('image', 'http://www.google.com/schemas/sitemap-image/1.1')
    ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')

    # Define namespace mapping
    ns = {
        'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
        'image': 'http://www.google.com/schemas/sitemap-image/1.1',
    }

    # Path to sitemap
    sitemap_path = 'sitemap.xml'
    
    # Check if there are any structural changes to the site
    # This could be detecting new files, deleted files, or changes to file paths
    structural_changes = has_structural_changes()
    
    try:
        # Parse existing sitemap
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing sitemap.xml: {e}")
        # If the file doesn't exist or is invalid, create a new one
        print("Creating new sitemap structure...")
        structural_changes = True
        root = create_new_sitemap()
        tree = ET.ElementTree(root)

    if structural_changes:
        # If there are structural changes, perform a full update
        print("Structural changes detected, updating entire sitemap...")
        updated_tree = update_full_sitemap(tree, root, ns)
    else:
        # If there are no structural changes, just update the timestamps
        print("No structural changes detected, updating timestamps only...")
        update_timestamps_only(tree, root, ns)

    # Save the updated sitemap
    tree.write(sitemap_path, encoding='UTF-8', xml_declaration=True)
    
    # Current date for confirmation message
    current_date = datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
    print(f"Sitemap updated successfully at {current_date}")

def has_structural_changes():
    """
    Determine if there are structural changes to the site that would
    require a full sitemap rebuild rather than just timestamp updates.
    
    This is a placeholder function - you'll need to implement the logic
    based on your specific site structure.
    
    Some ways to detect structural changes:
    1. Check for new or deleted HTML files
    2. Look for changes in routing files or navigation components
    3. Compare file lists between the last sitemap generation and now
    """
    try:
        # Example implementation: check for changes in HTML files 
        # since the last sitemap.xml commit
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%H', '--', 'sitemap.xml'],
            capture_output=True, text=True, check=True
        )
        last_sitemap_commit = result.stdout.strip()
        
        if not last_sitemap_commit:
            # No previous sitemap commit found, do a full rebuild
            return True
            
        # Check if any HTML files were added, removed, or modified since the last sitemap update
        result = subprocess.run(
            ['git', 'diff', '--name-status', last_sitemap_commit, 'HEAD', '--', '*.html'],
            capture_output=True, text=True, check=True
        )
        
        # If there are any changes to HTML files, return True
        return bool(result.stdout.strip())
    except Exception as e:
        print(f"Error checking for structural changes: {e}")
        # Default to a timestamp-only update if we can't determine changes
        return False

def create_new_sitemap():
    """Create a new sitemap structure from scratch"""
    # Create root element with proper namespaces
    root = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset', {
        '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation': 'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd',
        '{http://www.w3.org/2001/XMLSchema-instance}xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'
    })
    return root

def get_last_commit_date(file_path):
    """Get the latest commit date for a file"""
    try:
        # Get the last commit date for the file
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ci', '--', file_path],
            capture_output=True, text=True, check=True
        )
        date_str = result.stdout.strip()
        if date_str:
            # Parse the date
            commit_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')
            # Format to ISO 8601 for sitemap
            return commit_date.strftime('%Y-%m-%dT%H:%M:%S%z')
    except Exception as e:
        print(f"Error getting commit date for {file_path}: {e}")
    return None

def update_timestamps_only(tree, root, ns):
    """Update only the lastmod timestamps in the existing sitemap"""
    # Current timestamp in the format used by sitemaps
    current_date = datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S%z')

    # Update all lastmod elements
    updated = False
    for lastmod in root.findall('.//sm:lastmod', ns):
        lastmod.text = current_date
        updated = True

    if updated:
        print(f'Updated all lastmod timestamps to {current_date}')
    else:
        print('No lastmod elements found to update')

def update_full_sitemap(tree, root, ns):
    """Update the entire sitemap structure and dates"""
    # Get all URLs from the sitemap
    for url in root.findall('.//sm:url', ns):
        loc_elem = url.find('sm:loc', ns)
        lastmod_elem = url.find('sm:lastmod', ns)
        
        if loc_elem is not None:
            url_path = loc_elem.text
            
            # Convert the URL to a relative path if it's a file in our repo
            file_path = url_path.replace('https://sednabcn.github.io/', '')
            
            # Special case for the root URL
            if file_path == '':
                file_path = 'index.html'
            
            # If the file extension is missing and doesn't end with slash, append index.html
            if '.' not in file_path.split('/')[-1] and not file_path.endswith('/'):
                file_path += '/index.html'
            # If the path ends with slash, append index.html
            elif file_path.endswith('/'):
                file_path += 'index.html'
                
            # Check if the file exists in our repository
            if os.path.exists(file_path):
                last_commit_date = get_last_commit_date(file_path)
                
                if last_commit_date and lastmod_elem is not None:
                    # Update the lastmod element with the commit date
                    lastmod_elem.text = last_commit_date
                    print(f"Updated {url_path} with date {last_commit_date}")
                elif last_commit_date:
                    # Create a new lastmod element if it doesn't exist
                    new_lastmod = ET.SubElement(url, '{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
                    new_lastmod.text = last_commit_date
                    print(f"Added lastmod {last_commit_date} to {url_path}")
    
    return tree

# Add functionality to discover new pages and add them to the sitemap
def discover_and_add_new_pages(root, ns):
    """Discover new HTML pages and add them to the sitemap"""
    # Implementation depends on your site structure
    # This is a placeholder for site-specific logic
    pass

if __name__ == "__main__":
    main()
