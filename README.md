
---

# 🧰 PyToolKit — Python OSINT & Security Toolkit (2025 Edition)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge)](https://www.python.org/downloads/)
[![Async Ready](https://img.shields.io/badge/asyncio-modern-green?style=for-the-badge)](https://docs.python.org/3/library/asyncio.html)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)

> **PyToolKit** is a modern, modular, and async-ready Python toolkit for **OSINT reconnaissance, web scanning, and security testing** — redesigned in 2025 for performance, reliability, and usability.  
> ✅ **Ethical Use Only** — For educational purposes and authorized assessments.

---

## 🌟 What’s New in 2025?

We didn’t just update — we **re-engineered**.

- ✨ **All modules refactored** with clean, maintainable, production-ready code
- ⚡ **Async I/O everywhere** — XSS, SQLi, LFI, Directory, Tech-Detect, Param-Finder now use `asyncio` + `httpx` for blazing-fast scans
- 🛡️ **Error-proof & robust** — No more crashes on large wordlists or network timeouts
- 🌍 **New `geoip-scan.py`** — Instantly resolve IPs/domains to location, ISP, timezone
- 🎨 **Rich CLI interface** — Beautiful tables, progress bars, color-coded results via `rich`
- 📁 **Structured output** — All scans auto-save to `~/PyToolKit/results/` in **JSON + CSV**
- 🧭 **Full CLI support** — Every tool now has `--help`, `--debug`, and batch mode
- 📦 **Lightweight & curated** — No bloat. Only essential, battle-tested wordlists included

---

## 🧩 Toolkit Modules

| Category           | Module                  | Description                                                                 |
|--------------------|-------------------------|-----------------------------------------------------------------------------|
| 🔍 Intelligence     | `analyzer-whois.py`     | WHOIS & RDAP lookup for domains and IPs                                     |
| 🌐 DNS             | `dns-hunter.py`         | Query A, MX, TXT, CNAME, NS records from multiple resolvers                 |
| 🕸️ Web Fetch       | `get-html.py`           | Fetch and preview raw HTML content                                          |
| 📧 Email Hunter    | `find-email-in-html.py` | Extract emails from page source                                             |
| 🌳 Subdomains      | `subdomain-finder.py`   | Discover subdomains via crt.sh + active verification                        |
| 🔑 Parameters      | `param-finder.py`       | Brute-force URL parameters (async, configurable wordlist)                   |
| 📂 Directories     | `directory-fuzzer.py`   | Find hidden paths/files (async, progress-tracked)                           |
| 🔐 SSL/TLS         | `ssl-info.py`           | Inspect certificates, validity, SANs, TLS version                           |
| 📦 Headers         | `headers.py`            | Display HTTP headers + security analysis (HSTS, CSP, etc.)                  |
| 🕰️ Archives        | `wayback-Scan.py`       | Query historical snapshots from Wayback Machine                             |
| 🧩 Technologies    | `tech-detector.py`      | Detect CMS, frameworks, JS libs, servers (async, header+HTML patterns)      |
| 🚪 Ports           | `port-scan.py`          | Fast TCP port scanner for common services                                   |
| 💥 Vulnerabilities | `XSS-Scanner.py`        | Reflective XSS detection via payload injection                              |
|                    | `LFI-Scanner.py`        | Local File Inclusion scanner with content heuristics                        |
|                    | `SQLi-Scanner.py`       | SQL Injection scanner via error-based detection                             |
| 🌎 GeoIP           | `geoip-scan.py`         | **NEW!** Resolve location, ISP, timezone from IP/domain                     |
| 🎮 Launcher        | `CLI.py`                | Master menu to launch any module from one interface                         |

---

## 📚 Included Wordlists (Lightweight & Curated)

- `XSS-wordlist.txt` — XSS injection payloads
- `LFI-wordlist.txt` — Path traversal payloads (`/etc/passwd`, `C:\Windows\`, etc.)
- `SQLi-wordlist.txt` — SQL injection strings (error-based, boolean, stacked)
- `directory-wordlist.txt` — Common directories and files for fuzzing
- `large-params.txt` — Hundreds of parameter names for discovery
- `usernames.txt` / `passwords.txt` — Sample lists for brute-force (add your own!)

> 💡 **Pro Tip**: Keep wordlists lean. For enterprise use, mount external lists or use `--wordlist` flags.

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Death-hell/PyToolKit.git
cd PyToolKit
pip install -r requirements.txt
```

### 2. Run the Master CLI

```bash
python CLI.py
```

### 3. Or Run Any Module Directly

```bash
python geoip-scan.py --target cloudflare.com --debug
python XSS-Scanner.py --url "https://test.com/search?q=test" --params q --max-payloads 50
python tech-detector.py --url https://github.com --debug
```

### 4. View Results

All scans auto-save to:
```
~/PyToolKit/results/
```

---

## 🛡️ Ethical & Legal Notice

> ⚠️ **USE RESPONSIBLY. FOR AUTHORIZED TESTING ONLY.**

- ✅ Always obtain **explicit written permission** before scanning.
- ✅ Use on **your own systems** or **bug bounty programs**.
- ❌ Never scan without consent — it may be **illegal**.
- 💡 Consider adding `--confirm` or interactive prompts for safety.

---

## 🧪 Pro Tips for Testing

- 🎯 Start with `--max-payloads 5` or `--limit 10` to test modules quickly
- 🧪 Use local labs: **DVWA**, **OWASP Juice Shop**, **WebGoat**
- ⏱️ Respect rate limits — adjust `--concurrent` or add `--delay`
- 💾 Always check `~/PyToolKit/results/` — full context saved in JSON/CSV

---

## 🤝 Contributing

We ❤️ contributions! Here’s how to help:

- ➕ Add new OSINT modules (SecurityTrails, Shodan, VirusTotal, etc.)
- 🎯 Improve detection logic (reduce false positives/negatives)
- 📤 Add export formats: HTML, Markdown, PDF reports
- 📂 Organize wordlists into `/wordlists/` directory
- 🧹 Code cleanup, type hints, unit tests
- 📖 Improve documentation and examples

> ✨ **Modular, documented, and tested PRs get merged fastest!**

---

## 📜 License

**MIT License** — Free for personal, educational, and commercial use.

See [LICENSE](LICENSE) for full terms.

---

## 📌 System Requirements

- **Python 3.10+** (async/await syntax required)
- **Linux / Termux** — Fully tested
- **Windows** — Works with minor adjustments (path separators, asyncio policy)
- **Dependencies**: `httpx`, `dnspython`, `ipwhois`, `requests`, `rich`, `beautifulsoup4`, `lxml`

---

## 🌈 Why PyToolKit?

> Because OSINT shouldn’t be messy.

PyToolKit brings **structure, speed, and safety** to your reconnaissance workflow. Whether you’re a student, pentester, or bug hunter — this toolkit grows with you.

---

> 🚀 **PyToolKit 2025 — Where elegance meets efficiency in OSINT.**

---

✅ **Ready to clone, run, and dominate your recon game.**  
✅ **100% GitHub-optimized.**  
✅ **Zero fluff. Maximum utility.**

---

📌 **Star ⭐ the repo if you find it useful!**  
💬 **Open an issue if you need help or have ideas!**

---
