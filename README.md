
markdown
# 🧰 PyToolKit — by Death-hell

> 🔥 All-in-one Ethical Hacking & Security Toolkit — CLI-based, lightweight, and powerful.  
> Featuring the **AST-powered JavaScript Vulnerability Scanner** — `jsvulnscan.js` — built for accuracy, not regex.

---

<p align="center">
  <a href="https://github.com/Death-hell/PyToolKit/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Death-hell/PyToolKit?style=for-the-badge&color=blue" alt="License">
  </a>
  <a href="https://github.com/Death-hell/PyToolKit/releases">
    <img src="https://img.shields.io/github/v/release/Death-hell/PyToolKit?style=for-the-badge&color=green" alt="Release">
  </a>
  <a href="https://github.com/Death-hell/PyToolKit/stargazers">
    <img src="https://img.shields.io/github/stars/Death-hell/PyToolKit?style=for-the-badge&color=yellow" alt="Stars">
  </a>
  <a href="https://github.com/Death-hell/PyToolKit/issues">
    <img src="https://img.shields.io/github/issues/Death-hell/PyToolKit?style=for-the-badge&color=orange" alt="Issues">
  </a>
</p>

---

## 🚀 Highlights

✅ **`jsvulnscan.js`** — Interactive AST-based JS vulnerability scanner (eval, XSS, innerHTML, localStorage, etc)  
✅ **25+ Security Tools** — Recon, Scanning, Fuzzing, Analysis — all in CLI  
✅ **Zero Bloat** — Single-file tools, no heavy frameworks  
✅ **Beautiful CLI UX** — Progress spinners, colors, interactive prompts  
✅ **GitHub-Ready** — Perfect for automation, CI/CD, code scanning, PR checks

---

## 🛠️ Tool Inventory

### 🔍 Scanners & Testers
- `SQLi-Scanner.py` — SQL Injection vulnerability scanner
- `XSS-Scanner.py` — Cross-Site Scripting tester
- `LFI-Scanner.py` — Local File Inclusion detector
- `port-scan.py` — TCP port scanner
- `directory-fuzzer.py` — Brute-force hidden paths
- `param-finder.py` — Extract & fuzz URL parameters
- `malware-testScan.py` — Basic malware indicator scanner
- `BufferOverFlow-analyzer.py` — Buffer overflow pattern analyzer
- `Brute-ForceScan.py` — Credential brute-force module

### 🌐 Recon & Enumeration
- `subdomain-finder.py` — Discover subdomains via DNS & wordlists
- `dns-hunter.py` — Advanced DNS reconnaissance
- `tech-detector.py` — Identify web stack (frameworks, servers, etc)
- `wayback-Scan.py` — Fetch historical URLs from Wayback Machine
- `get-html.py` — Fetch and save raw HTML
- `find-email-in-html.py` — Extract emails from HTML source
- `Number_And_Email-Hunter.py` — Hunt emails & phone numbers in text

### 📊 Info & Analysis
- `headers.py` — Analyze HTTP security headers
- `ssl-info.py` — Extract SSL/TLS certificate info
- `analyzer-whois.py` — WHOIS domain lookup
- `geoip-scan.py` — Geolocate IP addresses
- `Traceroute-scan.py` — Trace network path to target
- `PingPong.py` — ICMP ping with latency stats

### 📁 Wordlists & Payloads
- `SQLi-wordlist.txt`
- `XSS-wordlist.txt`
- `LFI-wordlist.txt`
- `directory-wordlist.txt`
- `large-params.txt`
- `jsreq.txt`

### 🧩 Frameworks & Modules
- `DarkSINT` / `darksint.py` — Dark web intelligence module
- `PYSINT` — Python-based OSINT toolkit
- `metasploit-framework.py` — Metasploit-like CLI interface (educational)

### 🧪 Star Tool: `jsvulnscan.js`
```bash
node jsvulnscan.js --interactive
```
- ✅ AST parsing with `@babel/parser`
- ✅ Detects: `eval()`, `document.write`, `innerHTML`, `setTimeout(string)`, `console.log`, sensitive `localStorage`
- ✅ Colorful CLI with `chalk` + interactive with `inquirer`
- ✅ Export-ready for GitHub Actions & Code Scanning

---

## ⚙️ Installation

```bash
git clone https://github.com/Death-hell/PyToolKit.git
cd PyToolKit

# Python tools
pip install -r requirements.txt

# JS scanner
npm install
```

> 💡 Requirements:
> - Python 3.8+
> - Node.js 18+
> - Git

---

## 🎯 Quick Start

```bash
# Scan JS files interactively
node jsvulnscan.js --interactive

# SQLi test
python SQLi-Scanner.py -u "https://target.com/page?id=1"

# Subdomain brute-force
python subdomain-finder.py -d target.com

# Port scan
python port-scan.py -t 192.168.1.1 -p 22,80,443

# Extract emails from site
python find-email-in-html.py -u https://target.com
```

---

## 📜 License

MIT License — See [LICENSE](LICENSE)

---

## 🤝 Contribute

1. Fork it  
2. Create your feature branch: `git checkout -b feature/your-feature`  
3. Commit: `git commit -m 'feat: add your feature'`  
4. Push: `git push origin feature/your-feature`  
5. Open a Pull Request 🚀

---

## 📬 Contact

**Death-hell** — Ethical Hacker & Security Toolsmith  
📧 Email: [deathiswatchingyou937@gmail.com](mailto:deathiswatchingyou937@gmail.com)  
🐙 GitHub: [@Death-hell](https://github.com/Death-hell)

> “Security is a process, not a product.” — Bruce Schneier

---

> ⚠️ **Legal Notice**:  
> This toolkit is for **educational purposes and authorized security testing only**.  
> Do not use against systems you do not own or have explicit written permission to test.  
> The author is not responsible for misuse.

```

---