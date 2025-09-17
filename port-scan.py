#!/usr/bin/env python3
"""
port-scan.py - TCP Port Scanner for PYSINT Suite
Author: Mael
License: MIT
Repository: ~/PyToolKit

Features:
- Scan TCP ports on a host (IP or domain)
- Default scan of common ports, or custom range
- Concurrent scanning with thread pool
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--host, --ports, etc.) + Interactive fallback
- Debug mode (--debug) to log connection attempts and errors
- Help (--help) via argparse (native)
"""

import socket
import json
import csv
import os
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# ================== DEFAULTS ==================
DEFAULT_COMMON_PORTS = {
    20: "FTP-Data", 21: "FTP", 22: "SSH", 23: "Telnet",
    25: "SMTP", 53: "DNS", 67: "DHCP", 68: "DHCP", 69: "TFTP",
    80: "HTTP", 110: "POP3", 111: "RPCBind", 123: "NTP",
    135: "MSRPC", 139: "NetBIOS", 143: "IMAP", 161: "SNMP",
    194: "IRC", 443: "HTTPS", 445: "SMB", 465: "SMTPS",
    587: "SMTP-Alt", 993: "IMAPS", 995: "POP3S", 1433: "MSSQL",
    1521: "Oracle", 1723: "PPTP", 2049: "NFS", 3306: "MySQL",
    3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 9000: "Webmin"
}

DEFAULT_MAX_THREADS = 100
DEFAULT_TIMEOUT = 1.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
def scan_port(host: str, port: int, timeout: float, debug: bool = False):
    """Scan a single TCP port"""
    try:
        if debug:
            console.print(f"[DEBUG] Scanning {host}:{port}...")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))

            if result == 0:
                service = DEFAULT_COMMON_PORTS.get(port, "Unknown")
                if debug:
                    console.print(f"[DEBUG] Port {port} is OPEN (service: {service})")
                return {
                    "port": port,
                    "service": service,
                    "status": "open",
                    "error": None
                }
            else:
                if debug:
                    console.print(f"[DEBUG] Port {port} is CLOSED (code: {result})")
                return {
                    "port": port,
                    "service": DEFAULT_COMMON_PORTS.get(port, "Unknown"),
                    "status": "closed",
                    "error": None
                }

    except socket.timeout:
        if debug:
            console.print(f"[DEBUG] Port {port} timed out")
        return {
            "port": port,
            "service": DEFAULT_COMMON_PORTS.get(port, "Unknown"),
            "status": "timeout",
            "error": "timeout"
        }
    except Exception as e:
        if debug:
            console.print(f"[DEBUG] Error scanning {host}:{port}: {e}")
        return {
            "port": port,
            "service": DEFAULT_COMMON_PORTS.get(port, "Unknown"),
            "status": "error",
            "error": str(e)
        }


# ================== MAIN SCAN FUNCTION ==================
def port_scan(host: str, ports: list, max_threads: int, timeout: float, debug: bool):
    """Scan multiple ports on a host"""
    open_ports = []
    all_results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} ports"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Scanning {host}...", total=len(ports))

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Submit all tasks
            futures = {executor.submit(scan_port, host, port, timeout, debug): port for port in ports}

            # Process completed tasks
            for future in as_completed(futures):
                result = future.result()
                all_results.append(result)
                if result["status"] == "open":
                    open_ports.append(result)
                progress.advance(task)

    return open_ports, all_results


# ================== UTILS ==================
def parse_port_range(port_range: str):
    """Parse port range string (e.g., "1-1000" or "80,443,8080")"""
    ports = []
    try:
        if '-' in port_range:
            start, end = map(int, port_range.split('-'))
            ports = list(range(start, end + 1))
        elif ',' in port_range:
            ports = [int(p.strip()) for p in port_range.split(',') if p.strip().isdigit()]
        else:
            # Single port
            ports = [int(port_range)]
    except Exception as e:
        console.print(f"[red]Error parsing port range '{port_range}': {e}[/red]")
        return []
    return ports


def save_results(results: list, host: str, prefix: str = "port_scan", results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save results as JSON and CSV with timestamp"""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_host = host.replace('.', '_').replace(':', '_')
    json_path = results_dir / f"{prefix}_{safe_host}_{ts}.json"
    csv_path = results_dir / f"{prefix}_{safe_host}_{ts}.csv"

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
                fieldnames = ["port", "service", "status", "error"]
                writer = csv.DictWriter(cf, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    writer.writerow({
                        "port": r.get("port", ""),
                        "service": r.get("service", ""),
                        "status": r.get("status", ""),
                        "error": r.get("error", "")
                    })
        except Exception as e:
            console.print(f"[red]Failed to save CSV results: {e}[/red]")
            csv_path = None

    return json_path, csv_path


def display_results(open_ports: list, host: str):
    """Display results in rich table"""
    if open_ports:
        table = Table(title=f"✅ Open Ports Found on {host}", show_lines=True)
        table.add_column("Port", style="cyan", justify="right")
        table.add_column("Service", style="yellow")
        table.add_column("Status", style="green")

        for item in open_ports:
            table.add_row(
                str(item["port"]),
                item["service"],
                item["status"]
            )

        console.print(table)
        console.print(f"\n[bold green]✅ Found [bold yellow]{len(open_ports)}[/bold yellow] open ports.[/bold green]")
    else:
        console.print(f"\n[bold yellow]✅ Scan completed. No open ports found on {host}.[/bold yellow]")


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Port Scanner — TCP Port Discovery Tool",
        epilog="Examples:\n"
               "  python3 port-scan.py --host google.com\n"
               "  python3 port-scan.py --host 192.168.1.1 --ports 1-1000 --timeout 2.0 --debug"
    )
    parser.add_argument("--host", "-H", help="Target host (IP or domain)")
    parser.add_argument("--ports", "-p", help="Port range (e.g., '1-1000') or comma-separated list (e.g., '80,443,8080'). Default: common ports")
    parser.add_argument("--threads", "-t", type=int, default=DEFAULT_MAX_THREADS, help=f"Max concurrent threads (default: {DEFAULT_MAX_THREADS})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"Socket timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows connection attempts and errors)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT Port Scanner[/bold green]")

    # If no host provided, fallback to interactive mode
    if not args.host:
        host = Prompt.ask("[bold cyan]Enter the website or IP to scan")
        if not host:
            console.print("[red]No host provided. Exiting.[/red]")
            return

        ports_input = Prompt.ask("[bold yellow]Enter port range (e.g., '1-1000') or comma-separated list (e.g., '80,443'). Leave blank for common ports", default="")
        if ports_input:
            ports = parse_port_range(ports_input)
            if not ports:
                console.print("[yellow]Invalid port range. Using common ports.[/yellow]")
                ports = list(DEFAULT_COMMON_PORTS.keys())
        else:
            ports = list(DEFAULT_COMMON_PORTS.keys())

        threads_input = Prompt.ask(f"[bold yellow]Max concurrent threads (default: {DEFAULT_MAX_THREADS})", default=str(DEFAULT_MAX_THREADS))
        max_threads = int(threads_input) if threads_input.isdigit() else DEFAULT_MAX_THREADS

        timeout_input = Prompt.ask(f"[bold yellow]Socket timeout in seconds (default: {DEFAULT_TIMEOUT})", default=str(DEFAULT_TIMEOUT))
        timeout = float(timeout_input) if timeout_input.replace('.', '', 1).isdigit() else DEFAULT_TIMEOUT

        debug = Confirm.ask("[bold yellow]Enable debug mode?", default=False)

    else:
        # CLI mode
        host = args.host
        max_threads = args.threads
        timeout = args.timeout
        debug = args.debug

        if args.ports:
            ports = parse_port_range(args.ports)
            if not ports:
                console.print("[red]Invalid port range. Exiting.[/red]")
                return
        else:
            ports = list(DEFAULT_COMMON_PORTS.keys())

    # Resolve domain to IP if needed
    try:
        ip = socket.gethostbyname(host)
        if host != ip:
            console.print(f"[cyan]Resolved {host} to {ip}[/cyan]")
        scan_target = ip
    except socket.gaierror as e:
        console.print(f"[red]Error: Could not resolve host {host}: {e}[/red]")
        return
    except Exception as e:
        console.print(f"[red]Unexpected error resolving host: {e}[/red]")
        return

    # Run scan
    console.print(f"\n[bold yellow]🔍 Scanning [bold green]{host}[/bold green] ({scan_target}) for [bold green]{len(ports)}[/bold green] ports...[/bold yellow]\n")

    start_time = time.time()
    open_ports, all_results = port_scan(scan_target, ports, max_threads, timeout, debug)
    duration = time.time() - start_time

    # Display results
    display_results(open_ports, host)
    console.print(f"\n[bold green]✅ Scan finished in {duration:.1f}s. Scanned {len(ports)} ports.[/bold green]")

    # Save results
    json_path, csv_path = save_results(all_results, host)
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
