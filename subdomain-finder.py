#!/usr/bin/env python3
"""
subdomain-finder.py - Subdomain Discovery Tool for PYSINT Suite
Author: YourNameHere
License: MIT
Repository: ~/PYSINT

Features:
- Discover subdomains via crt.sh (Certificate Transparency logs)
- Fallback to HTML parsing if JSON fails
- Verify active subdomains via HTTP/HTTPS requests
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--domain, --limit, etc.) + Interactive fallback
- Debug mode (--debug) to log API requests and responses
- Help (--help) via argparse (native)
"""

import requests
import httpx
import re
import json
import csv
import os
import time
import argparse
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.text import Text

# ================== DEFAULTS ==================
DEFAULT_LIMIT = 50
DEFAULT_TIMEOUT = 10.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
def get_subdomains_crtsh(domain: str, limit: int, debug: bool = False):
    """Get subdomains from crt.sh using Certificate Transparency logs"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    # First attempt: JSON API
    url_json = f"https://crt.sh/?q=%25.{domain}&output=json"
    if debug:
        console.print(f"[DEBUG] Trying JSON API: {url_json}")

    try:
        resp = requests.get(url_json, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        
        if debug:
            console.print(f"[DEBUG] JSON API Status: {resp.status_code}")

        data = resp.json()
        subdomains = set()
        
        for entry in data:
            if isinstance(entry, dict) and 'name_value' in entry:
                names = entry['name_value'].split("\n")
                for name in names:
                    name = name.strip().lower()
                    if domain.lower() in name and '*' not in name:
                        # Clean and validate subdomain
                        if name.endswith(f".{domain.lower()}") or name == domain.lower():
                            subdomains.add(name)

        result_list = list(subdomains)[:limit] if limit > 0 else list(subdomains)
        if debug:
            console.print(f"[DEBUG] Found {len(result_list)} subdomains via JSON API")
        return result_list

    except Exception as e:
        if debug:
            console.print(f"[DEBUG] JSON API failed: {e}")
        console.print("[yellow]JSON fetch failed, trying HTML parsing...[/yellow]")

    # Fallback: HTML parsing
    url_html = f"https://crt.sh/?q=%25.{domain}"
    if debug:
        console.print(f"[DEBUG] Trying HTML parsing: {url_html}")

    try:
        resp = requests.get(url_html, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        
        if debug:
            console.print(f"[DEBUG] HTML page Status: {resp.status_code}")

        # Improved regex pattern
        pattern = rf"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{{0,61}}[a-zA-Z0-9])?\.)+{re.escape(domain)}"
        subdomains = set(re.findall(pattern, resp.text, re.IGNORECASE))
        
        # Filter and clean results
        cleaned_subdomains = set()
        for sub in subdomains:
            sub = sub.lower().strip()
            if sub.endswith(f".{domain.lower()}") or sub == domain.lower():
                cleaned_subdomains.add(sub)

        result_list = list(cleaned_subdomains)[:limit] if limit > 0 else list(cleaned_subdomains)
        if debug:
            console.print(f"[DEBUG] Found {len(result_list)} subdomains via HTML parsing")
        return result_list

    except Exception as e:
        if debug:
            console.print(f"[DEBUG] HTML parsing failed: {e}")
        console.print(f"[red]HTML fetch failed: {e}[/red]")
        return []


async def check_subdomain_status(client: httpx.AsyncClient, subdomain: str, debug: bool = False):
    """Check if a subdomain is active via HTTP/HTTPS"""
    protocols = ["https", "http"]
    
    for protocol in protocols:
        url = f"{protocol}://{subdomain}"
        try:
            if debug:
                console.print(f"[DEBUG] Checking {url}...")
                
            response = await client.get(url, timeout=5.0)
            status_code = response.status_code
            
            if debug:
                console.print(f"[DEBUG] {url} responded with {status_code}")
            
            if status_code < 400:
                return {
                    "subdomain": subdomain,
                    "url": url,
                    "status_code": status_code,
                    "status": "active",
                    "protocol": protocol,
                    "error": None
                }
            else:
                if debug:
                    console.print(f"[DEBUG] {url} returned {status_code} - not active")
                    
        except httpx.RequestError as e:
            if debug:
                console.print(f"[DEBUG] Request error for {url}: {e}")
            continue
        except Exception as e:
            if debug:
                console.print(f"[DEBUG] Unexpected error for {url}: {e}")
            continue
    
    # If both protocols failed
    return {
        "subdomain": subdomain,
        "url": None,
        "status_code": None,
        "status": "inactive",
        "protocol": None,
        "error": "All connection attempts failed"
    }


async def check_subdomains(subdomains: list, debug: bool):
    """Check which subdomains are active"""
    active = []
    results = []

    async with httpx.AsyncClient(follow_redirects=True, timeout=5.0) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} subdomains"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Checking subdomains...", total=len(subdomains))

            # Create tasks
            tasks = []
            for sub in subdomains:
                task_coro = check_subdomain_status(client, sub, debug)
                tasks.append(task_coro)

            # Process results
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                if result["status"] == "active":
                    active.append(result)
                progress.advance(task)

    return active, results


# ================== MAIN SCAN FUNCTION ==================
def find_and_check_subdomains(domain: str, limit: int, debug: bool):
    """Find and check subdomains for a domain"""
    # Get subdomains
    console.print(f"\n[bold yellow]🔍 Fetching up to {limit if limit > 0 else 'unlimited'} subdomains for [bold cyan]{domain}[/bold cyan]...[/bold yellow]\n")
    subdomains = get_subdomains_crtsh(domain, limit, debug)

    if not subdomains:
        console.print("[red]No subdomains found[/red]")
        return [], []

    console.print(f"[bold green]✅ Found {len(subdomains)} subdomains[/bold green]")

    # Check active subdomains
    console.print(f"\n[bold yellow]🔍 Checking which of the {len(subdomains)} subdomains are active...[/bold yellow]\n")
    active_subs, all_results = asyncio.run(check_subdomains(subdomains, debug))

    return active_subs, all_results


# ================== UTILS ==================
def display_results(active_subs: list, all_results: list, domain: str):
    """Display results in rich table"""
    if all_results:
        table = Table(title=f"Subdomain Status for {domain}", header_style="bold magenta", show_lines=True)
        table.add_column("Subdomain", style="cyan", no_wrap=False)
        table.add_column("Status", style="yellow")
        table.add_column("Protocol", style="blue")
        table.add_column("HTTP Code", style="green")
        table.add_column("URL", style="magenta")

        for result in all_results:
            subdomain = result["subdomain"]
            status = result["status"]
            protocol = result["protocol"] or "-"
            status_code = str(result["status_code"]) if result["status_code"] else "-"
            url = result["url"] or "-"

            if status == "active":
                status_text = Text("ACTIVE", style="bold green")
            else:
                status_text = Text("INACTIVE", style="red")

            table.add_row(subdomain, status_text, protocol, status_code, url)

        console.print(table)
        console.print(f"\n[bold green]✅ Found [bold yellow]{len(active_subs)}[/bold yellow] active subdomains out of {len(all_results)} total.[/bold green]")
    else:
        console.print("[yellow]No subdomain status results to display.[/yellow]")


def save_results(results: list, domain: str, prefix: str = "subdomain_scan", results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save results as JSON and CSV with timestamp"""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_domain = domain.replace('.', '_')
    json_path = results_dir / f"{prefix}_{safe_domain}_{ts}.json"
    csv_path = results_dir / f"{prefix}_{safe_domain}_{ts}.csv"

    # Save JSON
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"[red]Failed to save JSON results: {e}[/red]")
        json_path = None

    # Save CSV
    if results:
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                fieldnames = ["subdomain", "url", "status_code", "status", "protocol", "error"]
                writer = csv.DictWriter(cf, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    writer.writerow({
                        "subdomain": r.get("subdomain", ""),
                        "url": r.get("url", ""),
                        "status_code": r.get("status_code", ""),
                        "status": r.get("status", ""),
                        "protocol": r.get("protocol", ""),
                        "error": r.get("error", "")
                    })
        except Exception as e:
            console.print(f"[red]Failed to save CSV results: {e}[/red]")
            csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Subdomain Finder — Discover Subdomains via Certificate Transparency",
        epilog="Example: python3 subdomain-finder.py --domain example.com --limit 100 --debug"
    )
    parser.add_argument("--domain", "-d", action="append", help="Domain(s) to search for subdomains (can be used multiple times)")
    parser.add_argument("--file", "-f", help="File containing domains (one per line)")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Maximum number of subdomains to check (0 = unlimited, default: {DEFAULT_LIMIT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows API requests and responses)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT Subdomain Finder[/bold green]")

    # If no domain provided, fallback to interactive mode
    if not args.domain and not args.file:
        domain = Prompt.ask("[bold cyan]Enter the domain to search for subdomains")
        if not domain:
            console.print("[red]No domain provided. Exiting.[/red]")
            return

        limit_input = Prompt.ask(f"[bold cyan]Maximum number of subdomains to check (0 = unlimited, default: {DEFAULT_LIMIT})", default=str(DEFAULT_LIMIT))
        limit = int(limit_input) if limit_input.isdigit() else DEFAULT_LIMIT
        debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)

        domains = [domain.strip()]
    else:
        # CLI mode
        debug = args.debug
        limit = args.limit
        domains = []

        if args.domain:
            domains.extend([d.strip() for d in args.domain])

        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    file_domains = [line.strip() for line in f if line.strip()]
                    domains.extend(file_domains)
                    console.print(f"[cyan]Loaded {len(file_domains)} domains from {args.file}[/cyan]")
            except Exception as e:
                console.print(f"[red]Error reading domains file: {e}[/red]")
                return

        if not domains:
            console.print("[red]No domains provided. Exiting.[/red]")
            return

    # Process each domain
    for domain in domains:
        console.print(f"\n[bold blue]=== Processing domain: {domain} ===[/bold blue]")
        start_time = time.time()
        active_subs, all_results = find_and_check_subdomains(domain, limit, debug)
        duration = time.time() - start_time

        # Display results
        display_results(active_subs, all_results, domain)
        console.print(f"\n[bold green]✅ Scan for {domain} finished in {duration:.1f}s.[/bold green]")

        # Save results
        json_path, csv_path = save_results(all_results, domain)
        saved = []
        if json_path:
            saved.append(str(json_path))
        if csv_path:
            saved.append(str(csv_path))
        if saved:
            console.print(f"[green]💾 Results saved to:[/green] {', '.join(saved)}")
        else:
            console.print("[yellow]⚠️  No results were saved (I/O error).[/yellow]")
        console.print("")  # Empty line for spacing


if __name__ == "__main__":
    try:
        import asyncio
        main()
    except KeyboardInterrupt:
        console.print("\n[red]🛑 Scan interrupted by user.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
