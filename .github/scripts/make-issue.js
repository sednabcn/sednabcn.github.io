const fs = require('fs');

let reportContent = 'Report generation failed.';
try {
  reportContent = fs.readFileSync('sitemap-report.md', 'utf8');
  if (!reportContent.endsWith('\n')) reportContent += '\n';
} catch (error) {
  console.error('Could not read sitemap-report.md:', error.message);
}

const issueBody = `${reportContent}
**Workflow Run:** [#${process.env.GITHUB_RUN_NUMBER}](${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID})
**Triggered by:** ${process.env.GITHUB_EVENT_NAME}
**Issues Found:** ${process.env.ISSUES_COUNT}
**Fixes Applied:** ${process.env.FIXES_COUNT}

_Automatically created by the Enhanced Sitemap Monitor workflow._
`;

console.log(issueBody);
