# Account Lockout & Security Threat Remediation

**Article ID:** KB-SEC-001  
**Category:** IT  
**Last Updated:** 2026-03-01  

## Overview
To protect corporate systems against brute-force credential stuffing and unauthorized access, identity protection controls automatically monitor failed login attempts.

## Automatic Lockout Triggers
- **Failed Attempts Threshold:** An account is automatically locked after 5 consecutive incorrect password attempts within a 15-minute window.
- **Lockout Duration:** The account enters a temporary lockout state for 30 minutes. After 30 minutes, the account unlocks automatically, provided no further failed attempts occur.

## What to Do If Locked Out
1. Wait 30 minutes for the automatic cooling-off period to expire, then attempt login with your verified password.
2. If you need urgent access to meet a business-critical deadline:
   - Call the IT Emergency Hotline at extension 4357 (`HELP`) or `+1-800-555-4357`.
   - Your identity will be verified using out-of-band manager confirmation.

## Suspected Security Breaches
If you receive unexpected Okta push notifications, 2FA SMS codes, or password reset alerts that you did not initiate:
- Immediately email the Security Operations Center (SOC) at `security@company.com`.
- Do NOT approve any unprompted multi-factor authentication requests.
- The SOC will immediately invalidate all active sessions and issue a mandatory password reset.
