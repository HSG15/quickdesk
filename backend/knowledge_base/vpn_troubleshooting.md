# VPN Setup and Troubleshooting Policy

**Article ID:** KB-IT-001  
**Category:** IT  
**Last Updated:** 2026-01-15  

## Overview
QuickDesk employees working remotely must connect to the corporate network via the GlobalProtect VPN client to access internal databases, code repositories, and local intranet services.

## Standard Configuration
- **VPN Gateway Address:** `vpn.company.com`
- **Secondary Gateway (Fallback):** `vpn-backup.company.com`
- **Authentication:** Corporate email and Single Sign-On (SSO) password, followed by an Okta push notification.

## Common Issues & Troubleshooting Steps
1. **Error 800 (Gateway Unreachable):**
   - Verify that your local home internet connection is active.
   - Ensure your home router allows outbound traffic on ports 443 (HTTPS) and 1194 (UDP).
   - Flush your local DNS cache (`sudo dscacheutil -flushcache` on macOS).
2. **Error 691 / Authentication Failure:**
   - Verify that your corporate SSO password has not expired.
   - If you recently reset your password, open macOS Keychain or Windows Credential Manager and delete cached entries for `vpn.company.com`.
3. **Certificate Expired or Invalid:**
   - Download the updated internal root certificate authority bundle from `https://pki.internal.company.com/root.crt`.
   - Restart the VPN client.
4. **Frequent Disconnections:**
   - Switch from Wi-Fi to a wired Ethernet connection if possible.
   - Toggle the gateway from `vpn.company.com` to `vpn-backup.company.com`.
