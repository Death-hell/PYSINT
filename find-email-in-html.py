#!/usr/bin/env python3
"""
find-email-in-html.py - Email Extractor from Web Pages for PYSINT Suite
Author: Mael
License: MIT
Repository: ~/PyToolKit

Features:
- Extract emails from HTML content using regex
- Supports multiple URLs
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--url, --file, etc.) + Interactive fallback
- Debug mode (--debug) to show raw HTML snippets and regex matches
- Help (--help) via argparse (native)
"""

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
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# ================== DEFAULTS ==================
DEFAULT_TIMEOUT = 10.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Email regex pattern
EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

console = Console()


# ================== CORE FUNCTION ==================
def extract_emails_from_html(html: str, debug: bool = False):
    """Extract unique emails from HTML content"""
    matches = re.findall(EMAIL_PATTERN, html)
    unique_emails = sorted(set(matches))

    if debug and matches:
        console.print(f"[DEBUG] Found {len(matches)} raw matches, {len(unique_emails)} unique emails")
        if len(matches) > 10:
            console.print(f"[DEBUG] Sample matches: {matches[:5]} ... {matches[-5:]}")
        else:
            console.print(f"[DEBUG] All matches: {matches}")

    return unique_emails


async def fetch_and_extract_emails(
    client: httpx.AsyncClient,
    url: str,
    debug: bool = False
):
    """Fetch URL and extract emails"""
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        if debug:
            console.print(f"[DEBUG] Fetching: {url}")

        response = await client.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()

        if debug:
            console.print(f"[DEBUG] Status: {response.status_code} | Content-Type: {response.headers.get('content-type', 'N/A')} | Length: {len(response.text)}")

        emails = extract_emails_from_html(response.text, debug)
        return {
            "url": url,
            "status_code": response.status_code,
            "emails": emails,
            "count": len(emails),
            "error": None
        }

    except httpx.RequestError as e:
        if debug:
            console.print(f"[DEBUG] Request error for {url}: {e}")
        return {
            "url": url,
            "status_code": None,
            "emails": [],
            "count": 0,
            "error": f"RequestError: {e}"
        }
    except httpx.HTTPStatusError as e:
        if debug:
            console.print(f"[DEBUG] HTTP error for {url}: {e}")
        return {
            "url": url,
            "status_code": e.response.status_code if e.response else None,
            "emails": [],
            "count": 0,
            "error": f"HTTPStatusError: {e}"
        }
    except Exception as e:
        if debug:
            console.print(f"[DEBUG] Unexpected error for {url}: {e}")
        return {
            "url": url,
            "status_code": None,
            "emails": [],
            "count": 0,
            "error": f"{type(e).__name__}: {e}"
        }


# ================== MAIN SCAN FUNCTION ==================
async def scan_urls(urls: list, debug: bool):
    """Scan multiple URLs for emails"""
    results = []

    async with httpx.AsyncClient(follow_redirects=True, timeout=DEFAULT_TIMEOUT) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Scanning URLs...", total=len(urls))

            for url in urls:
                progress.update(task, description=f"[cyan]Scanning {url}...")
                result = await fetch_and_extract_emails(client, url, debug)
                results.append(result)
                progress.advance(task)

    return results


# ================== UTILS ==================
def display_results(results: list):
    """Display results in rich tables and panels"""
    total_emails = 0

    for result in results:
        url = result["url"]
        emails = result["emails"]
        error = result["error"]

        if error:
            console.print(Panel(f"❌ Error accessing [bold]{url}[/bold]: {error}", style="red"))
        elif emails:
            table = Table(title=f"📧 Emails found on {url} ({result['count']} total)", show_lines=True)
            table.add_column("Email Address", style="cyan", no_wrap=False)
            for email in emails:
                table.add_row(email)
            console.print(table)
            total_emails += len(emails)
        else:
            console.print(Panel(f"✅ No emails found on [bold]{url}[/bold].", style="yellow"))

    return total_emails


def save_results(results: list, prefix: str = "emails", results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save results as JSON and CSV with timestamp"""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = results_dir / f"{prefix}_{ts}.json"
    csv_path = results_dir / f"{prefix}_{ts}.csv"

    # Save JSON
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"[red]Failed to save JSON results: {e}[/red]")
        json_path = None

    # Save CSV
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            fieldnames = ["url", "status_code", "email", "error"]
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                if result["emails"]:
                    for email in result["emails"]:
                        writer.writerow({
                            "url": result["url"],
                            "status_code": result["status_code"],
                            "email": email,
                            "error": ""
                        })
                else:
                    writer.writerow({
                        "url": result["url"],
                        "status_code": result["status_code"],
                        "email": "",
                        "error": result["error"] or "No emails found"
                    })
    except Exception as e:
        console.print(f"[red]Failed to save CSV results: {e}[/red]")
        csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Email Extractor — Find Emails in Web Pages",
        epilog="Examples:\n"
               "  python3 find-email-in-html.py --url https://example.com\n"
               "  python3 find-email-in-html.py --url https://site1.com --url https://site2.com --debug"
    )
    parser.add_argument("--url", "-u", action="append", help="URL(s) to scan for emails (can be used multiple times)")
    parser.add_argument("--file", "-f", help="File containing URLs (one per line)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows HTML snippets and regex matches)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT Email Extractor[/bold green]")

    # If no URL provided, fallback to interactive mode
    if not args.url and not args.file:
        url = Prompt.ask("[bold cyan]Enter the URL of the website to search for emails")
        if not url:
            console.print("[red]No URL provided. Exiting.[/red]")
            return
        urls = [url.strip()]
        debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)
    else:
        # CLI mode
        debug = args.debug
        urls = []

        if args.url:
            urls.extend([u.strip() for u in args.url])

        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    file_urls = [line.strip() for line in f if line.strip()]
                    urls.extend(file_urls)
                    console.print(f"[cyan]Loaded {len(file_urls)} URLs from {args.file}[/cyan]")
            except Exception as e:
                console.print(f"[red]Error reading URL file: {e}[/red]")
                return

        if not urls:
            console.print("[red]No URLs provided. Exiting.[/red]")
            return

    # Run scan
    console.print(f"\n[bold yellow]🔍 Scanning [bold green]{len(urls)}[/bold green] URLs for emails...[/bold yellow]\n")

    start_time = time.time()
    results = asyncio.run(scan_urls(urls, debug))
    duration = time.time() - start_time

    # Display results
    total_emails = display_results(results)
    console.print(f"\n[bold green]✅ Scan finished in {duration:.1f}s. Found [bold yellow]{total_emails}[/bold yellow] unique emails across all URLs.[/bold green]")

    # Save results
    json_path, csv_path = save_results(results, prefix="emails_extract")
    saved = []
    if json_path:
        saved.append(str(json_path))
    if csv_path:
        saved.append(str(csv_path))
    if saved:
        console.print(f"[green]💾 Results saved to:[/green] {', '.join(saved)}")
    else:
        console.print("[yellow]⚠️  No results were saved (I/O error).[/yellow]")


if __name__ == "__main__":
    try:
        import asyncio
        main()
    except KeyboardInterrupt:
        console.print("\n[red]🛑 Scan interrupted by user.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
