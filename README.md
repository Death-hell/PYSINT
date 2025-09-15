# PYSINT — Python OSINT Scanner (Updated 2025)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]
[![Async](https://img.shields.io/badge/asyncio-modern-green.svg)]

**PYSINT** is a modular, Python-based **OSINT and web reconnaissance toolkit**, designed for **educational and authorized security testing**. This 2025 update introduces bug fixes, async support across most modules, a modernized interface, and a new GeoIP scanner.

---

## 🚀 What's New / 2025 Changes

- **Modernized code**: all scanners updated for readability and async/efficient requests.  
- **Async concurrency**: XSS, LFI, SQLi, directory-fuzzer, parameter-finder, and tech-detector now use `asyncio` + semaphores for safe, fast scanning.  
- **Bug fixes**: Resolved crashes on large wordlists or high-concurrency runs.  
- **New module added**: `geoip-scan.py` — quickly resolve IPs/domains and fetch location/ISP info.  
- **Rich output potential**: modules now structured for better readability (console or future GUI integration).  
- **Enhanced wordlists**: curated, modernized payloads and parameter lists.  
- **Cross-platform**: Tested on Linux and Termux; Windows requires minor adjustments.

---

## 🧩 Modules Overview

| #  | Module Name                     | Description                                                                 |
|----|---------------------------------|-----------------------------------------------------------------------------|
| 1  | Whois / IP Lookup               | Domain registration and IP ownership (RDAP/IPWhois).                       |
| 2  | DNS Lookup                      | Query DNS records (A, AAAA, MX, NS, TXT, CNAME) using `dnspython`.         |
| 3  | HTML Scraper                    | Retrieve page HTML (supports redirects).                                   |
| 4  | Email Extractor                 | Extract mailto/email patterns from HTML.                                    |
| 5  | Subdomain Finder                | Enumerate subdomains (crt.sh + checks).                                     |
| 6  | Parameter Scanner               | Test URL parameters against a wordlist (async).                             |
| 7  | Directory / File Scanner        | Async directory/file brute-force using a wordlist.                          |
| 8  | SSL / TLS Info                  | Retrieve certificate details, validity, SANs, and TLS version.             |
| 9  | HTTP Headers                    | Show server headers and security-related headers.                           |
| 10 | Wayback / Archive Lookup        | Query Wayback Machine snapshots (web.archive.org).                          |
| 11 | Technology / CMS Detection      | Detect CMS, frameworks, JS libraries (async).                               |
| 12 | Port / Service Scanner          | Scan common ports and report services (fast threaded scan).                 |
| 13 | Vulnerability Scanners          | **XSS, LFI, SQLi** (async, wordlist-based, reflective/error detection).     |
| 14 | GeoIP Scanner                   | Resolve IP/domain and display location, ISP, timezone (new module).         |
| 15 | Master CLI                      | Central CLI/launcher (`CLI.py`) to run modules from a single interface.     |

---

## 🧰 Wordlists

Curated, lightweight wordlists shipped with the repo:

- `XSS-wordlist.txt` — XSS payload candidates  
- `LFI-wordlist.txt` — typical LFI payloads (e.g., `../../etc/passwd`)  
- `SQLi-wordlist.txt` — common SQLi payloads (boolean, errors, quotes)  
- `directory-wordlist.txt` — directories and filenames for brute-force  
- `large-params.txt` — parameter names for parameter scanner  

> ⚠️ Tip: Avoid extremely large wordlists in the repo. For larger datasets, provide download links or release assets.

---

## 📦 Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/Death-hell/PYSINT.git
cd PYSINT
python3 -m pip install -r requirements.txt

Key Dependencies:

httpx

dnspython

ipwhois

beautifulsoup4

lxml

requests



---

⚙️ Quick Usage

Master CLI

python CLI.py

Run individual modules

python analyzer-whois.py
python dns-hunter.py
python get-html.py
python find-email-in-html.py
python subdomain-finder.py
python param-finder.py
python directory-fuzzer.py
python ssl-info.py
python headers.py
python wayback-Scan.py
python tech-detector.py
python port-scan.py
python geoip-scan.py

Vulnerability Scanners

# XSS Scanner (async)
python XSS-Scanner.py

# LFI Scanner (async)
python LFI-Scanner.py

# SQLi Scanner (async)
python SQLi-Scanner.py

Prompted inputs:

Target URL (include at least one ?param=value)

Which parameters to test (or blank for auto-detect)

Maximum payloads to try (0 = all)


Reports [VULNERABLE] or [SAFE] with full tested URL + HTTP status.



---

🛡️ Ethical & Legal Notice

Use responsibly — for educational and authorized testing only.

Obtain explicit permission before scanning targets.

Unauthorized scanning may be illegal.

Consider adding a --confirm flag or checklist in your workflow for safe operations.



---

🧪 Testing & Tips

Limit payloads (1–5) when testing vulnerability modules.

Test on local labs (DVWA, WebGoat, custom VMs) before live targets.

Respect rate limits: adjust async concurrency or semaphore values as needed.



---

🛠 Contributing

Add new modules (OSINT integrations, VirusTotal, SecurityTrails, etc.)

Improve detection heuristics (reduce false positives)

Add export/reporting formats (JSON/CSV)

Extend wordlists responsibly

Modular, well-documented PRs are preferred



---

📄 License

Licensed under MIT. See LICENSE for details.


---

📌 Notes

Compatible with Python 3.10+ (async features require modern Python).

Tested on Linux and Termux; minor Windows adjustments may be needed.

Wordlists live in repo root (consider wordlists/ folder for expansion).

Respect target load: batch scans and use concurrency limits for large scans.



---

> 🎉 PYSINT 2025 Edition — modular, async, modern, and safer OSINT toolkit!
