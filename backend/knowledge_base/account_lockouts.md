# Account Lockout & Security Threat Remediation

**Article ID:** KB-SEC-001  
**Category:** IT  
**Last Updated:** 2026-10-25

## Account lockout
- The account locks after 5 consecutive incorrect password attempts within 15 minutes.
- Lockout lasts 30 minutes if no further failed attempts occur.
- Wait 30 minutes, then retry with the correct password. For urgent access, call IT Emergency Hotline extension 4357 (HELP) or +1-800-555-4357. Identity verification through manager confirmation is required.

## Suspicious MFA or reset alerts
If you receive an Okta push, SMS code, or password-reset alert you did not initiate:
- Do not approve the request or share the code.
- Email **security@company.com** immediately.
- Include the time and a short description, but never include passwords or authentication codes.
- Security Operations may invalidate active sessions and require a password reset.

## Ticket details
Include the affected application, exact error, time, device type, and whether other company services work. Never include passwords or one-time codes.

## Quick FAQs
- **Lockout threshold:** 5 failed attempts within 15 minutes.
- **Lockout duration:** 30 minutes.
- **Unexpected MFA prompt:** Do not approve it; email security@company.com.

## Demo tickets
- **Title:** My company account is locked  
  **Description:** I entered my password incorrectly several times and now cannot sign in. How long should I wait?
- **Title:** I received an unexpected MFA prompt  
  **Description:** My phone received an Okta approval request I did not initiate. I have not approved it. What should I do?
