# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.2.x   | Yes       |
| 1.1.x   | No        |
| 1.0.x   | No        |

Only the latest release receives security patches. Update with `git pull` or in-app
**Help > Check for Updates**.

## Reporting a Vulnerability

If you discover a security vulnerability in Headless Marauder, **do not open a public issue.**

Instead, report it privately:

1. **GitHub Security Advisories (preferred):** Go to the
   [Security tab](https://github.com/LxveAce/headless-marauder-gui/security/advisories)
   of this repository and click **"Report a vulnerability"**.
2. **Email:** Send details to **extrafadexd@gmail.com** with the subject line
   `[SECURITY] headless-marauder-gui`.

Include as much of the following as possible:

- Description of the vulnerability
- Steps to reproduce
- Affected version(s)
- Potential impact
- Suggested fix (if any)

## Response Timeline

- **Acknowledgment:** within 48 hours
- **Initial assessment:** within 7 days
- **Patch release:** as soon as a fix is verified, typically within 14 days for critical issues

## Scope

The following are **in scope** for security reports:

- Code execution vulnerabilities in the Python application
- Command injection through serial input/output handling
- Path traversal in log file writing or firmware flashing
- Unsafe deserialization or data handling
- Web UI (Flask/SocketIO) vulnerabilities — XSS, CSRF, unauthorized access when
  bound to `0.0.0.0`
- Dependencies with known CVEs that affect this project's usage

The following are **out of scope:**

- Vulnerabilities in the ESP32 Marauder firmware itself (report those to
  [justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder))
- Vulnerabilities in upstream dependencies where this project uses them as intended
  and cannot mitigate the issue
- Social engineering attacks
- Physical access attacks against the ESP32 hardware
- Issues that require the attacker to already have code execution on the host machine

## Web UI Security Notes

The Browser UI (`headless-marauder-web`) binds to **localhost only** (`127.0.0.1:5000`)
by default. This is intentional — the web interface has no authentication layer and
provides direct serial access to the connected ESP32.

If you bind to `0.0.0.0` (LAN access), understand that **anyone on your network can
control the board**. This is documented behavior, not a vulnerability. If you need
LAN access with authentication, consider placing it behind a reverse proxy with
HTTP basic auth or similar.

## Disclosure Policy

We follow coordinated disclosure. Once a fix is released, the vulnerability will be
publicly documented in the release notes and (if applicable) a GitHub Security Advisory.
We ask that reporters allow up to 14 days for a patch before public disclosure.
