# VPN Setup and Troubleshooting Policy

**Article ID:** KB-IT-001  
**Category:** IT  
**Last Updated:** 2026-10-25

## Configuration
Use the GlobalProtect VPN client.
- **Primary gateway:** `vpn.company.com`
- **Backup gateway:** `vpn-backup.company.com`
- Sign in with corporate email and SSO password, then approve the Okta prompt you initiated.

## Common problems
### Error 800 / gateway unreachable
1. Check that your internet works without VPN.
2. Restart GlobalProtect and retry.
3. Try `vpn-backup.company.com`.
4. If unresolved, open an IT ticket with the error, OS, network type, and time.
5. On macOS, IT or an experienced user may flush DNS with `sudo dscacheutil -flushcache`.

### Error 691 / authentication failure
1. Check whether your SSO password has expired.
2. After a password reset, remove cached `vpn.company.com` entries from macOS Keychain or Windows Credential Manager.
3. Reconnect. If it still fails, contact IT.

### Certificate error
The supplied policy lists the internal certificate location `https://pki.internal.company.com/root.crt`. Install certificates only after verifying the source and current instructions with IT.

### Frequent disconnections
Try wired Ethernet or move closer to Wi-Fi. Switch to the backup gateway and note when disconnects happen.

Never approve an MFA request you did not initiate or share passwords/codes in a ticket.

## Quick FAQs
- **VPN gateway:** `vpn.company.com`.
- **Backup:** `vpn-backup.company.com`.
- **Error 800:** Check internet, restart VPN, try backup gateway.
- **Error 691 after password change:** Clear cached VPN credentials and reconnect.

## Demo tickets
- **Title:** VPN shows Error 800  
  **Description:** I am working from home and GlobalProtect says gateway unreachable, but my internet works. What should I try?
- **Title:** VPN keeps disconnecting on Wi-Fi  
  **Description:** My VPN disconnects several times each hour while I work remotely. What steps should I take before contacting IT?


## Wi-Fi and network connectivity
This section gives basic checks for Wi-Fi problems. The company-specific network name and configuration should be confirmed by IT.

1. Check that Wi-Fi is enabled and airplane mode is off.
2. Confirm you are on the approved corporate network; do not join unknown networks imitating the company name.
3. Toggle Wi-Fi off and on, then reconnect.
4. Check whether other devices are affected. If only internal sites fail, connect to VPN if required.
5. For home Wi-Fi, check router power and cables. Restart the router only if it will not disrupt other users.
6. For slow or unstable Wi-Fi, move closer to the access point or use Ethernet if available.

When opening a ticket, include device/OS, office or remote location, network name (never its password), start time, affected devices, and exact error. Do not disable endpoint security or install unknown network utilities.

**Wi-Fi FAQ:** If connected but there is no internet, toggle Wi-Fi, test another trusted website, and check whether other devices are affected.

**Demo ticket — Wi-Fi:**  
**Title:** Connected to Wi-Fi but no internet  
**Description:** My laptop connects to Wi-Fi, but websites do not load. What basic checks should I try before opening an IT ticket?
