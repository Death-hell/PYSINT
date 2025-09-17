#!/usr/bin/env python3
"""
geoip-scan.py - GeoIP Location Scanner for PYSINT Suite
Author: Mael
License: MIT
Repository: ~/PyToolKit

Features:
- Resolve domain to IP and fetch GeoIP data (location, ISP, timezone, etc.)
- Uses ip-api.com (free) with fallback to ipinfo.io (if configured)
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--target, --file, etc.) + Interactive fallback
- Debug mode (--debug) to show raw API responses and DNS resolution
- Help (--help) via argparse (native)
"""

import requests
import socket
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
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# IP-API.com endpoint (free, no key required)
IP_API_URL = "http://ip-api.com/json/{}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query"

# Optional: IPinfo.io (requires token for high volume, but free tier available)
# IPINFO_URL = "https://ipinfo.io/{}/json?token=YOUR_TOKEN_HERE"

console = Console()


# ================== CORE FUNCTION ==================
def resolve_domain_to_ip(target: str, debug: bool = False):
    """Resolve domain to IP address"""
    try:
        if debug:
            console.print(f"[DEBUG] Resolving {target}...")
        ip = socket.gethostbyname(target)
        if debug:
            console.print(f"[DEBUG] Resolved to {ip}")
        return ip
    except Exception as e:
        if debug:
            console.print(f"[DEBUG] DNS resolution failed: {e}")
        return None


def get_geoip_data_ipapi(ip: str, debug: bool = False):
    """Get GeoIP data from ip-api.com"""
    url = IP_API_URL.format(ip)

    if debug:
        console.print(f"[DEBUG] Querying: {url}")

    try:
        response = requests.get(url, timeout=10)
        if debug:
            console.print(f"[DEBUG] Status Code: {response.status_code}")

        response.raise_for_status()
        data = response.json()

        if debug:
            console.print(f"[DEBUG] Raw Response: {data}")

        if data.get("status") == "success":
            return {
                "source": "ip-api.com",
                "ip": data.get("query", ip),
                "country": data.get("country", "N/A"),
                "region": data.get("regionName", "N/A"),
                "city": data.get("city", "N/A"),
                "zip": data.get("zip", "N/A"),
                "lat": data.get("lat", "N/A"),
                "lon": data.get("lon", "N/A"),
                "timezone": data.get("timezone", "N/A"),
                "isp": data.get("isp", "N/A"),
                "org": data.get("org", "N/A"),
                "asn": data.get("as", "N/A"),
                "error": None
            }
        else:
            return {
                "source": "ip-api.com",
                "ip": ip,
                "error": data.get("message", "Unknown error")
            }

    except Exception as e:
        if debug:
            console.print(f"[DEBUG] API request failed: {e}")
        return {
            "source": "ip-api.com",
            "ip": ip,
            "error": f"Request failed: {type(e).__name__}: {e}"
        }


# Optional: Uncomment and configure if you want to use ipinfo.io
# def get_geoip_data_ipinfo(ip: str, token: str = None, debug: bool = False):
#     """Get GeoIP data from ipinfo.io"""
#     base_url = "https://ipinfo.io/{}/json"
#     if token:
#         base_url += f"?token={token}"
#     url = base_url.format(ip)
#
#     if debug:
#         console.print(f"[DEBUG] Querying ipinfo.io: {url}")
#
#     try:
#         response = requests.get(url, timeout=10)
#         response.raise_for_status()
#         data = response.json()
#
#         if debug:
#             console.print(f"[DEBUG] ipinfo.io Response: {data}")
#
#         return {
#             "source": "ipinfo.io",
#             "ip": data.get("ip", ip),
#             "country": data.get("country", "N/A"),
#             "region": data.get("region", "N/A"),
#             "city": data.get("city", "N/A"),
#             "zip": data.get("postal", "N/A"),
#             "lat": data.get("loc", "N/A").split(',')[0] if data.get("loc") else "N/A",
#             "lon": data.get("loc", "N/A").split(',')[1] if data.get("loc") else "N/A",
#             "timezone": data.get("timezone", "N/A"),
#             "isp": data.get("org", "N/A"),
#             "asn": data.get("asn", {}).get("asn", "N/A") if isinstance(data.get("asn"), dict) else data.get("asn", "N/A"),
#             "error": None
#         }
#     except Exception as e:
#         if debug:
#             console.print(f"[DEBUG] ipinfo.io request failed: {e}")
#         return {
#             "source": "ipinfo.io",
#             "ip": ip,
#             "error": f"Request failed: {type(e).__name__}: {e}"
#         }


def get_geoip(target: str, debug: bool = False):
    """Main function to get GeoIP data for a target"""
    # Resolve if it's a domain
    if any(c.isalpha() for c in target) and not target.replace('.', '').isdigit():
        ip = resolve_domain_to_ip(target, debug)
        if not ip:
            return {
                "target": target,
                "ip": None,
                "error": "Could not resolve domain"
            }
    else:
        ip = target

    # Get GeoIP data
    result = get_geoip_data_ipapi(ip, debug)

    # You can add fallback logic here, e.g.:
    # if result.get("error") and not debug:
    #     result = get_geoip_data_ipinfo(ip, debug=debug)

    result["target"] = target
    return result


# ================== MAIN SCAN FUNCTION ==================
def scan_targets(targets: list, debug: bool):
    """Scan multiple targets for GeoIP data"""
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Scanning targets...", total=len(targets))

        for target in targets:
            progress.update(task, description=f"[cyan]Scanning {target}...")
            result = get_geoip(target, debug)
            results.append(result)
            progress.advance(task)

    return results


# ================== UTILS ==================
def display_results(results: list):
    """Display results in rich tables and panels"""
    for result in results:
        target = result["target"]
        error = result.get("error")

        if error:
            console.print(Panel(f"❌ [bold]{target}[/bold]: {error}", style="red"))
        else:
            table = Table(title=f"🌍 GeoIP Information for {target} ({result['ip']})", show_lines=True)
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            fields = [
                ("IP Address", "ip"),
                ("Country", "country"),
                ("Region", "region"),
                ("City", "city"),
                ("ZIP Code", "zip"),
                ("Latitude", "lat"),
                ("Longitude", "lon"),
                ("Timezone", "timezone"),
                ("ISP", "isp"),
                ("Organization", "org"),
                ("ASN", "asn"),
                ("Data Source", "source")
            ]

            for label, key in fields:
                table.add_row(label, str(result.get(key, "N/A")))

            console.print(table)


def save_results(results: list, prefix: str = "geoip", results_dir: Path = DEFAULT_RESULTS_DIR):
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
            fieldnames = ["target", "ip", "country", "region", "city", "zip", "lat", "lon", "timezone", "isp", "org", "asn", "source", "error"]
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "target": r.get("target", ""),
                    "ip": r.get("ip", ""),
                    "country": r.get("country", ""),
                    "region": r.get("region", ""),
                    "city": r.get("city", ""),
                    "zip": r.get("zip", ""),
                    "lat": r.get("lat", ""),
                    "lon": r.get("lon", ""),
                    "timezone": r.get("timezone", ""),
                    "isp": r.get("isp", ""),
                    "org": r.get("org", ""),
                    "asn": r.get("asn", ""),
                    "source": r.get("source", ""),
                    "error": r.get("error", "")
                })
    except Exception as e:
        console.print(f"[red]Failed to save CSV results: {e}[/red]")
        csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT GeoIP Scanner — Location & Network Info from IP/Domain",
        epilog="Examples:\n"
               "  python3 geoip-scan.py --target google.com\n"
               "  python3 geoip-scan.py --target 8.8.8.8 --target 1.1.1.1 --debug"
    )
    parser.add_argument("--target", "-t", action="append", help="IP address or domain to scan (can be used multiple times)")
    parser.add_argument("--file", "-f", help="File containing targets (one per line)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows API requests and responses)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT GeoIP Scanner[/bold green]")

    # If no target provided, fallback to interactive mode
    if not args.target and not args.file:
        target = Prompt.ask("[bold cyan]Enter an IP address or domain")
        if not target:
            console.print("[red]No target provided. Exiting.[/red]")
            return
        targets = [target.strip()]
        debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)
    else:
        # CLI mode
        debug = args.debug
        targets = []

        if args.target:
            targets.extend([t.strip() for t in args.target])

        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    file_targets = [line.strip() for line in f if line.strip()]
                    targets.extend(file_targets)
                    console.print(f"[cyan]Loaded {len(file_targets)} targets from {args.file}[/cyan]")
            except Exception as e:
                console.print(f"[red]Error reading targets file: {e}[/red]")
                return

        if not targets:
            console.print("[red]No targets provided. Exiting.[/red]")
            return

    # Run scan
    console.print(f"\n[bold yellow]🔍 Scanning [bold green]{len(targets)}[/bold green] targets...[/bold yellow]\n")

    start_time = time.time()
    results = scan_targets(targets, debug)
    duration = time.time() - start_time

    # Display results
    display_results(results)
    console.print(f"\n[bold green]✅ Scan finished in {duration:.1f}s.[/bold green]")

    # Save results
    json_path, csv_path = save_results(results, prefix="geoip_scan")
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
