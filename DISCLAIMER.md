# Legal Disclaimer & Liability Notice

## Intended Use

Headless Marauder is a **security research and education tool** designed for:

- Authorized penetration testing of wireless networks you own or have explicit
  written permission to test
- Security research and vulnerability assessment in controlled lab environments
- Educational purposes — learning about WiFi protocols, 802.11 security, and
  wireless network behavior
- CTF (Capture The Flag) competitions and sanctioned security exercises
- Testing and hardening your own network infrastructure

## Legal Compliance

**You are solely responsible for ensuring your use of this software complies with all
applicable local, state, federal, and international laws.**

Many of the capabilities exposed by ESP32 Marauder firmware — including but not limited
to WiFi deauthentication, beacon flooding, probe request sniffing, evil portal attacks,
and Bluetooth spam — are **illegal to use against networks, devices, or individuals
without explicit authorization.** Relevant laws include but are not limited to:

- **United States:** Computer Fraud and Abuse Act (CFAA), FCC Part 15 regulations,
  Electronic Communications Privacy Act (ECPA), state-level computer crime statutes
- **European Union:** Directive 2013/40/EU on attacks against information systems,
  GDPR (for captured personal data), national implementations
- **United Kingdom:** Computer Misuse Act 1990, Wireless Telegraphy Act 2006
- **Canada:** Criminal Code §342.1 (unauthorized use of computer), Radiocommunication Act
- **Australia:** Criminal Code Act 1995 Part 10.7 (computer offences),
  Radiocommunications Act 1992

This is not exhaustive. Research the laws in your jurisdiction before use.

## Liability

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

**The author(s) and contributor(s) of Headless Marauder:**

- Accept **no responsibility or liability** for any damage, loss, legal consequences,
  or other harm resulting from the use or misuse of this software
- Make **no guarantees** about the accuracy, reliability, or completeness of the
  software or its output
- Do **not endorse or encourage** any illegal or unauthorized activity
- Are **not responsible** for actions taken by users of this software

By downloading, installing, or using this software, you acknowledge that:

1. You understand the capabilities of this tool and the associated legal risks
2. You will use it only in authorized, legal contexts
3. You accept full responsibility for your actions and any consequences
4. You will not hold the author(s) liable for any misuse

## Hardware & Firmware

This application is a **serial controller** — it sends text commands to an ESP32 board
running third-party Marauder firmware. The firmware itself is developed and maintained by
[justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) under
the GPL license. The authors of Headless Marauder are not affiliated with and do not
control the Marauder firmware project.

The built-in firmware flasher downloads binaries directly from the official Marauder
GitHub releases. **Verify firmware integrity yourself** — this tool does not perform
cryptographic signature verification on downloaded firmware files.

## Data Collection

Headless Marauder does **not** phone home, collect telemetry, or transmit any data to
external servers. All data — serial logs, AP/station captures, JSON snapshots — is stored
locally on your machine in a directory you choose. The Browser UI runs on localhost only
by default and does not expose data to the network unless you explicitly bind to `0.0.0.0`.

## Third-Party Dependencies

This software relies on open-source dependencies (PyQt5, Flask, pyserial, esptool,
Textual, etc.). The author(s) are not responsible for vulnerabilities or issues in
upstream packages. Review `requirements.txt` and `pyproject.toml` for the full
dependency list.

## Contact

For security issues, see [SECURITY.md](SECURITY.md).
For general questions, open an issue on
[GitHub](https://github.com/LxveAce/headless-marauder-gui/issues).
