#!/usr/bin/env python3
"""
Email Sitemap Reporter
Automated email reporting system for sitemap monitoring results
Integrates with the sitemap CLI tool and GitHub Actions
"""

import os
import sys
import json
import smtplib
import ssl
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import requests

try:
    import markdown2
    from jinja2 import Template
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install markdown2 jinja2")
    sys.exit(1)

class EmailSitemapReporter:
    def __init__(self, smtp_config: Dict):
        """Initialize email reporter with SMTP configuration"""
        self.smtp_config = smtp_config
        self.validate_smtp_config()
    
    def validate_smtp_config(self):
        """Validate SMTP configuration"""
        required_fields = ['server', 'port', 'username', 'password', 'from_email']
        missing_fields = [field for field in required_fields if field not in self.smtp_config]
        
        if missing_fields:
            raise ValueError(f"Missing SMTP configuration fields: {missing_fields}")
    
    def load_sitemap_results(self, results_file: str) -> Dict:
        """Load sitemap monitoring results from JSON file"""
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Results file not found: {results_file}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in results file: {results_file}")
    
    def generate_email_template(self) -> str:
        """Generate Jinja2 email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sitemap Monitor Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }
        .status-healthy {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .status-issues {
            background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
        }
        .status-error {
            background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
            text-align: center;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 2.5em;
        }
        .summary-card p {
            margin: 0;
            color: #6c757d;
            font-weight: 500;
        }
        .sitemap-item {
            background: #fff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #28a745;
        }
        .sitemap-item.error {
            border-left-color: #dc3545;
        }
        .sitemap-item.warning {
            border-left-color: #ffc107;
        }
        .sitemap-url {
            font-weight: bold;
            color: #007bff;
            word-break: break-all;
            margin-bottom: 10px;
        }
        .sitemap-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .detail-item {
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .detail-label {
            font-weight: bold;
            color: #495057;
        }
        .issues-section, .fixes-section {
            margin: 30px 0;
        }
        .issues-section {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
        }
        .fixes-section {
            background: #d1edff;
            border: 1px solid #74b9ff;
            border-radius: 8px;
            padding: 20px;
        }
        .issue-item, .fix-item {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .issue-item:last-child, .fix-item:last-child {
            border-bottom: none;
        }
        .recommendations {
            background: #e8f5e8;
            border: 1px solid #c3e6c3;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .recommendations h3 {
            color: #2d5a2d;
            margin-top: 0;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            color: #6c757d;
        }
        .button {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 5px;
        }
        .emoji {
            font-size: 1.2em;
        }
        @media (max-width: 600px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
            .sitemap-details {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header {% if results.summary.overall_status == 'healthy' %}status-healthy{% elif results.summary.overall_status == 'issues_detected' %}status-issues{% else %}status-error{% endif %}">
            <h1>
                {% if results.summary.overall_status == 'healthy' %}
                    <span class="emoji">✅</span> Sitemap Status: HEALTHY
                {% elif results.summary.overall_status == 'issues_detected' %}
                    <span class="emoji">⚠️</span> Sitemap Status: ISSUES DETECTED
                {% else %}
                    <span class="emoji">❌</span> Sitemap Status: ERROR
                {% endif %}
            </h1>
            <p><strong>Site:</strong> {{ results.site_url }}</p>
            <p><strong>Generated:</strong> {{ results.timestamp | format_datetime }}</p>
        </div>

        <!-- Summary Statistics -->
        <div class="summary-grid">
            <div class="summary-card">
                <h3>{{ results.summary.total_sitemaps }}</h3>
                <p>Total Sitemaps</p>
            </div>
            <div class="summary-card">
                <h3>{{ results.summary.healthy_sitemaps }}</h3>
                <p>Healthy Sitemaps</p>
            </div>
            <div class="summary-card">
                <h3>{{ results.summary.issues_found }}</h3>
                <p>Issues Found</p>
            </div>
            <div class="summary-card">
                <h3>{{ results.summary.fixes_applied }}</h3>
                <p>Fixes Applied</p>
            </div>
        </div>

        <!-- Sitemap Details -->
        <h2><span class="emoji">🗺️</span> Sitemap Details</h2>
        {% for sitemap in results.sitemaps %}
        <div class="sitemap-item {% if 'error' in sitemap.action.lower() or 'failed' in sitemap.action.lower() %}error{% elif 'warning' in sitemap.action.lower() %}warning{% endif %}">
            <div class="sitemap-url">{{ sitemap.url }}</div>
            
            <div class="sitemap-details">
                <div class="detail-item">
                    <span class="detail-label">Status:</span> {{ sitemap.action }}
                </div>
                {% if sitemap.validation %}
                <div class="detail-item">
                    <span class="detail-label">Validation:</span> 
                    {% if sitemap.validation.is_valid %}✅ Valid{% else %}❌ Invalid{% endif %}
                </div>
                {% endif %}
                {% if sitemap.lastDownloaded %}
                <div class="detail-item">
                    <span class="detail-label">Last Downloaded:</span> {{ sitemap.lastDownloaded }}
                </div>
                {% endif %}
                {% if sitemap.errors is defined and sitemap.errors > 0 %}
                <div class="detail-item">
                    <span class="detail-label">Errors:</span> <strong style="color: #dc3545;">{{ sitemap.errors }}</strong>
                </div>
                {% endif %}
                {% if sitemap.warnings is defined and sitemap.warnings > 0 %}
                <div class="detail-item">
                    <span class="detail-label">Warnings:</span> <strong style="color: #ffc107;">{{ sitemap.warnings }}</strong>
                </div>
                {% endif %}
            </div>
        </div>
        {% endfor %}

        <!-- Issues Section -->
        {% if results.issues_found %}
        <div class="issues-section">
            <h3><span class="emoji">⚠️</span> Issues Found</h3>
            {% for issue in results.issues_found %}
            <div class="issue-item">• {{ issue }}</div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Fixes Section -->
        {% if results.fixes_applied %}
        <div class="fixes-section">
            <h3><span class="emoji">🔧</span> Fixes Applied</h3>
            {% for fix in results.fixes_applied %}
            <div class="fix-item">• {{ fix }}</div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Recommendations -->
        {% if results.summary.issues_found > 0 %}
        <div class="recommendations">
            <h3><span class="emoji">💡</span> Recommendations</h3>
            <ul>
                <li>Review the issues listed above and address any underlying problems</li>
                <li>Check your sitemap XML files for proper formatting and valid URLs</li>
                <li>Ensure all URLs in your sitemaps are accessible and return proper HTTP status codes</li>
                <li>Monitor Google Search Console for additional insights and indexing status</li>
                <li>Consider implementing automated sitemap validation in your deployment process</li>
            </ul>
        </div>
        {% endif %}

        <!-- Action Buttons -->
        <div style="text-align: center; margin: 30px 0;">
            {% if workflow_url %}
            <a href="{{ workflow_url }}" class="button">View Workflow Run</a>
            {% endif %}
            {% if search_console_url %}
            <a href="{{ search_console_url }}" class="button">Open Search Console</a>
            {% endif %}
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>This report was automatically generated by the Sitemap Monitor system.</p>
            <p>Next check: {{ next_check_time | format_datetime if next_check_time else 'As scheduled' }}</p>
        </div>
    </div>
</body>
</html>
"""
    
    def format_datetime_filter(self, timestamp_str: str) -> str:
        """Custom filter to format datetime strings"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y at %H:%M UTC")
        except:
            return timestamp_str
    
    def generate_html_report(self, results: Dict, workflow_url: str = None) -> str:
        """Generate HTML email report from results"""
        template_str = self.generate_email_template()
        template = Template(template_str)
        
        # Add custom filters
        template.globals['format_datetime'] = self.format_datetime_filter
        
        # Prepare template variables
        template_vars = {
            'results': results,
            'workflow_url': workflow_url,
            'search_console_url': f"https://search.google.com/search-console?resource_id={results.get('site_url', '')}",
            'next_check_time': None  # Can be calculated based on schedule
        }
        
        return template.render(**template_vars)
    
    def generate_text_report(self, results: Dict) -> str:
        """Generate plain text version of the report"""
        lines = []
        summary = results.get('summary', {})
        
        # Header
        lines.append("SITEMAP MONITOR REPORT")
        lines.append("=" * 50)
        lines.append(f"Site: {results.get('site_url', 'Unknown')}")
        lines.append(f"Generated: {results.get('timestamp', 'Unknown')}")
        lines.append("")
        
        # Status
        status = summary.get('overall_status', 'unknown')
        if status == 'healthy':
            lines.append("STATUS: ✅ HEALTHY")
        elif status == 'issues_detected':
            lines.append("STATUS: ⚠️ ISSUES DETECTED")
        else:
            lines.append("STATUS: ❌ ERROR")
        lines.append("")
        
        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 20)
        lines.append(f"Total Sitemaps: {summary.get('total_sitemaps', 0)}")
        lines.append(f"Healthy Sitemaps: {summary.get('healthy_sitemaps', 0)}")
        lines.append(f"Issues Found: {summary.get('issues_found', 0)}")
        lines.append(f"Fixes Applied: {summary.get('fixes_applied', 0)}")
        lines.append("")
        
        # Sitemap details
        lines.append("SITEMAP DETAILS")
        lines.append("-" * 20)
        for sitemap in results.get('sitemaps', []):
            lines.append(f"URL: {sitemap.get('url', 'Unknown')}")
            lines.append(f"Status: {sitemap.get('action', 'Unknown')}")
            if sitemap.get('validation'):
                val = sitemap['validation']
                lines.append(f"Validation: {'✅ Valid' if val.get('is_valid') else '❌ Invalid'} - {val.get('message', '')}")
            if sitemap.get('errors', 0) > 0:
                lines.append(f"Errors: {sitemap['errors']}")
            if sitemap.get('warnings', 0) > 0:
                lines.append(f"Warnings: {sitemap['warnings']}")
            lines.append("")
        
        # Issues
        if results.get('issues_found'):
            lines.append("ISSUES FOUND")
            lines.append("-" * 20)
            for issue in results['issues_found']:
                lines.append(f"• {issue}")
            lines.append("")
        
        # Fixes
        if results.get('fixes_applied'):
            lines.append("FIXES APPLIED")
            lines.append("-" * 20)
            for fix in results['fixes_applied']:
                lines.append(f"• {fix}")
            lines.append("")
        
        return "\n".join(lines)
    
    def send_email(self, recipients: List[str], results: Dict, 
                   workflow_url: str = None, include_json: bool = False) -> bool:
        """Send email report to recipients"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            
            # Email subject based on status
            summary = results.get('summary', {})
            status = summary.get('overall_status', 'unknown')
            issues_count = summary.get('issues_found', 0)
            
            if status == 'healthy':
                subject = f"✅ Sitemap Status: All Healthy ({results.get('site_url', 'Site')})"
            elif status == 'issues_detected':
                subject = f"⚠️ Sitemap Alert: {issues_count} Issue(s) Found ({results.get('site_url', 'Site')})"
            else:
                subject = f"❌ Sitemap Error: Monitor Failed ({results.get('site_url', 'Site')})"
            
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(recipients)
            
            # Generate content
            text_content = self.generate_text_report(results)
            html_content = self.generate_html_report(results, workflow_url)
            
            # Attach content
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Attach JSON results if requested
            if include_json:
                json_attachment = MIMEBase('application', 'json')
                json_attachment.set_payload(json.dumps(results, indent=2))
                encoders.encode_base64(json_attachment)
                json_attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename="sitemap-results-{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
                )
                msg.attach(json_attachment)
            
            # Send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls(context=context)
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {len(recipients)} recipient(s)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_summary_digest(self, recipients: List[str], multiple_results: List[Dict]) -> bool:
        """Send a digest email with multiple site results"""
        try:
            # Create summary of all sites
            total_sites = len(multiple_results)
            healthy_sites = sum(1 for r in multiple_results if r.get('summary', {}).get('overall_status') == 'healthy')
            total_issues = sum(r.get('summary', {}).get('issues_found', 0) for r in multiple_results)
            
            # Create digest message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📊 Sitemap Digest: {healthy_sites}/{total_sites} Sites Healthy"
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(recipients)
            
            # Generate digest content
            digest_lines = []
            digest_lines.append("SITEMAP MONITORING DIGEST")
            digest_lines.append("=" * 50)
            digest_lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
            digest_lines.append("")
            digest_lines.append(f"Total Sites Monitored: {total_sites}")
            digest_lines.append(f"Healthy Sites: {healthy_sites}")
            digest_lines.append(f"Sites with Issues: {total_sites - healthy_sites}")
            digest_lines.append(f"Total Issues Found: {total_issues}")
            digest_lines.append("")
            
            digest_lines.append("SITE SUMMARY")
            digest_lines.append("-" * 30)
            
            for result in multiple_results:
                site = result.get('site_url', 'Unknown')
                status = result.get('summary', {}).get('overall_status', 'unknown')
                issues = result.get('summary', {}).get('issues_found', 0)
                
                status_icon = "✅" if status == 'healthy' else "⚠️" if status == 'issues_detected' else "❌"
                digest_lines.append(f"{status_icon} {site} - {issues} issues")
            
            digest_content = "\n".join(digest_lines)
            msg.attach(MIMEText(digest_content, 'plain', 'utf-8'))
            
            # Send digest
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls(context=context)
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            print(f"✅ Digest email sent successfully to {len(recipients)} recipient(s)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send digest email: {e}")
            return False

def load_email_config() -> Dict:
    """Load email configuration from environment variables"""
    config = {
        'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'port': int(os.getenv('SMTP_PORT', '587')),
        'username': os.getenv('SMTP_USERNAME'),
        'password': os.getenv('SMTP_PASSWORD'),
        'from_email': os.getenv('SMTP_FROM_EMAIL')
    }
    
    # Validate required fields
    if not all([config['username'], config['password'], config['from_email']]):
        raise ValueError("Missing required email configuration. Set SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL environment variables.")
    
    return config

def main():
    parser = argparse.ArgumentParser(description='Email Sitemap Reporter')
    parser.add_argument('--results', required=True, help='Path to sitemap results JSON file')
    parser.add_argument('--recipients', required=True, nargs='+', help='Email recipients')
    parser.add_argument('--workflow-url', help='GitHub workflow URL')
    parser.add_argument('--include-json', action='store_true', help='Attach JSON results file')
    parser.add_argument('--test-email', action='store_true', help='Send test email')
    
    args = parser.parse_args()
    
    try:
        # Load email configuration
        email_config = load_email_config()
        reporter = EmailSitemapReporter(email_config)
        
        if args.test_email:
            # Send test email
            test_results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'site_url': 'https://example.com',
                'summary': {
                    'total_sitemaps': 1,
                    'healthy_sitemaps': 1,
                    'issues_found': 0,
                    'fixes_applied': 0,
                    'overall_status': 'healthy'
                },
                'sitemaps': [{
                    'url': 'https://example.com/sitemap.xml',
                    'action': 'healthy',
                    'validation': {'is_valid': True, 'message': 'Valid sitemap with 100 URLs'}
                }],
                'issues_found': [],
                'fixes_applied': []
            }
            
            success = reporter.send_email(args.recipients, test_results, args.workflow_url, args.include_json)
            sys.exit(0 if success else 1)
        
        # Load and send actual results
        results = reporter.load_sitemap_results(args.results)
        success = reporter.send_email(args.recipients, results, args.workflow_url, args.include_json)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
