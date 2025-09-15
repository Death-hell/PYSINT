
# PYSINT — Python OSINT Scanner

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]

PYSINT is a modular, Python-based **OSINT (Open Source Intelligence) scanner** built for education and authorized security testing. It gathers information about domains, IPs and web applications using a collection of lightweight, easy-to-run modules.

---

## 🚀 What’s included

PYSINT is intentionally modular — run single checks or chain multiple modules for a full reconnaissance run. New (2025) additions: async vulnerability scanners and wordlists.

| #  | Module Name                     | Description                                                                 |
|----|---------------------------------|-----------------------------------------------------------------------------|
| 1  | Whois / IP Lookup               | Domain registration and IP ownership (RDAP/IPWhois).                       |
| 2  | DNS Lookup                      | Query DNS records (A, AAAA, MX, NS, TXT, CNAME) using `dnspython`.         |
| 3  | HTML Scraper                    | Retrieve page HTML (supports redirects).                                   |
| 4  | Email Extractor                 | Extract mailto/email patterns from HTML.                                    |
| 5  | Subdomain Finder                | Enumerate subdomains (crt.sh + checks).                                     |
| 6  | Parameter Scanner               | Test URL parameters against a parameter wordlist.                           |
| 7  | Directory / File Scanner        | Async directory/file brute-force using a directory wordlist.                |
| 8  | SSL / TLS Info                  | Retrieve certificate details and TLS version.                               |
| 9  | HTTP Headers                    | Show server headers and security-related headers.                           |
| 10 | Wayback / Archive Lookup        | Query Wayback Machine snapshots (web.archive.org).                          |
| 11 | Technology / CMS Detection      | Detect CMS, frameworks and JS libs (async).                                 |
| 12 | Port / Service Scanner          | Scan common ports and report services (fast threaded scan).                 |
| 13 | Vulnerability Scanners          | **XSS, LFI and SQLi** (async scanners using wordlists and reflection/error checks). |
| 14 | Master CLI                      | Central CLI/launcher (`CLI.py`) to run modules from a single interface.     |

---

## 🧰 Wordlists

Ship with curated wordlists (keep them small and useful):

- `XSS-wordlist.txt` — XSS payload candidates
- `LFI-wordlist.txt` — typical LFI payloads and paths (e.g. `../../etc/passwd`, `/etc/passwd`)
- `SQLi-wordlist.txt` — common SQLi payloads (quotations, boolean, errors)
- `directory-wordlist.txt` — directories and filenames to brute-force
- `large-params.txt` — parameter names for parameter scanner

> **Tip:** Avoid committing extremely large wordlists. If you want bigger lists, include them via a release asset or provide links in the README.

---

## 📦 Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/Death-hell/PYSINT.git
cd PYSINT
python3 -m pip install -r requirements.txt

Requirements (examples):

httpx

dnspython

ipwhois

beautifulsoup4

lxml


(See requirements.txt for pinned versions.)


---

⚙️ Quick Usage

Run the master CLI (menu):

python CLI.py

Run a single module:

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

Vulnerability scanners (examples):

# XSS scanner (async). Provide a URL with params and a payload limit when prompted
python XSS-Scanner.py

# LFI scanner (async)
python LFI-Scanner.py

# SQLi scanner (async)
python SQLi-Scanner.py

Each vuln scanner asks:

Target URL (include at least one ?param=value)

Which parameters to test (or blank to auto-detect)

Maximum payloads to try (0 = all)


They report [VULNERABLE] or [SAFE] and print the full tested URL + HTTP status.


---

🛡️ Ethical / Legal Notice

Use responsibly.
This project is intended for educational purposes and authorized testing only. You must have explicit permission to scan any target. The author is not responsible for misuse. Unauthorized scanning or attacks may be illegal.

Add a --confirm flag or checklist in your workflow to ensure targets are authorized before running automated scans.


---

🧪 Testing & Tips

When testing the vulnerability modules, limit payloads to 1 or 5 to avoid accidental high traffic.

Run scans against local lab instances (DVWA, WebGoat, custom VMs) before targeting real sites.

Use small concurrency limits if you are scanning fragile targets:

Modify httpx.AsyncClient or add semaphore logic if needed.




---

🛠 Contributing

Contributions are welcome:

Add new modules (e.g., OSINT integrations, VirusTotal, SecurityTrails)

Improve detection heuristics (fewer false positives)

Add export/reporting (JSON/CSV) and CI checks

Extend wordlists responsibly


Please open an issue or a pull request. Keep changes modular and well-documented.


---

📄 License

This project is licensed under the MIT License. See LICENSE for details.


---

📌 Notes

Compatible with Python 3.10+ (async features require modern Python).

Tested on Linux and Termux; minor adjustments may be necessary on Windows.

Wordlists live in the repository root — consider splitting them into wordlists/ if you expand the set.

For large scans, respect rate limits and target load — consider batching payloads and lowering concurrency.



---