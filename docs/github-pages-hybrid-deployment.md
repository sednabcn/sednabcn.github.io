# GitHub Pages Hybrid Deployment Guide

This guide explains how to implement a hybrid GitHub Pages deployment strategy where:
- The main site uses GitHub Actions for automation
- Project repositories use branch-based deployment for simplicity

## Main Repository Setup (`sednabcn.github.io`)

### 1. Create Repository

1. Create a repository named exactly `sednabcn.github.io`
2. Make it public
3. Initialize with a README

### 2. Add Basic Files

Clone the repository and add these essential files:

```bash
git clone https://github.com/sednabcn/sednabcn.github.io.git
cd sednabcn.github.io
```

Files to add:
- `index.html` - Main landing page
- `assets/css/style.css` - Styling
- `assets/js/main.js` - Interactivity
- `.nojekyll` - Empty file to disable Jekyll processing
- `robots.txt` - Search engine instructions
- `.github/workflows/static-deploy.yml` - Workflow file

### 3. Configure GitHub Actions Deployment

1. Go to repository Settings > Pages
2. Under "Build and deployment":
   - Source: Select "GitHub Actions"
3. Save changes

The GitHub Actions workflow will:
- Automatically generate and update sitemaps
- Commit sitemap changes back to the repository
- Deploy the site to GitHub Pages
- Run performance tests

## Project Repositories (e.g., `ai-llm-blog`)

### 1. Set Up Branch-Based Deployment

For each project repository:

1. Go to repository Settings > Pages
2. Under "Build and deployment":
   - Source: Select "Deploy from a branch"
   - Branch: Choose your branch (usually `main` or `gh-pages`)
   - Folder: Select folder (usually `/` or `/docs`)
3. Save changes

### 2. Add Project Sitemap

Each project repository should have its own `sitemap.xml` at the root level:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <!-- Project URLs go here -->
  <url>
    <loc>https://sednabcn.github.io/project-name/</loc>
    <lastmod>2025-05-10</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <!-- Additional URLs -->
</urlset>
```

## Connecting Everything

### 1. Update Main Sitemap Index

The automated workflow in your main repository will maintain a sitemap index at:
`https://sednabcn.github.io/sitemap.xml`

This index references:
- Main site URLs: `https://sednabcn.github.io/sitemap-main.xml`
- Project sitemaps: `https://sednabcn.github.io/project-name/sitemap.xml`

### 2. Google Search Console Setup

1. Add and verify property: `https://sednabcn.github.io/`
2. Submit sitemap by entering just `sitemap.xml`
3. Google will follow the links to find all your content

## Benefits of This Approach

- **Centralized SEO Management**: All sitemaps connected through one index
- **Automation Where Needed**: Automated sitemap updates for the main site
- **Simplicity for Projects**: Direct branch-based deployment for individual projects
- **Improved Indexing**: Google can discover all your content through a single entry point

## Maintenance

- **Adding a New Project**:
  1. Set up the project with branch-based GitHub Pages
  2. Add its sitemap URL to the sitemap index in the main repository
  3. Add a link to the project on your main landing page

- **Updating Sitemaps**:
  - Main repository: Automatically updates through GitHub Actions
  - Project repositories: Update manually as needed or set up your own automation