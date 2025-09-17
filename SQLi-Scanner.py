#!/usr/bin/env python3
"""
SQLi-Scanner.py - SQL Injection Scanner for PYSINT Suite
Author: Mael
License: MIT
Repository: ~/PyToolKit

Features:
- Scans URL parameters for SQL Injection vulnerabilities
- Uses wordlist (SQLi-wordlist.txt by default)
- Concurrent async requests
- Detects SQLi via error messages in response (MySQL, PostgreSQL, MSSQL, etc.)
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--url, --params, etc.) + Interactive fallback
- Debug mode (--debug) to log requests/responses
- Help (--help) via argparse (native)
"""

import asyncio
import httpx
import urllib.parse
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
DEFAULT_WORDLIST = "wordlist/SQLi-wordlist.txt"
DEFAULT_MAX_CONCURRENT = 10
DEFAULT_TIMEOUT = 15.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))

# Ensure results directory exists
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
async def test_sqli(
    client: httpx.AsyncClient,
    url: str,
    param: str,
    payload: str,
    sem: Semaphore,
    debug: bool = False
):
    """
    Test a single SQLi payload against a parameter.
    Returns a dict: {param, url, status, result, reason, response_length, response_preview}
    result in {"vulnerable", "safe", "error"}
    """
    async with sem:
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            query_params[param] = payload
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            full_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"

            if debug:
                console.print(f"[DEBUG] Testing: {full_url}")

            resp = await client.get(full_url, timeout=DEFAULT_TIMEOUT)
            text = (resp.text or "").lower()

            # SQLi Error Indicators (case-insensitive)
            indicators = [
                "you have an error in your sql syntax",
                "unclosed quotation mark after the character string",
                "warning: mysql",
                "pg_query()",
                "syntax error",
                "database error",
                "sqlstate",
                "mysql_fetch",
                "native client",
                "unterminated quoted string",
                "quoted string not properly terminated",
                "sql command not properly ended",
                "ora-01756",
                "ora-00933",
                "invalid column name",
                "mysql_num_rows()",
                "mssql_query()",
                "odbc sql server driver",
                "sqlite3_",
                "sqlite error",
                "group by clause",
                "order by clause",
                "union select",
                "procedure expects parameter",
                "sql injection",
            ]

            if any(ind in text for ind in indicators):
                if debug:
                    console.print(f"[DEBUG] SQLi indicator matched for {full_url}")
                return {
                    "param": param,
                    "url": full_url,
                    "status": resp.status_code,
                    "result": "vulnerable",
                    "reason": "error_indicator",
                    "response_length": len(resp.text),
                    "response_preview": resp.text[:200].replace('\n', ' ') if debug else ""
                }
            else:
                return {
                    "param": param,
                    "url": full_url,
                    "status": resp.status_code,
                    "result": "safe",
                    "reason": "",
                    "response_length": len(resp.text),
                    "response_preview": resp.text[:200].replace('\n', ' ') if debug else ""
                }

        except httpx.RequestError as e:
            if debug:
                console.print(f"[DEBUG] Request error for {url} (param={param}, payload={payload}): {e}")
            return {
                "param": param,
                "url": full_url if 'full_url' in locals() else url,
                "status": None,
                "result": "error",
                "reason": f"request_error: {e}",
                "response_length": 0,
                "response_preview": ""
            }
        except Exception as e:
            if debug:
                console.print(f"[DEBUG] Unexpected error: {e}")
            return {
                "param": param,
                "url": full_url if 'full_url' in locals() else url,
                "status": None,
                "result": "error",
                "reason": f"exception: {type(e).__name__}: {e}",
                "response_length": 0,
                "response_preview": ""
            }


# ================== MAIN SCAN FUNCTION ==================
async def run_sqli_scan(
    url: str,
    parameters: list,
    wordlist_file: str,
    max_payloads: int,
    max_concurrent: int,
    debug: bool
):
    # Load payloads
    try:
        with open(wordlist_file, "r", encoding="utf-8") as f:
            payloads = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        console.print(f"[bold red]Wordlist file {wordlist_file} not found. Exiting.[/red]")
        return []

    if max_payloads > 0:
        payloads = payloads[:max_payloads]

    total = len(parameters) * len(payloads)
    console.print(f"\n[bold yellow]🔍 Testing {len(payloads)} SQLi payloads on {len(parameters)} parameters ({total} requests)...[/bold yellow]\n")

    sem = Semaphore(max_concurrent)
    results = []

    async with httpx.AsyncClient(follow_redirects=True, timeout=DEFAULT_TIMEOUT) as client:
        tasks = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
            task = progress.add_task("[green]Scanning SQLi payloads...", total=total)
            for param in parameters:
                for payload in payloads:
                    coro = test_sqli(client, url, param, payload, sem, debug)
                    t = asyncio.create_task(coro)
                    t.add_done_callback(lambda fut: progress.update(task, advance=1))
                    tasks.append(t)

            # Gather results
            for done in asyncio.as_completed(tasks):
                res = await done
                results.append(res)

    return results


# ================== UTILS ==================
def save_results(results: list, prefix: str = "sqli", results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save results as JSON and CSV with timestamp in RESULTS_DIR. Returns paths."""
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
                fieldnames = ["param", "url", "status", "result", "reason", "response_length", "response_preview"]
                writer = csv.DictWriter(cf, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    writer.writerow({
                        "param": r.get("param", ""),
                        "url": r.get("url", ""),
                        "status": r.get("status", ""),
                        "result": r.get("result", ""),
                        "reason": r.get("reason", ""),
                        "response_length": r.get("response_length", 0),
                        "response_preview": r.get("response_preview", "")
                    })
        except Exception as e:
            console.print(f"[red]Failed to save CSV results: {e}[/red]")
            csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT SQLi Scanner — SQL Injection Detector",
        epilog="Example: python3 SQLi-Scanner.py --url 'https://example.com/search?q=test' --params q --max-payloads 50 --debug"
    )
    parser.add_argument("--url", "-u", help="Target URL with at least one query parameter (e.g., https://example.com/search?q=test)")
    parser.add_argument("--params", "-p", help="Comma-separated list of parameters to test (e.g., 'q,id,search'). If omitted, uses all from URL.")
    parser.add_argument("--wordlist", "-w", default=DEFAULT_WORDLIST, help=f"Path to SQLi payloads wordlist (default: {DEFAULT_WORDLIST})")
    parser.add_argument("--max-payloads", type=int, default=0, help="Maximum number of payloads to test (0 = all)")
    parser.add_argument("--concurrent", type=int, default=DEFAULT_MAX_CONCURRENT, help=f"Max concurrent requests (default: {DEFAULT_MAX_CONCURRENT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows URLs and response previews)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold red]PYSINT SQLi Scanner[/bold red]")

    # If no URL provided, fallback to interactive mode
    if not args.url:
        url = Prompt.ask("[bold cyan]Enter target URL (with http/https and at least one parameter)")
        if not url:
            console.print("[red]No URL provided. Exiting.[/red]")
            return

        params_input = Prompt.ask("[bold cyan]Enter comma-separated parameters to test (or leave blank for all)")
        if params_input:
            parameters = [p.strip() for p in params_input.split(",") if p.strip()]
        else:
            parsed = urllib.parse.urlparse(url)
            parameters = list(urllib.parse.parse_qs(parsed.query).keys())
            if not parameters:
                console.print("[bold red]No parameters found in URL. Exiting.[/red]")
                return

        max_payloads_input = Prompt.ask("[bold cyan]Enter maximum number of payloads to test (0 = all)", default="0")
        max_payloads = int(max_payloads_input) if max_payloads_input.isdigit() else 0
        wordlist_file = Prompt.ask("[bold cyan]Wordlist file path", default=DEFAULT_WORDLIST)
        concurrent_input = Prompt.ask("[bold cyan]Max concurrent requests", default=str(DEFAULT_MAX_CONCURRENT))
        max_concurrent = int(concurrent_input) if concurrent_input.isdigit() else DEFAULT_MAX_CONCURRENT
        debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)

    else:
        # CLI mode
        url = args.url
        wordlist_file = args.wordlist
        max_payloads = args.max_payloads
        max_concurrent = args.concurrent
        debug = args.debug

        if args.params:
            parameters = [p.strip() for p in args.params.split(",") if p.strip()]
        else:
            parsed = urllib.parse.urlparse(url)
            parameters = list(urllib.parse.parse_qs(parsed.query).keys())
            if not parameters:
                console.print("[bold red]No parameters found in URL. Exiting.[/red]")
                return

    # Run scan
    start_time = time.time()
    results = asyncio.run(
        run_sqli_scan(url, parameters, wordlist_file, max_payloads, max_concurrent, debug)
    )
    duration = time.time() - start_time

    # Display results
    table = Table(title="SQLi Scan Results", show_lines=True)
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Status/Code", style="magenta")
    table.add_column("URL", style="green")
    table.add_column("Reason", style="yellow")

    vulns = 0
    for r in results:
        param = r.get("param", "")
        full_url = r.get("url", "") or "-"
        status = r.get("status", "")
        result_flag = r.get("result", "")
        reason = r.get("reason", "") or ""

        if result_flag == "vulnerable":
            table.add_row(param, f"[bold red]VULNERABLE ({status})[/bold red]", full_url, reason)
            vulns += 1
        elif result_flag == "safe":
            table.add_row(param, f"[green]SAFE ({status})[/green]", full_url, reason)
        else:  # error
            table.add_row(param, f"[yellow]ERROR[/yellow]", full_url, reason)

    console.print(table)
    console.print(f"\n[bold yellow]✅ Scan finished in {duration:.1f}s. Vulnerable parameters found: {vulns}[/bold yellow]")

    # Save results
    json_path, csv_path = save_results(results, prefix="sqli")
    saved = []
    if json_path:
        saved.append(str(json_path))
    if csv_path:
        saved.append(str(csv_path))
    if saved:
        console.print(f"[green]Results saved to:[/green] {', '.join(saved)}")
    else:
        console.print("[yellow]No results were saved (I/O error).[/yellow]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Scan interrupted by user.[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
