#!/usr/bin/env python3
"""
Test script to verify email configuration works
Run this locally to test your email settings before using in GitHub Actions
"""

import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def test_email():
    print("=== Email Configuration Test ===")
    
    # Get environment variables
    email_from = os.getenv('EMAIL_FROM') or input("Enter EMAIL_FROM (your Gmail): ")
    email_password = os.getenv('EMAIL_PASSWORD') or input("Enter EMAIL_PASSWORD (App Password): ")
    email_to = os.getenv('NOTIFICATION_EMAIL') or input("Enter NOTIFICATION_EMAIL: ")
    
    print(f"\nTesting email configuration:")
    print(f"From: {email_from}")
    print(f"To: {email_to}")
    print(f"Password: {'*' * len(email_password) if email_password else 'Not set'}")
    
    # Create test message
    subject = "🧪 Email Test from GitHub Actions Script"
    body = f"""
This is a test email to verify your email configuration works.

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

If you received this email, your configuration is working correctly!

Test details:
- SMTP Server: smtp.gmail.com:587
- From: {email_from}
- To: {email_to}

Next steps:
1. Add these values as GitHub Secrets:
   - EMAIL_FROM: {email_from}
   - EMAIL_PASSWORD: [your app password]
   - NOTIFICATION_EMAIL: {email_to}

2. Make sure you're using a Gmail App Password, not your regular password
3. Run your GitHub Actions workflow
    """.strip()
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = email_to
    
    try:
        print("\nConnecting to Gmail SMTP server...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            print("Starting TLS encryption...")
            server.starttls()
            
            print("Authenticating...")
            server.login(email_from, email_password)
            
            print("Sending test email...")
            server.send_message(msg)
            
        print("✅ SUCCESS! Test email sent successfully.")
        print(f"Check {email_to} for the test message.")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure you're using a Gmail App Password, not your regular password")
        print("2. Enable 2-Factor Authentication on your Gmail account")
        print("3. Generate an App Password at: https://myaccount.google.com/apppasswords")
        print("4. Use the 16-character app password (remove spaces)")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_email()
