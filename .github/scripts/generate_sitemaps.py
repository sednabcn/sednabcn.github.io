#!/usr/bin/env python3
"""
Enhanced Sitemap Generator Script for GitHub Pages

This script generates multiple sitemaps according to the following structure:
- sitemap.xml (main index)
- sitemap-main.xml
- sitemap-ai-llm-blog.xml
- sitemap-frequency-daily.xml
- sitemap-frequency-weekly.xml
- sitemap-frequency-monthly.xml
- sitemap-frequency-index.xml
- sitemap-master.xml
- sitemap-media-images.xml

And for the AI/LLM Blog Directory:
- ai-llm-blog/sitemap-main.xml
- ai-llm-blog/sitemap-posts.xml
- ai-llm-blog/sitemap-categories.xml
- ai-llm-blog/sitemap-tags.xml
- ai-llm-blog/sitemap-tutorials.xml
- ai-llm-blog/sitemap-resources.xml
- ai-llm-blog/sitemap-community.xml
- ai-llm-blog/sitemap-help.xml

It's designed to be run as part of a GitHub Actions workflow.
"""

import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import glob
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import hashlib

# Base URL of your website
BASE_URL = "https://sednabcn.github.io"  # Replace with your actual domain

# Content directories
CONTENT_DIR = "ai-llm-blog"  # Main content directory
IMAGE_DIRS = ["assets/images", f"{CONTENT_DIR}/assets/images"]  # Image directories

# File extensions to include
HTML_EXTENSIONS = ['.html', '.htm']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']
VIDEO_EXTENSIONS = ['.mp4', '.webm', '.ogg', '.mov']

# Directories to exclude
EXCLUDED_DIRS = ['node_modules', '.git', '.github']

# Update frequencies to categorize content
DAILY_PATHS = [f'{CONTENT_DIR}/news/', 'news/']
WEEKLY_PATHS = [f'{CONTENT_DIR}/tutorials/', 'tutorials/', f'{CONTENT_DIR}/community/', 'community/']
MONTHLY_PATHS = [f'{CONTENT_DIR}/posts/', 'posts/', f'{CONTENT_DIR}/blog/', 'blog/', f'{CONTENT_DIR}/resources/', 'resources/']

def get_last_modified(file_path):
    """Get the last modified date of a file in W3C format."""
    timestamp = os.path.getmtime(file_path)
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S+00:00')

def extract_title_from_html(file_path):
    """Extract title from HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.text
            h1_tag = soup.find('h1')
            if h1_tag:
                return h1_tag.text
    except Exception as e:
        print(f"Error extracting title from {file_path}: {e}")
    return ""

def extract_meta_tags_from_html(file_path):
    """Extract meta tags from HTML file including description, keywords, category, etc."""
    meta_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and 'content' in meta_desc.attrs:
                meta_data['description'] = meta_desc['content']
            
            # Extract keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and 'content' in meta_keywords.attrs:
                meta_data['keywords'] = meta_keywords['content'].split(',')
            
            # Extract category
            meta_category = soup.find('meta', attrs={'name': 'category'})
            if meta_category and 'content' in meta_category.attrs:
                meta_data['category'] = meta_category['content']
                
            # Extract tags
            meta_tags = soup.find('meta', attrs={'name': 'tags'})
            if meta_tags and 'content' in meta_tags.attrs:
                meta_data['tags'] = meta_tags['content'].split(',')
                
    except Exception as e:
        print(f"Error extracting meta tags from {file_path}: {e}")
    
    return meta_data

def is_excluded_path(file_path):
    """Check if file path contains any excluded directories."""
    return any(dir_name in file_path for dir_name in EXCLUDED_DIRS)

def determine_change_frequency(file_path):
    """Determine the change frequency based on the file path."""
    if any(path in file_path for path in DAILY_PATHS):
        return "daily"
    elif any(path in file_path for path in WEEKLY_PATHS):
        return "weekly"
    elif any(path in file_path for path in MONTHLY_PATHS):
        return "monthly"
    else:
        # Default frequency for other content
        return "weekly"

def determine_priority(file_path):
    """Determine the priority based on the file path."""
    if file_path.endswith('index.html'):
        # Main index pages
        if file_path == "index.html" or file_path == f"{CONTENT_DIR}/index.html":
            return "1.0"
        else:
            return "0.9"
    elif any(path in file_path for path in DAILY_PATHS):
        # News and frequently updated content
        return "0.8"
    elif any(path in file_path for path in WEEKLY_PATHS):
        # Tutorials and community content
        return "0.7"
    elif any(path in file_path for path in MONTHLY_PATHS):
        # Blog posts and resources
        return "0.6"
    else:
        # Other pages
        return "0.5"

def create_url_element(root, file_path, override_freq=None, override_priority=None):
    """Create a URL element in the sitemap."""
    url = ET.SubElement(root, "url")
    
    # Set location (URL)
    loc = ET.SubElement(url, "loc")
    page_url = f"{BASE_URL}/{file_path.replace(os.sep, '/')}"
    # Fix double slashes in URL
    page_url = page_url.replace("//", "/").replace(":/", "://")
    loc.text = page_url
    
    # Set last modified date
    lastmod = ET.SubElement(url, "lastmod")
    lastmod.text = get_last_modified(file_path)
    
    # Set change frequency
    changefreq = ET.SubElement(url, "changefreq")
    if override_freq:
        changefreq.text = override_freq
    else:
        changefreq.text = determine_change_frequency(file_path)
    
    # Set priority
    priority = ET.SubElement(url, "priority")
    if override_priority:
        priority.text = override_priority
    else:
        priority.text = determine_priority(file_path)
    
    return url

def write_sitemap(root, file_path):
    """Write the XML sitemap to a file."""
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"Sitemap generated: {file_path}")

def get_all_html_files():
    """Get all HTML files in the repository."""
    all_html_files = []
    for ext in HTML_EXTENSIONS:
        for file_path in glob.glob(f"**/*{ext}", recursive=True):
            if not is_excluded_path(file_path):
                all_html_files.append(file_path)
    return all_html_files

def generate_main_sitemap():
    """Generate the main sitemap with all HTML pages."""
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Add the cover page at the root URL
    url = ET.SubElement(root, "url")
    loc = ET.SubElement(url, "loc")
    loc.text = BASE_URL
    lastmod = ET.SubElement(url, "lastmod")
    lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    changefreq = ET.SubElement(url, "changefreq")
    changefreq.text = "weekly"
    priority = ET.SubElement(url, "priority")
    priority.text = "1.0"
    
    # Process all HTML files
    for file_path in get_all_html_files():
        create_url_element(root, file_path)
    
    # Write sitemap to file
    write_sitemap(root, "sitemap-main.xml")

def generate_ai_llm_blog_sitemap():
    """Generate sitemap specific to AI/LLM blog content."""
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Add the blog index page
    if os.path.exists(f"{CONTENT_DIR}/index.html"):
        url = ET.SubElement(root, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{BASE_URL}/{CONTENT_DIR}/"
        lastmod = ET.SubElement(url, "lastmod")
        lastmod.text = get_last_modified(f"{CONTENT_DIR}/index.html")
        changefreq = ET.SubElement(url, "changefreq")
        changefreq.text = "daily"
        priority = ET.SubElement(url, "priority")
        priority.text = "1.0"
    
    # Process all HTML files in the AI/LLM blog directory
    for file_path in get_all_html_files():
        if file_path.startswith(CONTENT_DIR):
            create_url_element(root, file_path)
    
    # Write sitemap to file
    write_sitemap(root, "sitemap-ai-llm-blog.xml")

def generate_frequency_sitemaps():
    """Generate sitemaps by update frequency (daily, weekly, monthly)."""
    # Create roots for each frequency
    daily_root = ET.Element("urlset")
    daily_root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    weekly_root = ET.Element("urlset")
    weekly_root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    monthly_root = ET.Element("urlset")
    monthly_root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Process all HTML files and categorize by frequency
    for file_path in get_all_html_files():
        freq = determine_change_frequency(file_path)
        if freq == "daily":
            create_url_element(daily_root, file_path, override_freq="daily")
        elif freq == "weekly":
            create_url_element(weekly_root, file_path, override_freq="weekly")
        elif freq == "monthly":
            create_url_element(monthly_root, file_path, override_freq="monthly")
    
    # Write sitemaps to files
    write_sitemap(daily_root, "sitemap-frequency-daily.xml")
    write_sitemap(weekly_root, "sitemap-frequency-weekly.xml")
    write_sitemap(monthly_root, "sitemap-frequency-monthly.xml")

def generate_media_images_sitemap():
    """Generate sitemap for media images."""
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    root.set("xmlns:image", "http://www.google.com/schemas/sitemap-image/1.1")
    
    # Track processed images to avoid duplicates
    processed_images = set()
    
    # Find all image files
    for image_dir in IMAGE_DIRS:
        if not os.path.exists(image_dir):
            print(f"Warning: Image directory {image_dir} does not exist, skipping")
            continue
            
        for ext in IMAGE_EXTENSIONS:
            for file_path in glob.glob(f"{image_dir}/**/*{ext}", recursive=True):
                # Skip files in excluded directories or already processed
                if is_excluded_path(file_path) or file_path in processed_images:
                    continue
                    
                processed_images.add(file_path)
                
                # Create URL entry for the image
                url = ET.SubElement(root, "url")
                
                # Parent URL (where the image is located)
                loc = ET.SubElement(url, "loc")
                parent_dir = os.path.dirname(file_path).replace(os.sep, '/')
                parent_url = f"{BASE_URL}/{parent_dir}"
                if parent_url.endswith('/'):
                    parent_url = parent_url[:-1]
                loc.text = parent_url
                
                # Image information
                image = ET.SubElement(url, "image:image")
                
                image_loc = ET.SubElement(image, "image:loc")
                image_loc.text = f"{BASE_URL}/{file_path.replace(os.sep, '/')}"
                
                # Try to extract image title from filename
                title = os.path.splitext(os.path.basename(file_path))[0]
                title = re.sub(r'[-_]', ' ', title).title()
                
                image_title = ET.SubElement(image, "image:title")
                image_title.text = title
    
    # Write sitemap to file
    write_sitemap(root, "sitemap-media-images.xml")
    print(f"Total images processed: {len(processed_images)}")

def generate_ai_llm_blog_submap(name, filter_func):
    """Generate a specific AI/LLM blog sitemap based on a filter function."""
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Process all AI/LLM blog HTML files that match the filter
    for file_path in get_all_html_files():
        if file_path.startswith(CONTENT_DIR) and filter_func(file_path):
            create_url_element(root, file_path)
    
    # Write sitemap to file
    sitemap_path = f"{CONTENT_DIR}/sitemap-{name}.xml"
    write_sitemap(root, sitemap_path)

def generate_ai_llm_blog_sitemaps():
    """Generate all AI/LLM blog specific sitemaps."""
    # Ensure the AI/LLM blog directory exists
    os.makedirs(CONTENT_DIR, exist_ok=True)
    
    # Generate main AI/LLM blog sitemap (all content)
    generate_ai_llm_blog_submap("main", lambda path: True)
    
    # Generate posts sitemap
    generate_ai_llm_blog_submap("posts", lambda path: '/posts/' in path or '/blog/' in path)
    
    # Generate categories sitemap - extracting from meta tags or URL structure
    def is_category_page(path):
        return '/categories/' in path or '/category/' in path or \
               (os.path.exists(path) and 'category' in extract_meta_tags_from_html(path))
    
    generate_ai_llm_blog_submap("categories", is_category_page)
    
    # Generate tags sitemap - extracting from meta tags or URL structure
    def is_tag_page(path):
        return '/tags/' in path or '/tag/' in path or \
               (os.path.exists(path) and 'tags' in extract_meta_tags_from_html(path))
    
    generate_ai_llm_blog_submap("tags", is_tag_page)
    
    # Generate tutorials sitemap
    generate_ai_llm_blog_submap("tutorials", lambda path: '/tutorials/' in path)
    
    # Generate resources sitemap
    generate_ai_llm_blog_submap("resources", lambda path: '/resources/' in path)
    
    # Generate community sitemap
    generate_ai_llm_blog_submap("community", lambda path: '/community/' in path)
    
    # Generate help sitemap
    generate_ai_llm_blog_submap("help", lambda path: '/help/' in path or '/faq/' in path or '/guide/' in path)

def generate_frequency_index_sitemap():
    """Generate index sitemap for frequency-based sitemaps."""
    root = ET.Element("sitemapindex")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Add daily sitemap
    sitemap = ET.SubElement(root, "sitemap")
    loc = ET.SubElement(sitemap, "loc")
    loc.text = f"{BASE_URL}/sitemap-frequency-daily.xml"
    lastmod = ET.SubElement(sitemap, "lastmod")
    lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Add weekly sitemap
    sitemap = ET.SubElement(root, "sitemap")
    loc = ET.SubElement(sitemap, "loc")
    loc.text = f"{BASE_URL}/sitemap-frequency-weekly.xml"
    lastmod = ET.SubElement(sitemap, "lastmod")
    lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Add monthly sitemap
    sitemap = ET.SubElement(root, "sitemap")
    loc = ET.SubElement(sitemap, "loc")
    loc.text = f"{BASE_URL}/sitemap-frequency-monthly.xml"
    lastmod = ET.SubElement(sitemap, "lastmod")
    lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Write sitemap to file
    write_sitemap(root, "sitemap-frequency-index.xml")

def generate_master_sitemap():
    """Generate a comprehensive master sitemap with all content."""
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    root.set("xmlns:image", "http://www.google.com/schemas/sitemap-image/1.1")
    root.set("xmlns:video", "http://www.google.com/schemas/sitemap-video/1.1")
    
    # Process all HTML files
    for file_path in get_all_html_files():
        url_element = create_url_element(root, file_path)
        
        # Add additional metadata if available
        if os.path.exists(file_path):
            meta_tags = extract_meta_tags_from_html(file_path)
            
            # Add meta description as an extension element if available
            if 'description' in meta_tags:
                meta_desc = ET.SubElement(url_element, "meta:description")
                meta_desc.text = meta_tags['description']
    
    # Write sitemap to file
    write_sitemap(root, "sitemap-master.xml")

def generate_main_index_sitemap():
    """Generate the main index sitemap that references all other sitemaps."""
    root = ET.Element("sitemapindex")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Add main sitemap
    sitemap = ET.SubElement(root, "sitemap")
    loc = ET.SubElement(sitemap, "loc")
    loc.text = f"{BASE_URL}/sitemap-main.xml"
    lastmod = ET.SubElement(sitemap, "lastmod")
    lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Add AI/LLM blog sitemap
    sitemap = ET.SubElement(root, "sitemap")
    loc = ET.SubElement(sitemap, "loc")
    loc.text = f"{BASE_URL}/sitemap-ai-llm-blog.xml"
    lastmod = ET.SubElement(sitemap, "lastmod")
    lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Add frequency index sitemap
    sitemap = ET.SubElement(root, "sitemap")
    loc = ET.SubElement(sitemap, "loc")
    loc.text = f"{BASE_URL}/sitemap-frequency-index.xml"
    lastmod = ET.SubElement(sitemap, "lastmod")
    lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Add media images sitemap
    sitemap = ET.SubElement(root, "sitemap")
    loc = ET.SubElement(sitemap, "loc")
    loc.text = f"{BASE_URL}/sitemap-media-images.xml"
    lastmod = ET.SubElement(sitemap, "lastmod")
    lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Add master sitemap
    sitemap = ET.SubElement(root, "sitemap")
    loc = ET.SubElement(sitemap, "loc")
    loc.text = f"{BASE_URL}/sitemap-master.xml"
    lastmod = ET.SubElement(sitemap, "lastmod")
    lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Add AI/LLM blog sub-sitemaps
    ai_llm_submaps = [
        "main", "posts", "categories", "tags", 
        "tutorials", "resources", "community", "help"
    ]
    
    for submap in ai_llm_submaps:
        sitemap = ET.SubElement(root, "sitemap")
        loc = ET.SubElement(sitemap, "loc")
        loc.text = f"{BASE_URL}/{CONTENT_DIR}/sitemap-{submap}.xml"
        lastmod = ET.SubElement(sitemap, "lastmod")
        lastmod.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Write sitemap to file
    write_sitemap(root, "sitemap.xml")

def ensure_directories_exist():
    """Ensure all required directories exist."""
    os.makedirs(CONTENT_DIR, exist_ok=True)
    for image_dir in IMAGE_DIRS:
        os.makedirs(image_dir, exist_ok=True)

def main():
    print("Starting enhanced sitemap generation...")
    
    # Ensure required directories exist
    ensure_directories_exist()
    
    # Generate root directory sitemaps
    print("Generating root directory sitemaps...")
    generate_main_sitemap()  # sitemap-main.xml
    generate_ai_llm_blog_sitemap()  # sitemap-ai-llm-blog.xml
    generate_frequency_sitemaps()  # sitemap-frequency-daily.xml, sitemap-frequency-weekly.xml, sitemap-frequency-monthly.xml
    generate_frequency_index_sitemap()  # sitemap-frequency-index.xml
    generate_master_sitemap()  # sitemap-master.xml
    generate_media_images_sitemap()  # sitemap-media-images.xml
    
    # Generate AI/LLM blog specific sitemaps
    print("Generating AI/LLM blog specific sitemaps...")
    generate_ai_llm_blog_sitemaps()
    
    # Generate the main index sitemap last
    print("Generating main index sitemap...")
    generate_main_index_sitemap()  # sitemap.xml
    
    print("Sitemap generation complete!")

if __name__ == "__main__":
    main()
