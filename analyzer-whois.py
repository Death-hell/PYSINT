#!/usr/bin/env python3
"""
analyzer-whois.py - Domain & IP Whois Analyzer for PYSINT Suite
Author: YourNameHere
License: MIT
Repository: ~/PYSINT

Features:
- Lookup WHOIS for domains (using python-whois)
- Lookup RDAP/WHOIS for IPs (using ipwhois)
- CLI mode (--target, --type) + Interactive fallback
- Debug mode (--debug) to log raw responses and parsing steps
- Saves results to JSON/CSV in ~/PYSINT/results
- Help (--help) via argparse (native)
"""

import whois
from ipwhois import IPWhois
import json
import csv
import os
import argparse
import re
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

# ================== DEFAULTS ==================
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== UTILS ==================
def is_valid_ip(ip: str) -> bool:
    """Simple IP validation (IPv4/IPv6)"""
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'
    return bool(re.match(ipv4_pattern, ip)) or bool(re.match(ipv6_pattern, ip))


def is_valid_domain(domain: str) -> bool:
    """Simple domain validation"""
    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(domain_pattern, domain))


def save_results(data: dict, prefix: str, results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save Whois/IP results as JSON and CSV"""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', prefix)
    json_path = results_dir / f"{safe_prefix}_{ts}.json"
    csv_path = results_dir / f"{safe_prefix}_{ts}.csv"

    # Save JSON
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(data, jf, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        console.print(f"[red]Failed to save JSON results: {e}[/red]")
        json_path = None

    # Save CSV
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            writer = csv.writer(cf)
            writer.writerow(["Field", "Value"])
            for key, value in data.items():
                # Handle nested dicts/lists
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                writer.writerow([key, str(value)])
    except Exception as e:
        console.print(f"[red]Failed to save CSV results: {e}[/red]")
        csv_path = None

    return json_path, csv_path


def display_table(data: dict, title: str):
    """Display data in a rich table"""
    table = Table(title=title, show_lines=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    for key, value in data.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, indent=2, ensure_ascii=False, default=str)
        table.add_row(str(key), str(value))

    console.print(table)


# ================== CORE FUNCTIONS ==================
def analyze_domain(domain: str, debug: bool = False):
    """Analyze WHOIS for a domain"""
    if debug:
        console.print(f"[DEBUG] Looking up WHOIS for domain: {domain}")

    try:
        info = whois.whois(domain)
        data = {}

        # Convert WHOIS result to dict
        for key in dir(info):
            if not key.startswith('_') and not callable(getattr(info, key)):
                value = getattr(info, key)
                if value is not None:
                    data[key] = value

        if debug:
            console.print(f"[DEBUG] WHOIS lookup successful for {domain}")

        display_table(data, f"Whois Information for {domain}")
        json_path, csv_path = save_results(data, f"whois_domain_{domain.replace('.', '_')}")
        saved = []
        if json_path:
            saved.append(str(json_path))
        if csv_path:
            saved.append(str(csv_path))
        if saved:
            console.print(f"[green]Results saved to:[/green] {', '.join(saved)}")
        else:
            console.print("[yellow]No results were saved (I/O error).[/yellow]")

        return data

    except Exception as e:
        console.print(f"[bold red]ERROR! Failed to lookup WHOIS for {domain}:[/bold red] {e}")
        if debug:
            console.print_exception()
        return None


def analyze_ip(ip: str, debug: bool = False):
    """Analyze WHOIS/RDAP for an IP"""
    if debug:
        console.print(f"[DEBUG] Looking up RDAP for IP: {ip}")

    try:
        obj = IPWhois(ip)
        res = obj.lookup_rdap()

        if debug:
            console.print(f"[DEBUG] RDAP lookup successful for {ip}")

        display_table(res, f"IP Whois Information for {ip}")
        json_path, csv_path = save_results(res, f"whois_ip_{ip.replace('.', '_').replace(':', '_')}")
        saved = []
        if json_path:
            saved.append(str(json_path))
        if csv_path:
            saved.append(str(csv_path))
        if saved:
            console.print(f"[green]Results saved to:[/green] {', '.join(saved)}")
        else:
            console.print("[yellow]No results were saved (I/O error).[/yellow]")

        return res

    except Exception as e:
        console.print(f"[bold red]ERROR! Failed to lookup WHOIS for {ip}:[/bold red] {e}")
        if debug:
            console.print_exception()
        return None


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Whois/IP Analyzer — Domain & IP Intelligence Tool",
        epilog="Examples:\n"
               "  python3 analyzer-whois.py --target example.com --type domain\n"
               "  python3 analyzer-whois.py --target 8.8.8.8 --type ip --debug"
    )
    parser.add_argument("--target", "-t", help="Target domain or IP address")
    parser.add_argument("--type", choices=["domain", "ip"], help="Type of target: 'domain' or 'ip'")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows raw responses and errors)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold red]PYSINT Whois/IP Analyzer[/bold red]")

    # If no target provided, fallback to interactive mode
    if not args.target:
        while True:
            choice = Prompt.ask("[bold yellow]Do you want to check [domain/ip] or type 'exit' to quit[/bold yellow]").strip().lower()
            if choice == "domain":
                target = Prompt.ask("[bold cyan]Enter the domain to check (e.g., example.com)")
                if not target:
                    console.print("[red]No domain provided.[/red]")
                    continue
                if not is_valid_domain(target):
                    console.print("[yellow]Warning: Domain format may be invalid, but will try anyway.[/yellow]")
                debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)
                analyze_domain(target, debug=debug)

            elif choice == "ip":
                target = Prompt.ask("[bold cyan]Enter the IP to check (e.g., 8.8.8.8 or 2001:4860:4860::8888)")
                if not target:
                    console.print("[red]No IP provided.[/red]")
                    continue
                if not is_valid_ip(target):
                    console.print("[yellow]Warning: IP format may be invalid, but will try anyway.[/yellow]")
                debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)
                analyze_ip(target, debug=debug)

            elif choice == "exit":
                console.print("[bold green]Exiting analyzer. Goodbye![/bold green]")
                break
            else:
                console.print("[bold red]Invalid command! Please type 'domain', 'ip', or 'exit'.[/bold red]")

    else:
        # CLI mode
        target = args.target
        target_type = args.type
        debug = args.debug

        if not target_type:
            # Auto-detect type
            if is_valid_ip(target):
                target_type = "ip"
                console.print(f"[cyan]Auto-detected target type: IP[/cyan]")
            elif is_valid_domain(target):
                target_type = "domain"
                console.print(f"[cyan]Auto-detected target type: Domain[/cyan]")
            else:
                console.print("[red]Could not auto-detect target type. Please specify --type domain or --type ip.[/red]")
                return

        if target_type == "domain":
            analyze_domain(target, debug=debug)
        elif target_type == "ip":
            analyze_ip(target, debug=debug)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Analyzer interrupted by user.[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
