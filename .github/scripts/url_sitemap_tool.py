import sys, requests

url = "https://sednabcn.github.io/sitemap.xml"
try:
    r = requests.get(url)
    r.raise_for_status()
    print(r.status_code)
    if r.status_code == 200:
        # You can now parse or process r.text or r.content
        print("Sitemap retrieved successfully!")
    else:
        print(f"Failed to fetch sitemap, status code: {r.status_code}")
        # process sitemap here
except Exception as e:
    print(f"Error fetching or processing sitemap: {e}")
    sys.exit(1)
