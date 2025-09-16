#!/usr/bin/env python3
"""
headers.py - HTTP Headers Analyzer for PYSINT Suite
Author: YourNameHere
License: MIT
Repository: ~/PYSINT

Features:
- Fetch and display HTTP headers from URLs
- Analyze security headers (CSP, HSTS, XSS Protection, etc.)
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--url, --file, etc.) + Interactive fallback
- Debug mode (--debug) to show request details, redirects, timing
- Help (--help) via argparse (native)
"""

import httpx
import json
import csv
import os
import time
import argparse
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

# ================== DEFAULTS ==================
DEFAULT_TIMEOUT = 5.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== SECURITY HEADERS ANALYSIS ==================
SECURITY_HEADERS = {
    "strict-transport-security": {
        "name": "HSTS (Strict-Transport-Security)",
        "description": "Enforces HTTPS connections",
        "severity": "high",
        "recommendation": "Add HSTS header with max-age=31536000; includeSubDomains"
    },
    "content-security-policy": {
        "name": "CSP (Content-Security-Policy)",
        "description": "Prevents XSS and code injection attacks",
        "severity": "high",
        "recommendation": "Implement CSP with appropriate directives"
    },
    "x-content-type-options": {
        "name": "X-Content-Type-Options",
        "description": "Prevents MIME type sniffing",
        "severity": "medium",
        "recommendation": "Set to 'nosniff'"
    },
    "x-frame-options": {
        "name": "X-Frame-Options",
        "description": "Prevents clickjacking attacks",
        "severity": "medium",
        "recommendation": "Set to 'DENY' or 'SAMEORIGIN'"
    },
    "x-xss-protection": {
        "name": "X-XSS-Protection",
        "description": "Enables XSS filtering in browsers",
        "severity": "low",
        "recommendation": "Set to '1; mode=block' (deprecated but still used)"
    },
    "referrer-policy": {
        "name": "Referrer-Policy",
        "description": "Controls referrer information sent with requests",
        "severity": "medium",
        "recommendation": "Set to 'strict-origin-when-cross-origin' or stricter"
    },
    "permissions-policy": {
        "name": "Permissions-Policy",
        "description": "Controls browser features and APIs",
        "severity": "medium",
        "recommendation": "Restrict unnecessary features"
    },
    "cross-origin-embedder-policy": {
        "name": "COEP",
        "description": "Prevents loading cross-origin resources without explicit permission",
        "severity": "high",
        "recommendation": "Set to 'require-corp' for enhanced security"
    },
    "cross-origin-opener-policy": {
        "name": "COOP",
        "description": "Prevents cross-origin window references",
        "severity": "high",
        "recommendation": "Set to 'same-origin' for isolation"
    },
    "cross-origin-resource-policy": {
        "name": "CORP",
        "description": "Prevents cross-origin resource loading",
        "severity": "high",
        "recommendation": "Set to 'same-origin' or 'same-site'"
    }
}


def analyze_security_headers(headers: dict):
    """Analyze security headers and return recommendations"""
    missing = []
    present = []

    for header_key, info in SECURITY_HEADERS.items():
        if header_key in [h.lower() for h in headers.keys()]:
            present.append({
                "header": info["name"],
                "status": "✅ Present",
                "description": info["description"]
            })
        else:
            missing.append({
                "header": info["name"],
                "status": "❌ Missing",
                "description": info["description"],
                "recommendation": info["recommendation"],
                "severity": info["severity"]
            })

    return present, missing


# ================== CORE FUNCTION ==================
def scan_headers_url(url: str, debug: bool = False):
    """Scan HTTP headers for a single URL"""
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        if debug:
            console.print(f"[DEBUG] Fetching headers from: {url}")

        with httpx.Client(follow_redirects=False, timeout=DEFAULT_TIMEOUT) as client:  # We'll handle redirects manually
            start_time = time.time()
            response = client.get(url)
            duration = time.time() - start_time

            # Follow redirects manually to show each step if debug is enabled
            redirect_chain = []
            current_response = response
            while current_response.status_code in (301, 302, 303, 307, 308) and 'location' in current_response.headers:
                redirect_chain.append({
                    "url": str(current_response.url),
                    "status_code": current_response.status_code,
                    "location": current_response.headers['location']
                })
                if debug:
                    console.print(f"[DEBUG] Redirect: {current_response.status_code} from {current_response.url} to {current_response.headers['location']}")
                try:
                    current_response = client.get(current_response.headers['location'])
                except:
                    break

            final_response = current_response
            if debug:
                console.print(f"[DEBUG] Final URL: {final_response.url}")
                console.print(f"[DEBUG] Status: {final_response.status_code} | Duration: {duration:.2f}s")
                console.print(f"[DEBUG] Encoding: {final_response.encoding}")

            headers_dict = dict(final_response.headers)

            # Analyze security headers
            present_headers, missing_headers = analyze_security_headers(headers_dict)

            result = {
                "original_url": url,
                "final_url": str(final_response.url),
                "status_code": final_response.status_code,
                "duration_seconds": duration,
                "headers": headers_dict,
                "security_analysis": {
                    "present": present_headers,
                    "missing": missing_headers
                },
                "redirect_chain": redirect_chain,
                "error": None
            }

            return result

    except httpx.RequestError as e:
        if debug:
            console.print(f"[DEBUG] Request error: {e}")
        return {
            "original_url": url,
            "error": f"RequestError: {e}"
        }
    except Exception as e:
        if debug:
            console.print(f"[DEBUG] Unexpected error: {e}")
        return {
            "original_url": url,
            "error": f"{type(e).__name__}: {e}"
        }


# ================== MAIN SCAN FUNCTION ==================
def scan_multiple_urls(urls: list, debug: bool):
    """Scan headers for multiple URLs"""
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Scanning headers...", total=len(urls))

        for url in urls:
            progress.update(task, description=f"[cyan]Scanning {url}...")
            result = scan_headers_url(url, debug)
            results.append(result)
            progress.advance(task)

    return results


# ================== UTILS ==================
def display_results(results: list):
    """Display results in rich tables and panels"""
    for result in results:
        original_url = result["original_url"]
        error = result.get("error")

        if error:
            console.print(Panel(f"❌ [bold]{original_url}[/bold]: {error}", style="red"))
            continue

        final_url = result["final_url"]
        status_code = result["status_code"]
        duration = result["duration_seconds"]

        # Show redirect info if any
        if original_url != final_url:
            redirect_info = f" (redirected from {original_url})"
        else:
            redirect_info = ""

        panel_title = f"🔍 HTTP Headers for {final_url}{redirect_info}"
        panel_subtitle = f"Status: {status_code} | Response Time: {duration:.2f}s"
        panel = Panel(f"[bold green]{panel_title}[/bold green]\n[dim]{panel_subtitle}[/dim]", style="green")
        console.print(panel)

        # Display headers table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Header", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow")

        for header, value in result["headers"].items():
            table.add_row(header, value)

        console.print(table)

        # Display security analysis
        security_analysis = result["security_analysis"]
        present = security_analysis["present"]
        missing = security_analysis["missing"]

        if missing:
            console.print("\n[bold red]⚠️  Security Recommendations:[/bold red]")
            severity_colors = {"high": "red", "medium": "yellow", "low": "white"}
            for item in missing:
                color = severity_colors.get(item["severity"], "white")
                text = Text()
                text.append(f"• {item['header']} ", style=f"bold {color}")
                text.append(f"({item['severity'].upper()})\n", style=color)
                text.append(f"  Recommendation: {item['recommendation']}", style="dim")
                console.print(text)
        else:
            console.print("\n[bold green]✅ All critical security headers are present![/bold green]")

        console.print("")  # Empty line for spacing


def save_results(results: list, prefix: str = "headers", results_dir: Path = DEFAULT_RESULTS_DIR):
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
            fieldnames = ["url", "final_url", "status_code", "header_name", "header_value", "security_status", "severity", "recommendation"]
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                if result.get("error"):
                    writer.writerow({
                        "url": result["original_url"],
                        "final_url": "",
                        "status_code": "",
                        "header_name": "ERROR",
                        "header_value": result["error"],
                        "security_status": "",
                        "severity": "",
                        "recommendation": ""
                    })
                else:
                    # Write all headers
                    for header, value in result["headers"].items():
                        writer.writerow({
                            "url": result["original_url"],
                            "final_url": result["final_url"],
                            "status_code": result["status_code"],
                            "header_name": header,
                            "header_value": value,
                            "security_status": "",
                            "severity": "",
                            "recommendation": ""
                        })

                    # Write security recommendations
                    for item in result["security_analysis"]["missing"]:
                        writer.writerow({
                            "url": result["original_url"],
                            "final_url": result["final_url"],
                            "status_code": result["status_code"],
                            "header_name": item["header"],
                            "header_value": "MISSING",
                            "security_status": "MISSING",
                            "severity": item["severity"],
                            "recommendation": item["recommendation"]
                        })
    except Exception as e:
        console.print(f"[red]Failed to save CSV results: {e}[/red]")
        csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT HTTP Headers Scanner — Analyze Website Headers & Security",
        epilog="Examples:\n"
               "  python3 headers.py --url https://example.com\n"
               "  python3 headers.py --url https://site1.com --url https://site2.com --debug"
    )
    parser.add_argument("--url", "-u", action="append", help="URL(s) to scan headers for (can be used multiple times)")
    parser.add_argument("--file", "-f", help="File containing URLs (one per line)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows redirects, timing, encoding)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT HTTP Headers Scanner[/bold green]")

    # If no URL provided, fallback to interactive mode
    if not args.url and not args.file:
        url = Prompt.ask("[bold cyan]Enter the website (with http/https)")
        if not url:
            console.print("[red]No URL provided. Exiting.[/red]")
            return
        urls = [url.strip()]
        debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)
    else:
        # CLI mode
        debug = args.debug
        urls = []

        if args.url:
            urls.extend([u.strip() for u in args.url])

        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    file_urls = [line.strip() for line in f if line.strip()]
                    urls.extend(file_urls)
                    console.print(f"[cyan]Loaded {len(file_urls)} URLs from {args.file}[/cyan]")
            except Exception as e:
                console.print(f"[red]Error reading URL file: {e}[/red]")
                return

        if not urls:
            console.print("[red]No URLs provided. Exiting.[/red]")
            return

    # Run scan
    console.print(f"\n[bold yellow]🔍 Scanning headers for [bold green]{len(urls)}[/bold green] URLs...[/bold yellow]\n")

    start_time = time.time()
    results = scan_multiple_urls(urls, debug)
    duration = time.time() - start_time

    # Display results
    display_results(results)
    console.print(f"\n[bold green]✅ Scan finished in {duration:.1f}s.[/bold green]")

    # Save results
    json_path, csv_path = save_results(results, prefix="headers_scan")
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
