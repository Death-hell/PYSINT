#!/usr/bin/env python3
"""
tech-detector.py - Web Technology Detector for PYSINT Suite
Author: YourNameHere
License: MIT
Repository: ~/PYSINT

Features:
- Detect CMS, frameworks, JavaScript libraries, and servers from HTTP responses
- Uses HTML patterns and HTTP headers for detection
- Saves results to JSON/CSV in ~/PYSINT/results
- CLI mode (--url, --file, etc.) + Interactive fallback
- Debug mode (--debug) to show matched patterns and headers
- Help (--help) via argparse (native)
"""

import asyncio
import httpx
import re
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
DEFAULT_TIMEOUT = 5.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== TECH PATTERNS ==================
TECH_PATTERNS = {
    # CMS
    "WordPress": [r"wp-content", r"wp-includes", r"wordpress", r"wp-json", r"/wp-admin/"],
    "Joomla": [r"joomla", r"index.php\?option=", r"component", r"tmpl="],
    "Drupal": [r"drupal", r"sites/all", r"misc/drupal.js", r"core/misc/drupal.js"],
    "Magento": [r"magento", r"/skin/frontend/", r"mage-", r"varienForm"],
    "Shopify": [r"shopify", r"cdn.shopify.com", r"Shopify.theme", r"Shopify.currency"],
    "Wix": [r"wix", r"wix-code", r"wixapps", r"wixstatic.com"],
    "Squarespace": [r"squarespace", r"squarespace.com", r"SquarespaceAnalytics"],
    
    # Frameworks
    "Laravel": [r"laravel", r"/public/", r"laravel_session", r"X-Laravel"],
    "Django": [r"django", r"csrftoken", r"django_session", r"csrfmiddlewaretoken"],
    "Ruby on Rails": [r"rails", r"action_controller", r"X-Runtime"],
    "Express": [r"express", r"express-session", r"x-powered-by: express"],
    "Flask": [r"flask", r"flask-session", r"flask-wtf"],
    "Spring Boot": [r"spring", r"spring-boot", r"X-Application-Context"],
    
    # JavaScript Frameworks
    "React": [r"react", r"__reactinternal", r"data-reactroot", r"react-dom", r"react-router"],
    "Angular": [r"angular", r"ng-version", r"ng-app", r"@angular"],
    "Vue.js": [r"vue", r"v-cloak", r"v-bind", r"v-model", r"vue-router"],
    "Svelte": [r"svelte", r"sveltekit", r"data-sveltekit"],
    "Next.js": [r"_next", r"next-data", r"next-font", r"nextjs"],
    "Nuxt.js": [r"nuxt", r"_nuxt", r"nuxtjs"],
    "Gatsby": [r"gatsby", r"___gatsby", r"GATSBY_"],
    "jQuery": [r"jquery", r"jQuery", r"$(", r"$.ajax"],
    "Bootstrap": [r"bootstrap", r"navbar", r"btn-", r"col-md-", r"bootstrap.min.css"],
    "Tailwind CSS": [r"tailwind", r"sm:", r"md:", r"lg:", r"xl:", r"bg-", r"text-"],
    
    # Servers (will be detected via headers)
    "Nginx": [],
    "Apache": [],
    "IIS": [],
    "LiteSpeed": [],
    "Cloudflare": [],
    "Vercel": [],
    "Netlify": [],
    "GitHub Pages": [],
}

# Server header patterns
SERVER_PATTERNS = {
    "nginx": "Nginx",
    "apache": "Apache",
    "iis": "IIS",
    "litespeed": "LiteSpeed",
    "cloudflare": "Cloudflare",
    "vercel": "Vercel",
    "netlify": "Netlify",
    "github": "GitHub Pages",
    "heroku": "Heroku",
    "aws": "AWS",
    "google": "Google Cloud",
    "azure": "Azure",
}


# ================== CORE FUNCTION ==================
async def detect_tech(client: httpx.AsyncClient, domain: str, debug: bool = False):
    """Detect technologies used by a website"""
    detected = set()
    matches = []

    try:
        if not domain.startswith(("http://", "https://")):
            domain = "https://" + domain

        if debug:
            console.print(f"[DEBUG] Fetching {domain}...")

        response = await client.get(domain, timeout=DEFAULT_TIMEOUT)
        html = response.text.lower() if response.text else ""
        headers = {k.lower(): v.lower() for k, v in response.headers.items()}

        if debug:
            console.print(f"[DEBUG] Status: {response.status_code} | Content-Type: {headers.get('content-type', 'N/A')}")

        # Detect by HTML patterns
        for tech, patterns in TECH_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern.lower(), html):
                    detected.add(tech)
                    if debug:
                        matches.append(f"HTML pattern match: {tech} (pattern: {pattern})")

        # Detect by headers
        server = headers.get("server", "")
        x_powered_by = headers.get("x-powered-by", "")
        via = headers.get("via", "")
        
        # Check server header
        for pattern, tech_name in SERVER_PATTERNS.items():
            if pattern in server:
                detected.add(tech_name)
                if debug:
                    matches.append(f"Server header match: {tech_name} (found: {pattern})")
        
        # Check x-powered-by header
        for tech in TECH_PATTERNS.keys():
            if tech.lower() in x_powered_by:
                detected.add(tech)
                if debug:
                    matches.append(f"X-Powered-By header match: {tech}")
        
        # Check via header
        for pattern, tech_name in SERVER_PATTERNS.items():
            if pattern in via:
                detected.add(tech_name)
                if debug:
                    matches.append(f"Via header match: {tech_name} (found: {pattern})")

        # Detect by specific headers
        if "x-drupal-cache" in headers:
            detected.add("Drupal")
        if "x-generator" in headers:
            generator = headers["x-generator"].lower()
            if "wordpress" in generator:
                detected.add("WordPress")
            elif "joomla" in generator:
                detected.add("Joomla")
            elif "drupal" in generator:
                detected.add("Drupal")

        result = {
            "domain": domain,
            "final_url": str(response.url),
            "status_code": response.status_code,
            "detected_technologies": sorted(list(detected)),
            "matches": matches if debug else [],
            "headers": dict(response.headers) if debug else {},
            "error": None
        }

        return result

    except httpx.RequestError as e:
        if debug:
            console.print(f"[DEBUG] Request error for {domain}: {e}")
        return {
            "domain": domain,
            "error": f"RequestError: {e}"
        }
    except Exception as e:
        if debug:
            console.print(f"[DEBUG] Unexpected error for {domain}: {e}")
        return {
            "domain": domain,
            "error": f"{type(e).__name__}: {e}"
        }


# ================== MAIN SCAN FUNCTION ==================
async def scan_domains(domains: list, debug: bool):
    """Scan multiple domains for technologies"""
    results = []

    async with httpx.AsyncClient(follow_redirects=True, timeout=DEFAULT_TIMEOUT) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} domains"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Scanning domains...", total=len(domains))

            # Create tasks
            tasks = []
            for domain in domains:
                coro = detect_tech(client, domain, debug)
                tasks.append(coro)

            # Process results
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                progress.advance(task)

    return results


# ================== UTILS ==================
def display_results(results: list):
    """Display results in rich table"""
    table = Table(title="Technology Detection Results", header_style="bold magenta", show_lines=True)
    table.add_column("Domain", style="cyan", no_wrap=False)
    table.add_column("Status", style="yellow")
    table.add_column("Detected Technologies", style="green")

    for result in results:
        domain = result["domain"]
        error = result.get("error")

        if error:
            table.add_row(domain, Text("ERROR", style="bold red"), error)
            continue

        status_code = result["status_code"]
        final_url = result["final_url"]
        detected = result["detected_technologies"]
        
        # Show redirect info if domain changed
        display_domain = domain
        if domain != final_url:
            display_domain += f" → {final_url}"

        status_text = Text(f"{status_code}", style="bold green" if status_code < 400 else "bold red")
        tech_list = ", ".join(detected) if detected else "None detected"

        table.add_row(display_domain, status_text, tech_list)

    console.print(table)


def save_results(results: list, prefix: str = "tech_detect", results_dir: Path = DEFAULT_RESULTS_DIR):
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
            fieldnames = ["domain", "final_url", "status_code", "detected_technologies", "error"]
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "domain": r.get("domain", ""),
                    "final_url": r.get("final_url", ""),
                    "status_code": r.get("status_code", ""),
                    "detected_technologies": "; ".join(r.get("detected_technologies", [])),
                    "error": r.get("error", "")
                })
    except Exception as e:
        console.print(f"[red]Failed to save CSV results: {e}[/red]")
        csv_path = None

    return json_path, csv_path


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Technology Detector — Identify Web Technologies",
        epilog="Example: python3 tech-detector.py --url https://example.com --debug"
    )
    parser.add_argument("--url", "-u", action="append", help="URL(s) to scan for technologies (can be used multiple times)")
    parser.add_argument("--file", "-f", help="File containing URLs (one per line)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows matched patterns and headers)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT Technology Detector[/bold green]")

    # If no URL provided, fallback to interactive mode
    if not args.url and not args.file:
        input_domains = Prompt.ask("[bold cyan]Enter website(s) (comma-separated, with or without http/https)")
        if not input_domains:
            console.print("[red]No URLs provided. Exiting.[/red]")
            return
        domains = [d.strip() for d in input_domains.split(",")]
        debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)
    else:
        # CLI mode
        debug = args.debug
        domains = []

        if args.url:
            domains.extend([u.strip() for u in args.url])

        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    file_urls = [line.strip() for line in f if line.strip()]
                    domains.extend(file_urls)
                    console.print(f"[cyan]Loaded {len(file_urls)} URLs from {args.file}[/cyan]")
            except Exception as e:
                console.print(f"[red]Error reading URL file: {e}[/red]")
                return

        if not domains:
            console.print("[red]No URLs provided. Exiting.[/red]")
            return

    # Run scan
    console.print(f"\n[bold yellow]🔍 Scanning [bold green]{len(domains)}[/bold green] websites for technologies...[/bold yellow]\n")

    start_time = time.time()
    results = asyncio.run(scan_domains(domains, debug))
    duration = time.time() - start_time

    # Display results
    display_results(results)
    console.print(f"\n[bold green]✅ Scan finished in {duration:.1f}s.[/bold green]")

    # Save results
    json_path, csv_path = save_results(results, prefix="tech_detection")
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
