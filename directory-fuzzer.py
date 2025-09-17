#!/usr/bin/env python3
"""
directory-fuzzer.py - Directory & File Brute-Forcer for PYSINT Suite
Author: Mael
License: MIT
Repository: ~/PyToolKit

Features:
- Brute-force directories and files using wordlist
- Concurrent async requests
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--url, --wordlist, etc.) + Interactive fallback
- Debug mode (--debug) to log full responses and headers
- Help (--help) via argparse (native)
"""

import asyncio
import httpx
import json
import csv
import os
import time
import argparse
from pathlib import Path
from datetime import datetime
from asyncio import Semaphore

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm

# ================== DEFAULTS ==================
DEFAULT_WORDLIST = "wordlist/directory-wordlist.txt"
DEFAULT_MAX_CONCURRENT = 10
DEFAULT_TIMEOUT = 10.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))

# Ensure results directory exists
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
async def test_path(
    client: httpx.AsyncClient,
    domain: str,
    path: str,
    active_paths: list,
    sem: Semaphore,
    debug: bool = False
):
    """Test a single path against the domain"""
    async with sem:
        url = f"{domain.rstrip('/')}/{path.lstrip('/')}"

        try:
            r = await client.get(url, timeout=DEFAULT_TIMEOUT)

            if debug:
                console.print(f"[DEBUG] {r.status_code} {url} | Content-Length: {r.headers.get('content-length', 'N/A')} | Server: {r.headers.get('server', 'N/A')}")

            if 200 <= r.status_code < 400:
                result = {
                    "path": path,
                    "url": url,
                    "status_code": r.status_code,
                    "content_length": len(r.content),
                    "server": r.headers.get("server", ""),
                    "content_type": r.headers.get("content-type", "")
                }
                active_paths.append(result)
                return result
            else:
                return None

        except httpx.RequestError as e:
            if debug:
                console.print(f"[DEBUG] Request failed for {url}: {e}")
            return {
                "path": path,
                "url": url,
                "status_code": None,
                "error": str(e),
                "content_length": 0,
                "server": "",
                "content_type": ""
            }
        except Exception as e:
            if debug:
                console.print(f"[DEBUG] Unexpected error for {url}: {e}")
            return {
                "path": path,
                "url": url,
                "status_code": None,
                "error": f"{type(e).__name__}: {e}",
                "content_length": 0,
                "server": "",
                "content_type": ""
            }


# ================== MAIN SCAN FUNCTION ==================
async def scan_paths(
    domain: str,
    paths: list,
    max_concurrent: int,
    debug: bool
):
    active_paths = []
    sem = Semaphore(max_concurrent)

    async with httpx.AsyncClient(follow_redirects=True, timeout=DEFAULT_TIMEOUT) as client:
        tasks = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} paths"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Scanning {domain}...", total=len(paths))

            for path in paths:
                coro = test_path(client, domain, path, active_paths, sem, debug)
                t = asyncio.create_task(coro)
                t.add_done_callback(lambda fut: progress.advance(task))
                tasks.append(t)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks)

    # Filter only successful paths (status 200-399)
    successful = [p for p in active_paths if p.get("status_code") and 200 <= p["status_code"] < 400]
    return successful, active_paths


# ================== UTILS ==================
def load_wordlist(file_path: str, limit: int = 0):
    """Load wordlist from file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            paths = [line.strip() for line in f if line.strip()]
        if limit > 0:
            return paths[:limit]
        return paths
    except FileNotFoundError:
        console.print(f"[bold red]Wordlist file {file_path} not found![/bold red]")
        return []
    except Exception as e:
        console.print(f"[bold red]Error reading wordlist: {e}[/bold red]")
        return []


def save_results(results: list, prefix: str = "dirfuzz", results_dir: Path = DEFAULT_RESULTS_DIR):
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
    if results:
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                fieldnames = ["path", "url", "status_code", "content_length", "server", "content_type", "error"]
                writer = csv.DictWriter(cf, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    writer.writerow({
                        "path": r.get("path", ""),
                        "url": r.get("url", ""),
                        "status_code": r.get("status_code", ""),
                        "content_length": r.get("content_length", 0),
                        "server": r.get("server", ""),
                        "content_type": r.get("content_type", ""),
                        "error": r.get("error", "")
                    })
        except Exception as e:
            console.print(f"[red]Failed to save CSV results: {e}[/red]")
            csv_path = None

    return json_path, csv_path


def display_results(found: list, domain: str):
    """Display results in a rich table"""
    table = Table(title=f"Active Directories/Files for {domain}", show_lines=True)
    table.add_column("Path", style="cyan", no_wrap=False)
    table.add_column("Status", style="green", justify="center")
    table.add_column("Content-Length", style="yellow", justify="right")
    table.add_column("URL", style="magenta")

    for item in found:
        table.add_row(
            item["path"],
            str(item["status_code"]),
            str(item["content_length"]),
            item["url"]
        )

    console.print(table)


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Directory Fuzzer — Find Hidden Paths & Files",
        epilog="Example: python3 directory-fuzzer.py --url https://example.com --wordlist custom.txt --limit 1000 --debug"
    )
    parser.add_argument("--url", "-u", help="Target URL (with http/https)")
    parser.add_argument("--wordlist", "-w", default=DEFAULT_WORDLIST, help=f"Path to wordlist (default: {DEFAULT_WORDLIST})")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of paths to test (0 = all)")
    parser.add_argument("--concurrent", type=int, default=DEFAULT_MAX_CONCURRENT, help=f"Max concurrent requests (default: {DEFAULT_MAX_CONCURRENT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows headers and errors)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold red]PYSINT Directory Fuzzer[/bold red]")

    # If no URL provided, fallback to interactive mode
    if not args.url:
        domain = Prompt.ask("[bold cyan]Enter the website to scan (with http/https)")
        if not domain:
            console.print("[red]No URL provided. Exiting.[/red]")
            return

        limit_input = Prompt.ask("[bold yellow]Enter maximum number of directories/files to test (0 = all)", default="0")
        limit = int(limit_input) if limit_input.isdigit() else 0
        wordlist_file = Prompt.ask("[bold yellow]Wordlist file path", default=DEFAULT_WORDLIST)
        concurrent_input = Prompt.ask("[bold yellow]Max concurrent requests", default=str(DEFAULT_MAX_CONCURRENT))
        max_concurrent = int(concurrent_input) if concurrent_input.isdigit() else DEFAULT_MAX_CONCURRENT
        debug = Confirm.ask("[bold yellow]Enable debug mode?", default=False)

    else:
        # CLI mode
        domain = args.url
        wordlist_file = args.wordlist
        limit = args.limit
        max_concurrent = args.concurrent
        debug = args.debug

    # Load wordlist
    paths = load_wordlist(wordlist_file, limit)
    if not paths:
        console.print("[red]No paths to scan. Exiting.[/red]")
        return

    console.print(f"\n[bold yellow]🔍 Scanning {domain} for [bold green]{len(paths)}[/bold green] directories/files...[/bold yellow]\n")

    # Run scan
    start_time = time.time()
    found, all_results = asyncio.run(scan_paths(domain, paths, max_concurrent, debug))
    duration = time.time() - start_time

    # Display results
    if found:
        display_results(found, domain)
        console.print(f"\n[bold green]✅ Scan finished in {duration:.1f}s. Found [bold yellow]{len(found)}[/bold yellow] active paths.[/bold green]")
    else:
        console.print(f"\n[bold yellow]✅ Scan finished in {duration:.1f}s. No active paths found.[/bold yellow]")

    # Save ALL results (including 404s and errors) for analysis
    json_path, csv_path = save_results(all_results, prefix=f"dirfuzz_{domain.replace('://', '_').replace('/', '_').replace('.', '_')}")
    saved = []
    if json_path:
        saved.append(str(json_path))
    if csv_path:
        saved.append(str(csv_path))
    if saved:
        console.print(f"[green]💾 All results saved to:[/green] {', '.join(saved)}")
    else:
        console.print("[yellow]⚠️  No results were saved (I/O error).[/yellow]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]🛑 Scan interrupted by user.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
