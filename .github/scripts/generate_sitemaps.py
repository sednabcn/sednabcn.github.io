#!/usr/bin/env python3
"""
Script to generate sitemaps for the main GitHub Pages site and update
references to project sitemaps.
"""

import os
import re
import xml.dom.minidom
import datetime
from pathlib import Path

def generate_sitemap_index():
    """Generate the sitemap index file that references all other sitemaps."""
    today = datetime.date.today().isoformat()
    
    sitemap_index = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://sednabcn.github.io/sitemap-main.xml</loc>
    <lastmod>{today}</lastmod>
  </sitemap>
  <sitemap>
    <loc>https://sednabcn.github.io/ai-llm-blog/sitemap.xml</loc>
    <lastmod>{today}</lastmod>
  </sitemap>
  <!-- Add other project sitemaps as needed -->
</sitemapindex>
"""
    
    with open("sitemap.xml", "w") as f:
        f.write(sitemap_index)
    
    print("Generated sitemap index at sitemap.xml")

def generate_main_sitemap():
    """Generate the main sitemap for the root site."""
    today = datetime.date.today().isoformat()
    
    # Read the index.html to find any additional links
    try:
        with open("index.html", "r") as f:
            content = f.read()
            
        # Find project links (this is a simple approach, might need adjustment)
        links = re.findall(r'href="(https://sednabcn\.github\.io/[^"]+)"', content)
        
        # De-duplicate links
        links = list(set(links))
    except FileNotFoundError:
        links = []
    
    # Start with the base URLs
    urls = [
        {
            "loc": "https://sednabcn.github.io/",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "1.0"
        },
        {
            "loc": "https://sednabcn.github.io/ai-llm-blog/",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.9"
        },
        {
            "loc": "https://sednabcn.github.io/ai-llm-blog/posts/",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.8"
        },
        {
            "loc": "https://sednabcn.github.io/ai-llm-blog/about/",
            "lastmod": today,
            "changefreq": "monthly",
            "priority": "0.7"
        },
        {
            "loc": "https://sednabcn.github.io/ai-llm-blog/categories/",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.7"
        },
        {
            "loc": "https://sednabcn.github.io/ai-llm-blog/tags/",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.7"
        }
    ]
    
    # Add any additional links found in the HTML
    for link in links:
        if link not in [url["loc"] for url in urls]:
            urls.append({
                "loc": link,
                "lastmod": today,
                "changefreq": "monthly",
                "priority": "0.5"
            })
    
    # Create the main sitemap XML
    main_sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    main_sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        main_sitemap += f'  <url>\n'
        main_sitemap += f'    <loc>{url["loc"]}</loc>\n'
        main_sitemap += f'    <lastmod>{url["lastmod"]}</lastmod>\n'
        main_sitemap += f'    <changefreq>{url["changefreq"]}</changefreq>\n'
        main_sitemap += f'    <priority>{url["priority"]}</priority>\n'
        main_sitemap += f'  </url>\n'
    
    main_sitemap += '</urlset>'
    
    # Format the XML for better readability
    dom = xml.dom.minidom.parseString(main_sitemap)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove extra empty lines
    pretty_xml = os.linesep.join([s for s in pretty_xml.splitlines() if s.strip()])
    
    with open("sitemap-main.xml", "w") as f:
        f.write(pretty_xml)
    
    print("Generated main sitemap at sitemap-main.xml")

def main():
    # Create necessary directories
    Path(".github/scripts").mkdir(parents=True, exist_ok=True)
    
    # Generate sitemaps
    generate_sitemap_index()
    generate_main_sitemap()

if __name__ == "__main__":
    main()
