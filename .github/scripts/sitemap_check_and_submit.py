import subprocess
import os
import sys
import tabulate

SITE = "https://sednabcn.github.io/"
SITEMAP = "https://sednabcn.github.io/sitemap.xml"
SCRIPT = ".github/scripts/submit_status_sitemap.py"

def run_command(args):
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"::error ::Command failed:\n{e.stderr}")
        sys.exit(1)

# Step 1: Check current sitemap status
print("🔍 Checking sitemap status...")
check_cmd = ["python", SCRIPT, "--site", SITE, "--sitemaps", SITEMAP, "--status"]
status_output = run_command(check_cmd)

# Step 2: Parse status
status_line = next((line for line in status_output.splitlines() if "Status:" in line), None)

if status_line:
    status = status_line.split(":")[-1].strip().upper()
    print(f"::notice ::Sitemap status detected: {status}")

    if status == "NOT FETCHED" or status == "NOT_FETCHED":
        print("::warning ::Sitemap is still NOT FETCHED — re-submitting now...")
        submit_cmd = ["python", SCRIPT, "--site", SITE, "--sitemaps", SITEMAP]
        submission_output = run_command(submit_cmd)
        print("::notice ::Sitemap re-submission completed.")
        print(submission_output)
    else:
        print("::notice ::Sitemap already submitted and fetched. No action required.")
else:
    print("::error ::Could not find sitemap status in output. Check if the sitemap exists in GSC.")
    sys.exit(1)
