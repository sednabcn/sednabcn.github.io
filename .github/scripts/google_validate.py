import os
import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def main():
    sitemap_url = os.getenv("SITEMAP_URL")
    site_url = os.getenv("SITE_URL", "")  # e.g. "https://modelphysmat.com/"

    if not sitemap_url or not site_url:
        print("❌ Missing SITE_URL or SITEMAP_URL environment variables.")
        sys.exit(1)

    # Load service account JSON from env
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    if not creds_json:
        print("❌ Missing GOOGLE_SERVICE_ACCOUNT secret.")
        sys.exit(1)

    creds_info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/webmasters"]
    )

    # Build Search Console service
    service = build("searchconsole", "v1", credentials=creds)

    report_lines = []
    status_flag = "healthy"

    try:
        # Submit sitemap to GSC
        service.sitemaps().submit(siteUrl=site_url, feedpath=sitemap_url).execute()
        report_lines.append(f"📤 Sitemap submitted: {sitemap_url}")

        # Get sitemap status
        sitemap_info = service.sitemaps().get(siteUrl=site_url, feedpath=sitemap_url).execute()

        report_lines.append("### Google Search Console Status")
        report_lines.append(f"- Last Submitted: {sitemap_info.get('lastSubmitted', 'N/A')}")
        report_lines.append(f"- Last Checked: {sitemap_info.get('lastDownloaded', 'N/A')}")
        report_lines.append(f"- Status: {sitemap_info.get('isPending', False) and '⏳ Pending' or '✅ Processed'}")
        report_lines.append(f"- Warnings: {sitemap_info.get('warnings', 0)}")
        report_lines.append(f"- Errors: {sitemap_info.get('errors', 0)}")

        if sitemap_info.get("errors", 0) > 0:
            status_flag = "unhealthy"

    except Exception as e:
        report_lines.append(f"❌ Error while checking sitemap in GSC: {e}")
        status_flag = "unhealthy"

    # Write report to file
    with open("gsc_report.md", "w") as f:
        f.write("\n".join(report_lines))

    # Also print to GitHub summary
    print("::group::GSC Sitemap Report")
    print("\n".join(report_lines))
    print("::endgroup::")

    # Output status for workflow
    print(f"::set-output name=status::{status_flag}")

if __name__ == "__main__":
    main()
