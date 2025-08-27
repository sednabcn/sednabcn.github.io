#!/usr/bin/env python3
"""
Quick email test for GitHub Actions debugging
Save this as test_email.py and run locally or add as a workflow step
"""
import os
import smtplib
from email.mime.text import MIMEText

# Get from environment or prompt
email_from = os.getenv('EMAIL_FROM')
email_password = os.getenv('EMAIL_PASSWORD') 
email_to = os.getenv('NOTIFICATION_EMAIL')

print("=== Email Test ===")
print(f"EMAIL_FROM: {'✅' if email_from else '❌'} {email_from or 'Not set'}")
print(f"EMAIL_PASSWORD: {'✅' if email_password else '❌'} {'[hidden]' if email_password else 'Not set'}")
print(f"NOTIFICATION_EMAIL: {'✅' if email_to else '❌'} {email_to or 'Not set'}")

if not all([email_from, email_password, email_to]):
    print("❌ Missing required environment variables")
    exit(1)

try:
    msg = MIMEText("This is a test email from your GitHub Actions workflow. If you received this, your email configuration is working!")
    msg['Subject'] = "🧪 GitHub Actions Email Test"
    msg['From'] = email_from
    msg['To'] = email_to

    print("Connecting to Gmail SMTP...")
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        print("Starting TLS...")
        server.starttls()
        print("Logging in...")
        server.login(email_from, email_password)
        print("Sending...")
        server.send_message(msg)
    
    print("✅ SUCCESS! Email sent.")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit(1)
