#!/usr/bin/env python3
"""
dns-hunter.py - Advanced DNS Record Scanner for PYSINT Suite
Author: Mael
License: MIT
Repository: ~/PyToolKit

Features:
- Query multiple DNS record types (A, MX, NS, TXT, CNAME, AAAA, SOA, etc.)
- Uses configurable DNS resolvers (Google, Cloudflare, custom)
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--domain, --record-types, etc.) + Interactive fallback
- Debug mode (--debug) to log resolver config, query times, and raw responses
- Help (--help) via argparse (native)
"""

import dns.resolver
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
from rich.progress import Progress, SpinnerColumn, TextColumn

# ================== DEFAULTS ==================
DEFAULT_NAMESERVERS = ['8.8.8.8', '1.1.1.1']  # Google DNS, Cloudflare
DEFAULT_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))

# Ensure results directory exists
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
def query_dns(domain: str, record_types: list, nameservers: list, debug: bool = False):
    """Query DNS records for a domain"""
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = nameservers

    if debug:
        console.print(f"[DEBUG] Using DNS servers: {', '.join(nameservers)}")

    results = {}

    for rtype in record_types:
        try:
            start_time = time.time()
            answers = resolver.resolve(domain, rtype, lifetime=5.0)
            query_time = round((time.time() - start_time) * 1000, 2)

            records = [rdata.to_text() for rdata in answers]
            results[rtype] = {
                "records": records,
                "count": len(records),
                "query_time_ms": query_time,
                "error": None
            }

            if debug:
                console.print(f"[DEBUG] {rtype} query took {query_time}ms, found {len(records)} records")

            # Display table
            table = Table(title=f"{rtype} records for {domain} ({query_time}ms)", show_lines=True)
            table.add_column("Record", style="cyan", no_wrap=False)
            for record in records:
                table.add_row(record)
            console.print(table)

        except dns.resolver.NoAnswer:
            results[rtype] = {
                "records": [],
                "count": 0,
                "query_time_ms": 0,
                "error": "NoAnswer"
            }
            console.print(f"[yellow]{rtype} records for {domain}: No answer[/yellow]")

        except dns.resolver.NXDOMAIN:
            results[rtype] = {
                "records": [],
                "count": 0,
                "query_time_ms": 0,
                "error": "NXDOMAIN"
            }
            console.print(f"[red]{rtype} records for {domain}: Domain does not exist[/red]")
            break  # If domain doesn't exist, no point checking other records

        except dns.exception.Timeout:
            results[rtype] = {
                "records": [],
                "count": 0,
                "query_time_ms": 0,
                "error": "Timeout"
            }
            console.print(f"[red]{rtype} records for {domain}: Query timeout[/red]")

        except Exception as e:
            results[rtype] = {
                "records": [],
                "count": 0,
                "query_time_ms": 0,
                "error": f"{type(e).__name__}: {e}"
            }
            console.print(f"[red]{rtype} records for {domain}: Error - {e}[/red]")

    return results


# ================== UTILS ==================
def save_results(data: dict, domain: str, prefix: str = "dns", results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save DNS results as JSON and CSV with timestamp"""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_domain = domain.replace('.', '_').replace(':', '_')
    json_path = results_dir / f"{prefix}_{safe_domain}_{ts}.json"
    csv_path = results_dir / f"{prefix}_{safe_domain}_{ts}.csv"

    # Save JSON
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(data, jf, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"[red]Failed to save JSON results: {e}[/red]")
        json_path = None

    # Save CSV
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            writer = csv.writer(cf)
            writer.writerow(["Record Type", "Record", "Query Time (ms)", "Error"])
            for rtype, info in data.items():
                if info["records"]:
                    for record in info["records"]:
                        writer.writerow([rtype, record, info["query_time_ms"], ""])
                else:
                    writer.writerow([rtype, "", info["query_time_ms"], info["error"] or "No records"])
    except Exception as e:
        console.print(f"[red]Failed to save CSV results: {e}[/red]")
        csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT DNS Hunter — Advanced DNS Record Scanner",
        epilog="Example: python3 dns-hunter.py --domain example.com --record-types A,MX,TXT --nameserver 8.8.8.8 --debug"
    )
    parser.add_argument("--domain", "-d", help="Domain to query DNS records for")
    parser.add_argument("--record-types", "-r", help="Comma-separated record types (e.g., A,MX,TXT,AAAA,NS,CNAME,SOA)")
    parser.add_argument("--nameserver", "-n", action="append", help="Custom DNS server(s) to use (can be used multiple times)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows query times and resolver config)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT DNS Hunter[/bold green]")

    # If no domain provided, fallback to interactive mode
    if not args.domain:
        domain = Prompt.ask("[bold cyan]Enter the domain you want to check DNS records for")
        if not domain:
            console.print("[red]No domain provided. Exiting.[/red]")
            return

        record_types_input = Prompt.ask(
            f"[bold yellow]Enter comma-separated record types (default: {','.join(DEFAULT_RECORD_TYPES)})",
            default=",".join(DEFAULT_RECORD_TYPES)
        )
        record_types = [t.strip().upper() for t in record_types_input.split(",")] if record_types_input else DEFAULT_RECORD_TYPES

        nameservers_input = Prompt.ask(
            f"[bold yellow]Enter comma-separated DNS servers (default: {','.join(DEFAULT_NAMESERVERS)})",
            default=",".join(DEFAULT_NAMESERVERS)
        )
        nameservers = [ns.strip() for ns in nameservers_input.split(",")] if nameservers_input else DEFAULT_NAMESERVERS

        debug = Confirm.ask("[bold yellow]Enable debug mode?", default=False)

    else:
        # CLI mode
        domain = args.domain
        debug = args.debug

        if args.record_types:
            record_types = [t.strip().upper() for t in args.record_types.split(",")]
        else:
            record_types = DEFAULT_RECORD_TYPES

        if args.nameserver:
            nameservers = args.nameserver
        else:
            nameservers = DEFAULT_NAMESERVERS

    # Run DNS queries
    console.print(f"\n[bold yellow]🔍 Querying DNS records for [bold cyan]{domain}[/bold cyan]...[/bold yellow]\n")

    start_time = time.time()
    results = query_dns(domain, record_types, nameservers, debug)
    duration = time.time() - start_time

    console.print(f"\n[bold green]✅ DNS query finished in {duration:.1f}s.[/bold green]")

    # Save results
    json_path, csv_path = save_results(results, domain)
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
        console.print("\n[red]🛑 DNS query interrupted by user.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
