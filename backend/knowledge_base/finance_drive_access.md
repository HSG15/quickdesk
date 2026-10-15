# Finance Shared Drive Permissions & Security Policy

**Article ID:** KB-FIN-001  
**Category:** Finance  
**Last Updated:** 2026-01-20  

## Overview
The Finance Shared Drive (`\\corp.internal\finance\shared`) contains sensitive financial disclosures, payroll spreadsheets, audit logs, and vendor invoices. Strict principle-of-least-privilege access controls apply.

## Access Request Procedure
1. **Department Manager Approval:**
   - The requesting employee must email their direct manager detailing the business justification and specific sub-folders required (e.g., `Billing`, `Payroll_Reports`, `Accounts_Payable`).
2. **Head of Finance Sign-off:**
   - The direct manager must forward the request to `finance-approvals@company.com` for executive review.
3. **IT Provisioning Ticket:**
   - Once written approval is granted, open a QuickDesk ticket under the **Finance** category.
   - Attach the approval email PDF or screenshot.
   - The IT Systems team will provision active directory security group membership within 24 hours.

## Security Constraints
- Downloading confidential spreadsheets to non-corporate unmanaged devices is strictly forbidden.
- Access is audited quarterly; inactive permissions will be revoked automatically after 60 days of zero access.
