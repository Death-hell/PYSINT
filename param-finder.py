#!/usr/bin/env python3
"""
param-finder.py - HTTP Parameter Discovery Scanner for PYSINT Suite
Author: YourNameHere
License: MIT
Repository: ~/PYSINT

Features:
- Discover active HTTP parameters by appending ?param=test to URLs
- Uses wordlist (large-params.txt by default)
- Concurrent async requests
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--url, --wordlist, etc.) + Interactive fallback
- Debug mode (--debug) to log headers, response snippets, and timing
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
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# ================== DEFAULTS ==================
DEFAULT_WORDLIST = "large-params.txt"
DEFAULT_MAX_CONCURRENT = 10
DEFAULT_TIMEOUT = 10.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))

# Ensure results directory exists
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
async def test_param(
    client: httpx.AsyncClient,
    domain: str,
    param: str,
    sem: Semaphore,
    debug: bool = False
):
    """Test a single parameter against the domain"""
    async with sem:
        url = f"{domain}?{param}=test"

        try:
            start_time = time.time()
            r = await client.get(url, timeout=DEFAULT_TIMEOUT)
            duration = time.time() - start_time

            if debug:
                console.print(f"[DEBUG] {r.status_code} {url} | Time: {duration:.2f}s | Content-Length: {r.headers.get('content-length', 'N/A')}")

            result = {
                "param": param,
                "url": url,
                "status_code": r.status_code,
                "duration_seconds": duration,
                "content_length": len(r.content) if r.content else 0,
                "server": r.headers.get("server", ""),
                "content_type": r.headers.get("content-type", ""),
                "is_active": r.status_code < 400
            }

            if r.status_code < 400:
                if debug:
                    snippet = r.text[:200].replace('\n', ' ') if r.text else ""
                    console.print(f"[DEBUG] Active parameter '{param}' response snippet: {snippet}")
                return result
            else:
                return result

        except httpx.RequestError as e:
            if debug:
                console.print(f"[DEBUG] Request failed for {url}: {e}")
            return {
                "param": param,
                "url": url,
                "status_code": None,
                "duration_seconds": 0,
                "content_length": 0,
                "server": "",
                "content_type": "",
                "is_active": False,
                "error": f"RequestError: {e}"
            }
        except Exception as e:
            if debug:
                console.print(f"[DEBUG] Unexpected error for {url}: {e}")
            return {
                "param": param,
                "url": url,
                "status_code": None,
                "duration_seconds": 0,
                "content_length": 0,
                "server": "",
                "content_type": "",
                "is_active": False,
                "error": f"{type(e).__name__}: {e}"
            }


# ================== MAIN SCAN FUNCTION ==================
async def scan_parameters(
    domain: str,
    params: list,
    max_concurrent: int,
    debug: bool
):
    """Scan multiple parameters against the domain"""
    active_params = []
    sem = Semaphore(max_concurrent)

    async with httpx.AsyncClient(follow_redirects=True, timeout=DEFAULT_TIMEOUT) as client:
        tasks = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} params"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Scanning parameters for {domain}...", total=len(params))

            for param in params:
                coro = test_param(client, domain, param, sem, debug)
                t = asyncio.create_task(coro)
                t.add_done_callback(lambda fut: progress.advance(task))
                tasks.append(t)

            # Wait for all tasks to complete
            results = []
            for coro in asyncio.as_completed(tasks):
                res = await coro
                results.append(res)
                if res["is_active"]:
                    active_params.append(res)

    return active_params, results


# ================== UTILS ==================
def load_wordlist(file_path: str, limit: int = 0):
    """Load wordlist from file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            params = [line.strip() for line in f if line.strip()]
        if limit > 0:
            return params[:limit]
        return params
    except FileNotFoundError:
        console.print(f"[red]Wordlist file {file_path} not found![/red]")
        return []
    except Exception as e:
        console.print(f"[red]Error reading wordlist: {e}[/red]")
        return []


def save_results(results: list, domain: str, prefix: str = "param_scan", results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save results as JSON and CSV with timestamp"""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_domain = domain.replace('://', '_').replace('/', '_').replace('.', '_')
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
                fieldnames = ["param", "url", "status_code", "duration_seconds", "content_length", "server", "content_type", "is_active", "error"]
                writer = csv.DictWriter(cf, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    writer.writerow({
                        "param": r.get("param", ""),
                        "url": r.get("url", ""),
                        "status_code": r.get("status_code", ""),
                        "duration_seconds": r.get("duration_seconds", 0),
                        "content_length": r.get("content_length", 0),
                        "server": r.get("server", ""),
                        "content_type": r.get("content_type", ""),
                        "is_active": r.get("is_active", False),
                        "error": r.get("error", "")
                    })
        except Exception as e:
            console.print(f"[red]Failed to save CSV results: {e}[/red]")
            csv_path = None

    return json_path, csv_path


def display_results(active_params: list, domain: str):
    """Display results in a rich table"""
    if active_params:
        table = Table(title=f"✅ Active Parameters Found for {domain}", show_lines=True)
        table.add_column("Parameter", style="cyan", no_wrap=False)
        table.add_column("HTTP Status", style="green", justify="center")
        table.add_column("Response Time", style="yellow", justify="right")
        table.add_column("Content Length", style="magenta", justify="right")
        table.add_column("URL", style="blue")

        for item in active_params:
            table.add_row(
                item["param"],
                str(item["status_code"]),
                f"{item['duration_seconds']:.2f}s",
                str(item["content_length"]),
                item["url"]
            )

        console.print(table)
        console.print(f"\n[bold green]✅ Found [bold yellow]{len(active_params)}[/bold yellow] active parameters.[/bold green]")
    else:
        console.print(f"\n[bold yellow]✅ Scan completed. No active parameters found for {domain}.[/bold yellow]")


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Parameter Finder — Discover Active HTTP Parameters",
        epilog="Example: python3 param-finder.py --url https://example.com --wordlist custom-params.txt --limit 1000 --debug"
    )
    parser.add_argument("--url", "-u", help="Target URL (with http/https)")
    parser.add_argument("--wordlist", "-w", default=DEFAULT_WORDLIST, help=f"Path to parameters wordlist (default: {DEFAULT_WORDLIST})")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of parameters to test (0 = all)")
    parser.add_argument("--concurrent", type=int, default=DEFAULT_MAX_CONCURRENT, help=f"Max concurrent requests (default: {DEFAULT_MAX_CONCURRENT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows headers and response snippets)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT Parameter Finder[/bold green]")

    # If no URL provided, fallback to interactive mode
    if not args.url:
        domain = Prompt.ask("[bold cyan]Enter the website to scan (with http/https)")
        if not domain:
            console.print("[red]No URL provided. Exiting.[/red]")
            return

        limit_input = Prompt.ask("[bold yellow]Enter maximum number of parameters to test (0 = all)", default="0")
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
    params = load_wordlist(wordlist_file, limit)
    if not params:
        console.print("[red]No parameters to test. Exiting.[/red]")
        return

    console.print(f"\n[bold yellow]🔍 Scanning [bold green]{domain}[/bold green] for [bold green]{len(params)}[/bold green] parameters...[/bold yellow]\n")

    # Run scan
    start_time = time.time()
    active_params, all_results = asyncio.run(scan_parameters(domain, params, max_concurrent, debug))
    duration = time.time() - start_time

    # Display results
    display_results(active_params, domain)
    console.print(f"\n[bold green]✅ Scan finished in {duration:.1f}s. Tested {len(params)} parameters.[/bold green]")

    # Save ALL results (including inactive ones) for analysis
    json_path, csv_path = save_results(all_results, domain)
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
