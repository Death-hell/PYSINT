#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 PYSINT ULTIMATE PRO v5.0 — EMAIL & PHONE OSINT (WITH & WITHOUT API)
The most advanced, beautiful, and complete OSINT tool in a single file.
Supports interactive mode, CLI flags, custom API keys, batch mode, and international targets.
Saves all results to ~/PyToolKit/PYSINT/results/
Ethical use only. Works on Termux/Windows/Linux/macOS.
"""

import os
import sys
import json
import hashlib
import asyncio
import aiohttp
import random
import time
import re
import phonenumbers
import argparse
from urllib.parse import quote, urlparse
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm_asyncio
from dotenv import load_dotenv

# ======================
# RICH UI SETUP
# ======================

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, MofNCompleteColumn
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
    from rich.text import Text
    from rich.columns import Columns
    from rich.prompt import Prompt, Confirm
    from rich.tree import Tree
    from rich.markdown import Markdown
except ImportError:
    print("❌ 'rich' not installed. Run: pip install rich aiohttp beautifulsoup4 phonenumbers python-dotenv tqdm")
    sys.exit(1)

console = Console(record=True)

# ======================
# CONFIG & PATHS
# ======================

BASE_DIR = Path.home() / "PyToolKit" / "PYSINT" / "results"
BASE_DIR.mkdir(parents=True, exist_ok=True)

# Load .env for API keys (optional)
load_dotenv()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 14; Mobile; rv:127.0) Gecko/127.0 Firefox/127.0",
]

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

DISCLAIMER = """
⚠️  DISCLAIMER:
This tool is for educational and defensive security purposes only.
Use only on data you own or have explicit permission to investigate.
Do not use for harassment, spam, or illegal reconnaissance.
Violators will be haunted by RFC 2324 (Teapot Protocol).
"""

# ======================
# CORE UTILS
# ======================

def get_random_headers():
    headers = HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    return headers

def hash_input(target: str) -> str:
    return hashlib.sha256(target.strip().lower().encode()).hexdigest()[:16]

def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name)

def is_email(target: str) -> bool:
    pattern = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    return re.match(pattern, target.strip()) is not None

def normalize_phone(phone: str) -> str:
    cleaned = re.sub(r'[^\d+]', '', phone.strip())
    if not cleaned.startswith('+') and len(cleaned) >= 10:
        return '+' + cleaned
    return cleaned

def is_phone(target: str) -> bool:
    try:
        normalized = normalize_phone(target)
        parsed = phonenumbers.parse(normalized, None)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False

def get_phone_info(phone: str):
    try:
        normalized = normalize_phone(phone)
        parsed = phonenumbers.parse(normalized, None)
        country = phonenumbers.region_code_for_number(parsed)
        carrier = "Unknown"
        location = "Unknown"
        number_type = phonenumbers.number_type(parsed)
        type_str = ["FIXED_LINE", "MOBILE", "FIXED_LINE_OR_MOBILE", "TOLL_FREE", "PREMIUM_RATE", "SHARED_COST", "VOIP", "PERSONAL_NUMBER", "PAGER", "UAN", "UNKNOWN"][min(number_type, 10)]

        if country == "BR":
            prefix = str(parsed.national_number)[:2]
            carriers = {"11": "Vivo", "12": "Vivo", "13": "Vivo", "14": "Vivo", "15": "Vivo", "16": "Vivo", "17": "Vivo", "18": "Vivo", "19": "Vivo",
                        "21": "Claro", "22": "Claro", "24": "Claro", "27": "Claro", "28": "Claro",
                        "31": "TIM", "32": "TIM", "33": "TIM", "34": "TIM", "35": "TIM", "37": "TIM", "38": "TIM",
                        "41": "Algar Telecom", "42": "Algar Telecom", "43": "Algar Telecom", "44": "Algar Telecom", "45": "Algar Telecom", "46": "Algar Telecom",
                        "51": "Oi", "53": "Oi", "54": "Oi", "55": "Oi",
                        "61": "Claro", "62": "Claro", "63": "Oi", "64": "Claro", "65": "Claro", "66": "Claro", "67": "Oi", "68": "Claro", "69": "Vivo",
                        "71": "Claro", "73": "Claro", "74": "Claro", "75": "Claro", "77": "Claro", "79": "Claro",
                        "81": "Claro", "82": "Claro", "83": "Claro", "84": "Claro", "85": "Claro", "86": "Claro", "87": "Claro", "88": "Claro", "89": "Claro",
                        "91": "Vivo", "92": "Vivo", "93": "Vivo", "94": "Vivo", "95": "Vivo", "96": "Vivo", "97": "Vivo", "98": "Vivo", "99": "Vivo"}
            carrier = carriers.get(prefix, "Unknown BR Carrier")
            location = f"DDD {prefix} region"
        elif country == "US":
            carrier = "US Carrier (simulated)"
            location = "US Region (simulated)"

        return {
            "country": country or "Unknown",
            "carrier": carrier,
            "location": location,
            "type": type_str,
            "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
            "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        }
    except Exception as e:
        return {"error": str(e)}

# ======================
# API MODULES (OPTIONAL)
# ======================

async def check_hibp_api(email: str, api_key: str, session):
    """Check Have I Been Pwned with API key."""
    if not api_key:
        return None
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote(email)}"
    headers = {
        "User-Agent": "PYSINT-PRO",
        "hibp-api-key": api_key
    }
    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 404:
                return []
            else:
                return {"error": f"HIBP HTTP {resp.status}"}
    except Exception as e:
        return {"error": f"HIBP Exception: {str(e)}"}

async def check_dehashed_api(email_or_phone: str, api_key: str, session):
    """Simulate Dehashed API check (requires username:api_key)."""
    if not api_key or ":" not in api_key:
        return None
    # Dehashed API structure: https://api.dehashed.com/search?query=email_or_phone
    # Requires Basic Auth: username:api_key
    url = f"https://api.dehashed.com/search?query={quote(email_or_phone)}"
    try:
        auth = aiohttp.BasicAuth(api_key.split(":")[0], api_key.split(":")[1])
        async with session.get(url, auth=auth, timeout=15) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("entries", [])
            else:
                return {"error": f"Dehashed HTTP {resp.status}"}
    except Exception as e:
        return {"error": f"Dehashed Exception: {str(e)}"}

# ======================
# SCRAPING MODULES (NO API)
# ======================

async def fetch_text(session, url: str, retries=3, delay=1):
    for attempt in range(retries):
        try:
            headers = get_random_headers()
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:
                    await asyncio.sleep(delay * 3)
                elif response.status in [500, 502, 503, 504]:
                    await asyncio.sleep(delay * 2)
                else:
                    return None
        except asyncio.TimeoutError:
            if attempt == retries - 1:
                return None
            await asyncio.sleep(delay)
        except Exception as e:
            if attempt == retries - 1:
                return None
            await asyncio.sleep(delay)
    return None

async def scrape_pastebin(target: str, session):
    results = []
    try:
        query = quote(target)
        url = f"https://psbdmp.ws/search/{query}"
        text = await fetch_text(session, url)
        if not text:
            return results
        soup = BeautifulSoup(text, "html.parser")
        for link in soup.find_all("a", href=True):
            if "/dump/" in link["href"]:
                full_url = "https://psbdmp.ws" + link["href"]
                snippet = f"Paste containing '{target[:20]}...'"
                results.append({"source": "psbdmp.ws", "url": full_url, "snippet": snippet})
                if len(results) >= 5: break
        await asyncio.sleep(random.uniform(0.5, 1.2))
    except Exception as e:
        return [{"error": str(e)}]
    return results

async def scrape_github(target: str, session):
    results = []
    try:
        query_code = quote(f'"{target}"')
        url_code = f"https://github.com/search?q={query_code}&type=code"
        text_code = await fetch_text(session, url_code)
        if text_code:
            soup = BeautifulSoup(text_code, "html.parser")
            for a in soup.find_all("a", href=True):
                if "/blob/" in a["href"] and not a["href"].endswith("wiki"):
                    full_url = "https://github.com" + a["href"]
                    results.append({"source": "GitHub Code", "url": full_url, "snippet": "Code file containing target"})
                    if len(results) >= 3: break

        await asyncio.sleep(random.uniform(0.8, 1.5))

        username = target.split("@")[0] if is_email(target) else re.sub(r'\D', '', target)[-8:]
        url_profile = f"https://github.com/{username}"
        text_profile = await fetch_text(session, url_profile)
        if text_profile and "<title>Page not found" not in text_profile and "Join GitHub" not in text_profile:
            results.append({"source": "GitHub Profile", "url": url_profile, "snippet": f"User profile: {username}"})

    except Exception as e:
        return [{"error": str(e)}]
    return results

async def scrape_duckduckgo(target: str, session):
    results = []
    try:
        query = quote(f'"{target}" (site:linkedin.com OR site:twitter.com OR site:instagram.com OR site:facebook.com OR site:t.me OR "whatsapp") -inurl:job -inurl:careers')
        url = f"https://lite.duckduckgo.com/lite?q={query}"
        text = await fetch_text(session, url)
        if not text:
            return results
        soup = BeautifulSoup(text, "html.parser")
        for result in soup.find_all("a", href=True):
            href = result["href"]
            if href.startswith("http") and "duckduckgo.com" not in href and "ad_provider" not in href:
                title = result.get_text().strip()
                if len(title) > 10:
                    snippet = f"{title[:80]}..." if len(title) > 80 else title
                    results.append({"source": "DuckDuckGo", "url": href, "snippet": snippet})
                    if len(results) >= 10: break
        await asyncio.sleep(random.uniform(1, 2.5))
    except Exception as e:
        return [{"error": str(e)}]
    return results

async def scrape_truecaller_simulated(phone: str, session):
    results = []
    try:
        queries = [
            f'"{phone}" "name" OR "contato" site:facebook.com OR site:linkedin.com',
            f'"{phone}" "whatsapp" OR "telegram" OR "signal" site:.br OR site:.com',
        ]
        for q in queries:
            encoded = quote(q)
            url = f"https://lite.duckduckgo.com/lite?q={encoded}"
            text = await fetch_text(session, url)
            if text:
                soup = BeautifulSoup(text, "html.parser")
                for result in soup.find_all("a", href=True):
                    href = result["href"]
                    if href.startswith("http") and "duckduckgo" not in href:
                        title = result.get_text().strip()
                        if len(title) > 10 and any(kw in title.lower() for kw in ["name", "contato", "whatsapp", "telegram", "signal", phone[-4:]]):
                            snippet = f"Possible owner: {title[:70]}..."
                            results.append({"source": "TrueCaller (sim)", "url": href, "snippet": snippet})
                            if len(results) >= 4: break
            await asyncio.sleep(random.uniform(0.7, 1.8))
    except Exception as e:
        return [{"error": str(e)}]
    return results

async def scrape_telegram(phone: str, session):
    results = []
    try:
        query = quote(f'"{phone}" site:t.me')
        url = f"https://lite.duckduckgo.com/lite?q={query}"
        text = await fetch_text(session, url)
        if text:
            soup = BeautifulSoup(text, "html.parser")
            for result in soup.find_all("a", href=True):
                href = result["href"]
                if "t.me" in href and "/s/" not in href and "join" not in href:
                    title = result.get_text().strip()
                    if len(title) > 5:
                        results.append({"source": "Telegram (public)", "url": href, "snippet": f"Public group/channel: {title[:60]}..."})
                        if len(results) >= 3: break
        await asyncio.sleep(random.uniform(0.6, 1.5))
    except Exception as e:
        return [{"error": str(e)}]
    return results

# ======================
# ORCHESTRATOR
# ======================

async def run_scan(target: str, target_type: str, use_api: bool, hibp_key: str = None, dehashed_key: str = None):
    modules = {}
    results = {}

    connector = aiohttp.TCPConnector(limit=20, ssl=False, ttl_dns_cache=300)
    timeout = aiohttp.ClientTimeout(total=30, connect=10)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # API MODULES (if enabled)
        if use_api:
            if target_type == "email" and hibp_key:
                modules["hibp_breaches"] = lambda: check_hibp_api(target, hibp_key, session)
            if dehashed_key:
                modules["dehashed"] = lambda: check_dehashed_api(target, dehashed_key, session)

        # SCRAPING MODULES (always)
        if target_type == "email":
            modules.update({
                "pastebin": lambda: scrape_pastebin(target, session),
                "github": lambda: scrape_github(target, session),
                "social_media": lambda: scrape_duckduckgo(target, session),
            })
        else:  # phone
            modules.update({
                "truecaller_sim": lambda: scrape_truecaller_simulated(target, session),
                "telegram": lambda: scrape_telegram(target, session),
                "general_search": lambda: scrape_duckduckgo(target, session),
            })

        # Run all modules
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False
        ) as progress:
            task = progress.add_task("🚀 Executing OSINT modules...", total=len(modules))

            for name, coro_func in modules.items():
                progress.update(task, description=f"🔍 {name.replace('_', ' ').title()}")
                try:
                    results[name] = await asyncio.wait_for(coro_func(), timeout=40)
                except asyncio.TimeoutError:
                    results[name] = [{"error": "Timeout"}]
                except Exception as e:
                    results[name] = [{"error": f"Exception: {str(e)}"}]
                progress.advance(task)
                await asyncio.sleep(random.uniform(0.1, 0.5))

    return results

def save_results(target: str, results: dict, target_type: str, phone_info=None, output_dir: Path = None):
    if output_dir is None:
        output_dir = BASE_DIR / hash_input(target)
    output_dir.mkdir(exist_ok=True)

    metadata = {
        "target": target,
        "type": target_type,
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "tool": "PYSINT ULTIMATE PRO v5.0",
        "sources": list(results.keys()),
        "total_findings": sum(len(v) if isinstance(v, list) and not (len(v) == 1 and "error" in v[0]) else 0 for v in results.values()),
        "used_api": any("error" not in (v[0] if isinstance(v, list) and len(v) > 0 else {}) for k, v in results.items() if "hibp" in k or "dehashed" in k),
    }

    if phone_info and "error" not in phone_info:
        metadata["phone_info"] = phone_info

    with open(output_dir / "METADATA.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    for source, data in results.items():
        filename = sanitize_filename(source.upper()) + ".json"
        with open(output_dir / filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    report_path = generate_report(target, results, output_dir, target_type, phone_info)
    return output_dir, report_path

def generate_report(target: str, results: dict, output_dir: Path, target_type: str, phone_info=None):
    lines = [
        "# 🔐 PYSINT ULTIMATE PRO v5.0 — DEFINITIVE OSINT REPORT",
        "==========================================================",
        f"🎯 TARGET: `{target}`",
        f"📌 TYPE: **{target_type.upper()}**",
        f"📅 SCANNED: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"📂 OUTPUT: `{output_dir}`",
        "==========================================================",
        ""
    ]

    if phone_info and "error" not in phone_info:
        lines.extend([
            "## 📱 PHONE DETAILS",
            f"- **Country**: {phone_info.get('country', 'N/A')}",
            f"- **Carrier**: {phone_info.get('carrier', 'N/A')}",
            f"- **Location**: {phone_info.get('location', 'N/A')}",
            f"- **Type**: {phone_info.get('type', 'N/A')}",
            f"- **E.164**: `{phone_info.get('e164', 'N/A')}`",
            f"- **National**: `{phone_info.get('national', 'N/A')}`",
            ""
        ])

    for source, data in results.items():
        lines.append(f"## 🔍 SOURCE: {source.replace('_', ' ').title()}")
        lines.append("")

        if isinstance(data, list):
            if len(data) == 0:
                lines.append("✅ No findings.")
            else:
                for item in data:
                    if isinstance(item, dict):
                        if "error" in item:
                            lines.append(f"❌ **Error**: {item['error']}")
                        else:
                            url = item.get("url", "N/A")
                            snippet = item.get("snippet", "No snippet")
                            lines.append(f"- **{snippet}**")
                            lines.append(f"  → {url}")
                    else:
                        lines.append(f"- {item}")
        else:
            lines.append(f"⚠️ Unexpected result: {data}")

        lines.append("")

    report_path = output_dir / "REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    console.print(f"\n📄 [bold green]FULL REPORT SAVED TO:[/bold green] [cyan]{report_path}[/cyan]")
    return report_path

async def scan_single_target(target: str, use_api: bool, hibp_key: str = None, dehashed_key: str = None, output_dir: Path = None):
    if is_email(target):
        target_type = "email"
        phone_info = None
    elif is_phone(target):
        target = normalize_phone(target)
        target_type = "phone"
        phone_info = get_phone_info(target)
    else:
        console.print(f"[red]❌ Invalid target: {target}[/red]")
        return None, None

    start_time = time.time()
    results = await run_scan(target, target_type, use_api, hibp_key, dehashed_key)
    output_dir, report_path = save_results(target, results, target_type, phone_info, output_dir)

    # Build summary table
    table = Table(title=f"✅ SCAN RESULTS FOR: {target}", box=box.ROUNDED, style="green", header_style="bold cyan")
    table.add_column("SOURCE", style="bold", no_wrap=True)
    table.add_column("STATUS", style="yellow", justify="center")
    table.add_column("FINDINGS", style="bold magenta", justify="right")

    total_findings = 0
    for source, data in results.items():
        if isinstance(data, list):
            errors = [item for item in data if isinstance(item, dict) and "error" in item]
            success = len(data) - len(errors)
            if success > 0:
                status = "✅"
                count = str(success)
                total_findings += success
            elif len(errors) > 0:
                status = "❌"
                count = "Error"
            else:
                status = "🟢"
                count = "0"
        else:
            status = "⚠️"
            count = "?"

        table.add_row(source.replace("_", " ").title(), status, count)

    console.print("\n", table)
    console.print(f"⏱️  Scan completed in {time.time() - start_time:.1f} seconds.")

    return output_dir, results

async def batch_scan(targets_file: str, use_api: bool, hibp_key: str = None, dehashed_key: str = None):
    if not os.path.exists(targets_file):
        console.print(f"[red]❌ File not found: {targets_file}[/red]")
        return

    with open(targets_file, 'r', encoding='utf-8') as f:
        targets = [line.strip() for line in f if line.strip()]

    console.print(f"[bold blue]🚀 Starting batch scan of {len(targets)} targets...[/bold blue]")

    for i, target in enumerate(targets, 1):
        console.print(f"\n[bold]🔎 TARGET {i}/{len(targets)}: {target}[/bold]")
        await scan_single_target(target, use_api, hibp_key, dehashed_key)

    console.print(f"\n[bold green]🎉 BATCH SCAN COMPLETE FOR {len(targets)} TARGETS.[/bold green]")

async def interactive_mode():
    console.print(Panel.fit(
        "[bold blue]🔐 PYSINT ULTIMATE PRO v5.0 — INTERACTIVE MODE[/bold blue]\n"
        "[dim]Email & Phone OSINT • With/Without API • International Support[/dim]",
        border_style="blue", padding=(1, 2)
    ))
    console.print(DISCLAIMER)

    use_api = Confirm.ask("🔑 Do you want to use API keys? (HIBP, Dehashed)", default=False)
    hibp_key = None
    dehashed_key = None

    if use_api:
        hibp_key = Prompt.ask("🔐 Enter your HIBP API key (optional)", default="").strip() or None
        dehashed_key = Prompt.ask("🔐 Enter your Dehashed API key (username:api_key, optional)", default="").strip() or None

    while True:
        target = Prompt.ask("\n[bold green]➡️  Enter target (email or phone) or 'quit' to exit[/bold green]").strip()
        if target.lower() in ['quit', 'exit', 'q']:
            break
        if not target:
            continue

        await scan_single_target(target, use_api, hibp_key, dehashed_key)

    console.print("\n[bold green]👋 Thank you for using PYSINT ULTIMATE PRO![/bold green]")

def main():
    parser = argparse.ArgumentParser(description="PYSINT ULTIMATE PRO — Email & Phone OSINT Tool")
    parser.add_argument("--email", "-e", help="Single email target")
    parser.add_argument("--phone", "-p", help="Single phone target")
    parser.add_argument("--batch", "-b", help="File with list of targets (one per line)")
    parser.add_argument("--api-key-hibp", help="HIBP API key")
    parser.add_argument("--api-key-dehashed", help="Dehashed API key (username:api_key)")
    parser.add_argument("--no-api", action="store_true", help="Disable API usage")
    parser.add_argument("--output", "-o", help="Custom output directory")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive mode")

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(interactive_mode())
        return

    use_api = not args.no_api
    hibp_key = args.api_key_hibp or os.getenv("HIBP_API_KEY")
    dehashed_key = args.api_key_dehashed or os.getenv("DEHASHED_API_KEY")

    if args.batch:
        asyncio.run(batch_scan(args.batch, use_api, hibp_key, dehashed_key))
    elif args.email or args.phone:
        target = args.email or args.phone
        output_dir = Path(args.output) if args.output else None
        asyncio.run(scan_single_target(target, use_api, hibp_key, dehashed_key, output_dir))
    else:
        console.print("[yellow]No target provided. Starting interactive mode...[/yellow]")
        asyncio.run(interactive_mode())

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow bold]🛑 INTERRUPTED BY USER. Exiting gracefully...[/yellow bold]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red bold]💥 FATAL ERROR:[/red bold] {e}")
        console.print(Syntax(traceback.format_exc(), "python", theme="monokai", line_numbers=True))
        sys.exit(1)
