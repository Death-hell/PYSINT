#!/usr/bin/env python3
"""
ssl-info.py - SSL/TLS Certificate Analyzer for PYSINT Suite
Author: YourNameHere
License: MIT
Repository: ~/PYSINT

Features:
- Fetch and display SSL/TLS certificate information
- Check certificate validity, issuer, SANs, TLS version
- Warns about soon-to-expire certificates
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--domain, --port, etc.) + Interactive fallback
- Debug mode (--debug) to show raw certificate and connection details
- Help (--help) via argparse (native)
"""

import ssl
import socket
import json
import csv
import os
import time
import argparse
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# ================== DEFAULTS ==================
DEFAULT_PORT = 443
DEFAULT_TIMEOUT = 5.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
def get_ssl_info(domain: str, port: int = DEFAULT_PORT, debug: bool = False):
    """Get SSL/TLS certificate information for a domain"""
    context = ssl.create_default_context()

    try:
        if debug:
            console.print(f"[DEBUG] Connecting to {domain}:{port}...")

        with socket.create_connection((domain, port), timeout=DEFAULT_TIMEOUT) as sock:
            if debug:
                console.print(f"[DEBUG] Connected. Wrapping with SSL...")

            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                if debug:
                    console.print(f"[DEBUG] SSL handshake completed. TLS version: {ssock.version()}")

                cert = ssock.getpeercert()
                if debug:
                    console.print(f"[DEBUG] Raw certificate: {cert}")

                # Parse certificate fields
                subject = dict(x[0] for x in cert.get('subject', ())) if cert.get('subject') else {}
                issuer = dict(x[0] for x in cert.get('issuer', ())) if cert.get('issuer') else {}

                # Get dates
                not_before_str = cert.get('notBefore', '')
                not_after_str = cert.get('notAfter', '')

                not_before = datetime.strptime(not_before_str, "%b %d %H:%M:%S %Y %Z") if not_before_str else None
                not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z") if not_after_str else None

                # Calculate days until expiration
                days_until_expiration = None
                if not_after:
                    days_until_expiration = (not_after - datetime.utcnow()).days

                # Get SANs
                sans = cert.get('subjectAltName', ())
                san_list = [x[1] for x in sans] if sans else []

                # TLS version
                tls_version = ssock.version()

                result = {
                    "domain": domain,
                    "port": port,
                    "common_name": subject.get('commonName', ''),
                    "organization": subject.get('organizationName', ''),
                    "organizational_unit": subject.get('organizationalUnitName', ''),
                    "issuer_common_name": issuer.get('commonName', ''),
                    "issuer_organization": issuer.get('organizationName', ''),
                    "valid_from": not_before_str,
                    "valid_until": not_after_str,
                    "days_until_expiration": days_until_expiration,
                    "san_list": san_list,
                    "tls_version": tls_version,
                    "raw_cert": cert if debug else {},
                    "error": None
                }

                return result

    except socket.timeout:
        error_msg = f"Connection to {domain}:{port} timed out"
        if debug:
            console.print(f"[DEBUG] {error_msg}")
        return {
            "domain": domain,
            "port": port,
            "error": f"Timeout: {error_msg}"
        }
    except socket.gaierror as e:
        error_msg = f"Could not resolve host {domain}: {e}"
        if debug:
            console.print(f"[DEBUG] {error_msg}")
        return {
            "domain": domain,
            "port": port,
            "error": f"DNS Error: {error_msg}"
        }
    except ssl.SSLError as e:
        error_msg = f"SSL Error: {e}"
        if debug:
            console.print(f"[DEBUG] {error_msg}")
        return {
            "domain": domain,
            "port": port,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        if debug:
            console.print(f"[DEBUG] {error_msg}")
        return {
            "domain": domain,
            "port": port,
            "error": error_msg
        }


# ================== MAIN SCAN FUNCTION ==================
def scan_domains(domains: list, port: int, debug: bool):
    """Scan SSL/TLS info for multiple domains"""
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Scanning SSL/TLS...", total=len(domains))

        for domain in domains:
            progress.update(task, description=f"[cyan]Scanning {domain}:{port}...")
            result = get_ssl_info(domain, port, debug)
            results.append(result)
            progress.advance(task)

    return results


# ================== UTILS ==================
def display_results(results: list):
    """Display results in rich tables and panels"""
    for result in results:
        domain = result["domain"]
        port = result["port"]
        error = result.get("error")

        if error:
            console.print(Panel(f"❌ [bold]{domain}:{port}[/bold]: {error}", style="red"))
            continue

        # Check expiration
        days_until_expiration = result["days_until_expiration"]
        if days_until_expiration is not None:
            if days_until_expiration < 0:
                expiration_status = Text("EXPIRED", style="bold red")
            elif days_until_expiration < 30:
                expiration_status = Text(f"EXPIRES IN {days_until_expiration} DAYS", style="bold yellow")
            else:
                expiration_status = Text(f"VALID FOR {days_until_expiration} MORE DAYS", style="bold green")
        else:
            expiration_status = Text("UNKNOWN", style="dim")

        # Create table
        table = Table(title=f"🔒 SSL/TLS Certificate Info for {domain}:{port}", header_style="bold magenta", show_lines=True)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow")

        fields = [
            ("Common Name", result["common_name"]),
            ("Organization", result["organization"]),
            ("Organizational Unit", result["organizational_unit"]),
            ("Issuer (Common Name)", result["issuer_common_name"]),
            ("Issuer (Organization)", result["issuer_organization"]),
            ("Valid From", result["valid_from"]),
            ("Valid Until", result["valid_until"]),
            ("Expiration Status", expiration_status),
            ("TLS Version", result["tls_version"]),
            ("Subject Alternative Names", ", ".join(result["san_list"]) if result["san_list"] else "-"),
        ]

        for field_name, field_value in fields:
            if isinstance(field_value, Text):
                table.add_row(field_name, field_value)
            else:
                table.add_row(field_name, str(field_value))

        console.print(table)
        console.print("")  # Empty line for spacing


def save_results(results: list, prefix: str = "ssl_scan", results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save results as JSON and CSV with timestamp"""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = results_dir / f"{prefix}_{ts}.json"
    csv_path = results_dir / f"{prefix}_{ts}.csv"

    # Save JSON
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        console.print(f"[red]Failed to save JSON results: {e}[/red]")
        json_path = None

    # Save CSV
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            fieldnames = [
                "domain", "port", "common_name", "organization", "organizational_unit",
                "issuer_common_name", "issuer_organization", "valid_from", "valid_until",
                "days_until_expiration", "tls_version", "san_list", "error"
            ]
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                row = r.copy()
                # Convert list to string for CSV
                if isinstance(row.get("san_list"), list):
                    row["san_list"] = "; ".join(row["san_list"])
                writer.writerow(row)
    except Exception as e:
        console.print(f"[red]Failed to save CSV results: {e}[/red]")
        csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT SSL/TLS Scanner — Certificate Information Tool",
        epilog="Examples:\n"
               "  python3 ssl-info.py --domain google.com\n"
               "  python3 ssl-info.py --domain github.com --port 443 --debug"
    )
    parser.add_argument("--domain", "-d", action="append", help="Domain(s) to scan SSL/TLS info for (can be used multiple times)")
    parser.add_argument("--file", "-f", help="File containing domains (one per line)")
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT, help=f"Port to connect to (default: {DEFAULT_PORT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows raw certificate and connection details)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT SSL/TLS Scanner[/bold green]")

    # If no domain provided, fallback to interactive mode
    if not args.domain and not args.file:
        domain = Prompt.ask("[bold cyan]Enter the website domain (without https://)")
        if not domain:
            console.print("[red]No domain provided. Exiting.[/red]")
            return

        port_input = Prompt.ask(f"[bold cyan]Enter port (default: {DEFAULT_PORT})", default=str(DEFAULT_PORT))
        port = int(port_input) if port_input.isdigit() else DEFAULT_PORT
        debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)

        domains = [domain.strip()]
    else:
        # CLI mode
        debug = args.debug
        port = args.port
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
    console.print(f"\n[bold yellow]🔍 Scanning SSL/TLS for [bold green]{len(domains)}[/bold green] domains on port {port}...[/bold yellow]\n")

    start_time = time.time()
    results = scan_domains(domains, port, debug)
    duration = time.time() - start_time

    # Display results
    display_results(results)
    console.print(f"\n[bold green]✅ Scan finished in {duration:.1f}s.[/bold green]")

    # Save results
    json_path, csv_path = save_results(results, prefix="ssl_info")
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
