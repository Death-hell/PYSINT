#!/usr/bin/env python3
"""
wayback-Scan.py - Wayback Machine Archive Scanner for PYSINT Suite
Author: YourNameHere
License: MIT
Repository: ~/PYSINT

Features:
- Fetch archived snapshots from Wayback Machine (web.archive.org)
- Display snapshot dates and original URLs
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--domain, --limit, etc.) + Interactive fallback
- Debug mode (--debug) to show API requests and raw responses
- Help (--help) via argparse (native)
"""

import requests
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
DEFAULT_LIMIT = 10
DEFAULT_TIMEOUT = 60.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
def wayback_lookup(domain: str, limit: int, debug: bool = False):
    """Lookup Wayback Machine snapshots for a domain"""
    # Construct API URL
    url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=timestamp,original&collapse=digest"
    
    if debug:
        console.print(f"[DEBUG] API URL: {url}")

    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        
        if debug:
            console.print(f"[DEBUG] Response Status: {response.status_code}")
            if response.status_code == 200:
                console.print(f"[DEBUG] Response Length: {len(response.text)} bytes")

        if response.status_code != 200:
            return {
                "domain": domain,
                "error": f"HTTP {response.status_code}",
                "snapshots": []
            }

        data = response.json()
        
        if debug:
            console.print(f"[DEBUG] JSON parsed successfully. {len(data)} rows received.")

        if len(data) <= 1:
            return {
                "domain": domain,
                "error": None,
                "snapshots": []
            }

        # Process snapshots (skip header row)
        snapshots = []
        for entry in data[1:]:
            if len(entry) >= 2:
                timestamp = entry[0]
                original_url = entry[1]
                
                # Format date: YYYY-MM-DD
                try:
                    date_str = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
                except:
                    date_str = timestamp
                
                snapshots.append({
                    "timestamp": timestamp,
                    "date": date_str,
                    "original_url": original_url
                })

        # Apply limit
        if limit > 0:
            snapshots = snapshots[:limit]

        return {
            "domain": domain,
            "error": None,
            "snapshots": snapshots
        }

    except requests.RequestException as e:
        if debug:
            console.print(f"[DEBUG] Request exception: {e}")
        return {
            "domain": domain,
            "error": f"RequestException: {e}",
            "snapshots": []
        }
    except json.JSONDecodeError as e:
        if debug:
            console.print(f"[DEBUG] JSON decode error: {e}")
        return {
            "domain": domain,
            "error": f"JSONDecodeError: {e}",
            "snapshots": []
        }
    except Exception as e:
        if debug:
            console.print(f"[DEBUG] Unexpected error: {e}")
        return {
            "domain": domain,
            "error": f"{type(e).__name__}: {e}",
            "snapshots": []
        }


# ================== MAIN SCAN FUNCTION ==================
def scan_domains(domains: list, limit: int, debug: bool):
    """Scan multiple domains for Wayback Machine snapshots"""
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} domains"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Scanning domains...", total=len(domains))

        for domain in domains:
            progress.update(task, description=f"[cyan]Scanning {domain}...")
            result = wayback_lookup(domain, limit, debug)
            results.append(result)
            progress.advance(task)

    return results


# ================== UTILS ==================
def display_results(results: list):
    """Display results in rich tables"""
    for result in results:
        domain = result["domain"]
        error = result.get("error")
        snapshots = result["snapshots"]

        if error:
            console.print(f"[red]❌ Error for {domain}: {error}[/red]")
            continue

        if not snapshots:
            console.print(f"[yellow]⚠️  No archived versions found for {domain}[/yellow]")
            continue

        table = Table(title=f"🌐 Wayback Machine Snapshots for {domain}", header_style="bold magenta", show_lines=True)
        table.add_column("Date", style="cyan", justify="center")
        table.add_column("Timestamp", style="yellow", justify="center")
        table.add_column("Original URL", style="green")

        for snapshot in snapshots:
            table.add_row(
                snapshot["date"],
                snapshot["timestamp"],
                snapshot["original_url"]
            )

        console.print(table)
        console.print(f"[bold green]✅ Found {len(snapshots)} snapshots for {domain}[/bold green]\n")


def save_results(results: list, prefix: str = "wayback_scan", results_dir: Path = DEFAULT_RESULTS_DIR):
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
            fieldnames = ["domain", "timestamp", "date", "original_url", "error"]
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                domain = result["domain"]
                error = result.get("error")
                snapshots = result["snapshots"]
                
                if error:
                    writer.writerow({
                        "domain": domain,
                        "timestamp": "",
                        "date": "",
                        "original_url": "",
                        "error": error
                    })
                else:
                    if snapshots:
                        for snapshot in snapshots:
                            writer.writerow({
                                "domain": domain,
                                "timestamp": snapshot["timestamp"],
                                "date": snapshot["date"],
                                "original_url": snapshot["original_url"],
                                "error": ""
                            })
                    else:
                        writer.writerow({
                            "domain": domain,
                            "timestamp": "",
                            "date": "",
                            "original_url": "",
                            "error": "No snapshots found"
                        })
    except Exception as e:
        console.print(f"[red]Failed to save CSV results: {e}[/red]")
        csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Wayback Scanner — Archive.org Snapshot Finder",
        epilog="Example: python3 wayback-Scan.py --domain example.com --limit 20 --debug"
    )
    parser.add_argument("--domain", "-d", action="append", help="Domain(s) to scan for Wayback Machine snapshots (can be used multiple times)")
    parser.add_argument("--file", "-f", help="File containing domains (one per line)")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Maximum number of snapshots to show (0 = all, default: {DEFAULT_LIMIT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows API requests and raw responses)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT Wayback Scanner[/bold green]")

    # If no domain provided, fallback to interactive mode
    if not args.domain and not args.file:
        domain = Prompt.ask("[bold cyan]Enter the website (without http/https)")
        if not domain:
            console.print("[red]No domain provided. Exiting.[/red]")
            return

        limit_input = Prompt.ask(f"[bold cyan]Enter maximum number of snapshots to show (0 = all, max 50, default: {DEFAULT_LIMIT})", default=str(DEFAULT_LIMIT))
        limit = int(limit_input) if limit_input.isdigit() else DEFAULT_LIMIT
        limit = min(limit, 50)  # Cap to avoid too many results
        debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)

        domains = [domain.strip()]
    else:
        # CLI mode
        debug = args.debug
        limit = args.limit
        limit = min(limit, 50) if limit > 0 else limit  # Cap to 50 if limit > 0
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

    # Run scan
    console.print(f"\n[bold yellow]🔍 Scanning [bold green]{len(domains)}[/bold green] domains for Wayback Machine snapshots...[/bold yellow]\n")

    start_time = time.time()
    results = scan_domains(domains, limit, debug)
    duration = time.time() - start_time

    # Display results
    display_results(results)
    console.print(f"\n[bold green]✅ Scan finished in {duration:.1f}s.[/bold green]")

    # Save results
    json_path, csv_path = save_results(results, prefix="wayback_scan")
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
        main()
    except KeyboardInterrupt:
        console.print("\n[red]🛑 Scan interrupted by user.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
