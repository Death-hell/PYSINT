#!/usr/bin/env python3
"""
Traceroute-scan.py - Advanced Network Traceroute Scanner for PYSINT Suite
Author: YourNameHere
License: MIT
Repository: ~/PYSINT

Features:
- Traceroute with ICMP (root) or UDP (no-root) mode
- Resolves hostnames and fetches ASN/Org info via ipinfo.io
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--target, --noroot, --max-hops, etc.) + Interactive fallback
- Debug mode (--debug) to log socket operations and API calls
- Help (--help) via argparse (native)
"""

import asyncio
import socket
import time
import aiohttp
import json
import csv
import os
import argparse
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

# ================== DEFAULTS ==================
DEFAULT_MAX_HOPS = 30
DEFAULT_TIMEOUT = 2.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
IPINFO_URL = "https://ipinfo.io/{}/json"

# Ensure results directory exists
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
async def get_asn_info(ip: str, debug: bool = False) -> str:
    """Fetch ASN/Org info for an IP using ipinfo.io"""
    if ip == "*" or not ip or ip.startswith("Error:"):
        return ""

    url = IPINFO_URL.format(ip)
    if debug:
        console.print(f"[DEBUG] Fetching ASN for {ip} from {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    org = data.get("org", "N/A")
                    if debug:
                        console.print(f"[DEBUG] ASN for {ip}: {org}")
                    return org
                else:
                    if debug:
                        console.print(f"[DEBUG] ipinfo.io returned {resp.status} for {ip}")
                    return "N/A"
    except Exception as e:
        if debug:
            console.print(f"[DEBUG] Error fetching ASN for {ip}: {e}")
        return f"Error: {type(e).__name__}"


async def traceroute_host(
    host: str,
    noroot: bool = False,
    max_hops: int = DEFAULT_MAX_HOPS,
    timeout: float = DEFAULT_TIMEOUT,
    debug: bool = False
):
    """Perform traceroute to the given host"""
    try:
        dest_ip = socket.gethostbyname(host)
        if debug:
            console.print(f"[DEBUG] Resolved {host} to {dest_ip}")
    except socket.gaierror as e:
        console.print(f"[bold red]Cannot resolve host {host}: {e}[/bold red]")
        return []

    results = []
    console.print(f"[bold cyan]🚀 Advanced Traceroute to {host} ({dest_ip})[/bold cyan]\n")

    port = 33434
    ttl = 1

    while ttl <= max_hops:
        hop_ip = "*"
        rtt = "Timeout"
        asn_info = ""
        hop_name = ""

        try:
            start = time.time()

            if noroot:
                # UDP mode (no root required)
                if debug:
                    console.print(f"[DEBUG] Hop {ttl}: Sending UDP packet (port {port}) with TTL={ttl}")
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
                    send_socket.settimeout(timeout)
                    send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
                    send_socket.sendto(b'', (host, port))
                    try:
                        _, curr_addr = send_socket.recvfrom(512)
                        hop_ip = curr_addr[0]
                        rtt = round((time.time() - start) * 1000, 2)
                        if debug:
                            console.print(f"[DEBUG] Received reply from {hop_ip} in {rtt}ms")
                    except socket.timeout:
                        hop_ip = "*"
                        if debug:
                            console.print(f"[DEBUG] Hop {ttl}: Timeout")
            else:
                # ICMP raw mode (requires root)
                if debug:
                    console.print(f"[DEBUG] Hop {ttl}: Sending ICMP packet with TTL={ttl}")
                recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
                recv_socket.settimeout(timeout)
                send_socket.sendto(b'', (host, port))

                try:
                    _, curr_addr = recv_socket.recvfrom(512)
                    hop_ip = curr_addr[0]
                    rtt = round((time.time() - start) * 1000, 2)
                    if debug:
                        console.print(f"[DEBUG] Received reply from {hop_ip} in {rtt}ms")
                except socket.timeout:
                    hop_ip = "*"
                    if debug:
                        console.print(f"[DEBUG] Hop {ttl}: Timeout")
                finally:
                    send_socket.close()
                    recv_socket.close()

            # Resolve hostname and ASN if we got an IP
            if hop_ip != "*":
                try:
                    hop_name = socket.gethostbyaddr(hop_ip)[0]
                    if debug:
                        console.print(f"[DEBUG] Resolved {hop_ip} to {hop_name}")
                except Exception as e:
                    hop_name = hop_ip
                    if debug:
                        console.print(f"[DEBUG] Could not resolve hostname for {hop_ip}: {e}")

                asn_info = await get_asn_info(hop_ip, debug)
                hop_display = f"{hop_name} ({hop_ip})" if hop_name != hop_ip else hop_ip
            else:
                hop_display = hop_ip

        except Exception as e:
            hop_display = f"Error: {e}"
            if debug:
                console.print(f"[DEBUG] Exception at hop {ttl}: {e}")

        results.append({
            "hop": ttl,
            "ip": hop_display,
            "rtt_ms": rtt,
            "asn": asn_info
        })

        # Stop if we reached destination
        if dest_ip in str(hop_display):
            if debug:
                console.print(f"[DEBUG] Reached destination {dest_ip} at hop {ttl}. Stopping.")
            break

        ttl += 1

    return results


# ================== UTILS ==================
def print_results(results: list):
    """Pretty print results with rich table"""
    table = Table(title="Traceroute Results", show_lines=True)
    table.add_column("Hop", style="yellow", justify="right")
    table.add_column("IP / Hostname", style="cyan", no_wrap=False)
    table.add_column("RTT (ms)", style="magenta", justify="right")
    table.add_column("ASN / Org", style="green")

    for r in results:
        table.add_row(
            str(r["hop"]),
            r["ip"],
            str(r["rtt_ms"]),
            r["asn"]
        )

    console.print(table)


def save_results(results: list, prefix="traceroute", results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save results to JSON and CSV in ~/PYSINT/results"""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = results_dir / f"{prefix}_{ts}.json"
    csv_path = results_dir / f"{prefix}_{ts}.csv"

    # Save JSON
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"[red]Failed to save JSON: {e}[/red]")
        json_path = None

    # Save CSV
    if results:
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                fieldnames = ["hop", "ip", "rtt_ms", "asn"]
                writer = csv.DictWriter(cf, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        except Exception as e:
            console.print(f"[red]Failed to save CSV: {e}[/red]")
            csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Traceroute Scanner — Advanced Network Path Analyzer",
        epilog="Example: python3 Traceroute-scan.py --target google.com --noroot --max-hops 20 --debug"
    )
    parser.add_argument("--target", "-t", help="Target host (domain or IP)")
    parser.add_argument("--noroot", action="store_true", help="Use UDP mode (no root required, less accurate)")
    parser.add_argument("--max-hops", type=int, default=DEFAULT_MAX_HOPS, help=f"Max number of hops (default: {DEFAULT_MAX_HOPS})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"Timeout per hop in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows socket operations and API calls)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
async def main():
    args = parse_args()

    console.rule("[bold cyan]PYSINT Traceroute Scanner[/bold cyan]")

    # If no target provided, fallback to interactive mode
    if not args.target:
        target = Prompt.ask("[bold cyan]Enter the target host (domain or IP)")
        if not target:
            console.print("[red]No target provided. Exiting.[/red]")
            return
        noroot = Prompt.ask("[bold cyan]Use UDP mode (no root required)?", choices=["y", "n"], default="n") == "y"
        max_hops_input = Prompt.ask(f"[bold cyan]Max hops (default: {DEFAULT_MAX_HOPS})", default=str(DEFAULT_MAX_HOPS))
        max_hops = int(max_hops_input) if max_hops_input.isdigit() else DEFAULT_MAX_HOPS
        timeout_input = Prompt.ask(f"[bold cyan]Timeout per hop in seconds (default: {DEFAULT_TIMEOUT})", default=str(DEFAULT_TIMEOUT))
        timeout = float(timeout_input) if timeout_input.replace('.', '', 1).isdigit() else DEFAULT_TIMEOUT
        debug = Prompt.ask("[bold cyan]Enable debug mode?", choices=["y", "n"], default="n") == "y"
    else:
        # CLI mode
        target = args.target
        noroot = args.noroot
        max_hops = args.max_hops
        timeout = args.timeout
        debug = args.debug

    # Run traceroute
    start_time = time.time()
    results = await traceroute_host(target, noroot=noroot, max_hops=max_hops, timeout=timeout, debug=debug)
    duration = time.time() - start_time

    if results:
        print_results(results)
        json_path, csv_path = save_results(results)
        console.print(f"\n[green]✅ Traceroute completed in {duration:.1f}s.[/green]")
        saved = []
        if json_path:
            saved.append(str(json_path))
        if csv_path:
            saved.append(str(csv_path))
        if saved:
            console.print(f"[cyan]💾 Results saved to:[/cyan] {', '.join(saved)}")
        else:
            console.print("[yellow]⚠️  No results were saved (I/O error).[/yellow]")
    else:
        console.print("[red]❌ No results to display.[/red]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]🛑 Traceroute interrupted by user.[/red]")
    except PermissionError:
        console.print("[red]❌ Permission denied. Try running with sudo for ICMP mode, or use --noroot.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
