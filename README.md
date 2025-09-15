

---

# PYSINT - Python OSINT Scanner

PYSINT is a modular, Python-based **OSINT (Open Source Intelligence) scanner** designed for educational purposes and authorized security testing. It combines multiple OSINT techniques to gather information about domains, IPs, websites, and more.

---

## ⚡ Features

PYSINT includes the following modules:

| #  | Module Name                     | Description                                                                 |
|----|---------------------------------|-----------------------------------------------------------------------------|
| 1  | Whois/IP Lookup                 | Retrieves domain registration and IP information.                           |
| 2  | DNS Lookup                       | Queries DNS records (A, MX, NS, TXT, CNAME).                                |
| 3  | HTML Scraper                     | Fetches website HTML content.                                               |
| 4  | Email Extractor                  | Extracts email addresses from HTML pages.                                   |
| 5  | Subdomain Finder                 | Enumerates subdomains of a target domain.                                   |
| 6  | Parameter Scanner                | Tests website URL parameters for responsiveness.                            |
| 7  | Directory / File Scanner         | Searches for directories and files on a target site using wordlists.        |
| 8  | SSL / TLS Info                    | Retrieves SSL/TLS certificate information.                                  |
| 9  | HTTP Headers                      | Displays HTTP headers returned by a website.                                 |
| 10 | Wayback / Archive Lookup          | Checks historical snapshots of a site using Wayback Machine.               |
| 11 | Technology / CMS Detection        | Detects CMS, frameworks, JS libraries, and server info.                     |
| 12 | Port / Service Scanner            | Scans common open ports and identifies associated services.                 |
| 13 | Master OSINT Scanner              | Integrates all modules in a single CLI menu for easy use.                  |

---

## 📦 Installation

1. Clone the repository:

```bash
git clone https://github.com/YourUsername/PYSINT.git
cd PYSINT

2. Install dependencies:



pip install -r requirements.txt


---

🛠 Usage

Run the Master OSINT Scanner to access all modules:

python master-osint.py

Follow the menu prompts to run individual modules.

Alternatively, run any module directly:

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


---

⚠️ Disclaimer

This tool is intended for educational purposes and authorized testing only.

The author is not responsible for any misuse of this software. Use responsibly and only on systems you have permission to test. Unauthorized scanning or attacks may be illegal.


---

💡 Contributing

Contributions are welcome! You can:

Add new OSINT modules

Improve scanning efficiency

Expand wordlists or parameter lists

Improve documentation


Please open an issue or submit a pull request.


---

📜 License

This project is licensed under the MIT License. See the LICENSE file for details.


---

📌 Notes

Compatible with Python 3.10+

Tested on Linux, Termux, and Windows (with minor adjustments)

Wordlists are located in the wordlists/ directory

Use responsibly and ethically
=======
# PYSINT
an OSINT Framework made in python 
>>>>>>> 9238042bdb75d7f27a6d19b648df1294335a486d
