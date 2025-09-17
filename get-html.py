#!/usr/bin/env python3
"""
get-html.py - HTML Fetcher & Viewer for PYSINT Suite
Author: Mael
License: MIT
Repository: ~/PyToolKit

Features:
- Fetch and display HTML content from URLs
- Limit output length or save full HTML to file
- Saves results (HTML + metadata) to ~/PYSINT/results
- CLI mode (--url, --length, --save, etc.) + Interactive fallback
- Debug mode (--debug) to show headers, encoding, response time
- Help (--help) via argparse (native)
"""

import httpx
import json
import os
import time
import argparse
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.markup import escape
from rich.progress import Progress, SpinnerColumn, TextColumn

# ================== DEFAULTS ==================
DEFAULT_TIMEOUT = 10.0
DEFAULT_LENGTH = 500
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

console = Console()


# ================== CORE FUNCTION ==================
def fetch_html_content(url: str, length: int = None, save_full: bool = False, debug: bool = False):
    """Fetch HTML content from URL"""
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        if debug:
            console.print(f"[DEBUG] Fetching: {url}")

        with httpx.Client(follow_redirects=True, timeout=DEFAULT_TIMEOUT) as client:
            start_time = time.time()
            response = client.get(url)
            duration = time.time() - start_time

            response.raise_for_status()

            if debug:
                console.print(f"[DEBUG] Status: {response.status_code} | Duration: {duration:.2f}s")
                console.print(f"[DEBUG] Content-Type: {response.headers.get('content-type', 'N/A')}")
                console.print(f"[DEBUG] Encoding: {response.encoding}")
                console.print(f"[DEBUG] Content-Length: {len(response.content)} bytes")

            html_content = response.text
            display_content = html_content[:length] if length else html_content

            result = {
                "url": url,
                "final_url": str(response.url),
                "status_code": response.status_code,
                "content_length": len(response.content),
                "encoding": response.encoding,
                "content_type": response.headers.get("content-type", ""),
                "duration_seconds": duration,
                "html_preview": display_content,
                "html_full": html_content if save_full else None,
                "headers": dict(response.headers) if debug else {},
                "error": None
            }

            return result

    except httpx.RequestError as e:
        if debug:
            console.print(f"[DEBUG] Request error: {e}")
        return {
            "url": url,
            "error": f"RequestError: {e}"
        }
    except httpx.HTTPStatusError as e:
        if debug:
            console.print(f"[DEBUG] HTTP error: {e}")
        return {
            "url": url,
            "status_code": e.response.status_code if e.response else None,
            "error": f"HTTPStatusError: {e}"
        }
    except Exception as e:
        if debug:
            console.print(f"[DEBUG] Unexpected error: {e}")
        return {
            "url": url,
            "error": f"{type(e).__name__}: {e}"
        }


# ================== MAIN SCAN FUNCTION ==================
def fetch_multiple_urls(urls: list, length: int, save_full: bool, debug: bool):
    """Fetch HTML from multiple URLs"""
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Fetching HTML...", total=len(urls))

        for url in urls:
            progress.update(task, description=f"[cyan]Fetching {url}...")
            result = fetch_html_content(url, length, save_full, debug)
            results.append(result)
            progress.advance(task)

    return results


# ================== UTILS ==================
def display_results(results: list, use_syntax: bool = False):
    """Display results in rich panels"""
    for result in results:
        url = result["url"]
        error = result.get("error")

        if error:
            console.print(Panel(f"❌ [bold]{url}[/bold]: {error}", style="red"))
        else:
            final_url = result["final_url"]
            status_code = result["status_code"]
            content_length = result["content_length"]
            duration = result["duration_seconds"]

            title = f"🌐 HTML Content from {url}"
            if url != final_url:
                title += f" (redirected to {final_url})"

            subtitle = f"Status: {status_code} | Size: {content_length} bytes | Time: {duration:.2f}s"
            panel = Panel(f"[bold cyan]{title}[/bold cyan]\n[dim]{subtitle}[/dim]", style="green")
            console.print(panel)

            html_preview = result["html_preview"]
            if use_syntax:
                # Try to use Syntax highlighting if rich supports it
                try:
                    syntax = Syntax(html_preview, "html", theme="monokai", line_numbers=False)
                    console.print(syntax)
                except:
                    console.print(escape(html_preview))
            else:
                console.print(escape(html_preview))


def save_results(results: list, prefix: str = "html_fetch", results_dir: Path = DEFAULT_RESULTS_DIR):
    """Save results as JSON (metadata) and separate HTML files"""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = results_dir / f"{prefix}_{ts}.json"
    html_dir = results_dir / f"{prefix}_{ts}_html"
    html_dir.mkdir(exist_ok=True)

    # Save metadata JSON
    try:
        # Create a copy without full HTML for the JSON
        metadata_results = []
        for r in results:
            r_copy = r.copy()
            if "html_full" in r_copy:
                del r_copy["html_full"]
            if "headers" in r_copy and not r.get("error"):
                # Keep headers only if debug was enabled and no error
                pass
            else:
                r_copy.pop("headers", None)
            metadata_results.append(r_copy)

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(metadata_results, jf, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"[red]Failed to save JSON metadata: {e}[/red]")
        json_path = None

    # Save individual HTML files
    html_paths = []
    for result in results:
        if not result.get("error") and result.get("html_full"):
            try:
                # Create safe filename
                url_part = result["final_url"].replace("://", "_").replace("/", "_").replace("?", "_").replace("&", "_")[:50]
                html_path = html_dir / f"{url_part}.html"
                with open(html_path, "w", encoding="utf-8") as hf:
                    hf.write(result["html_full"])
                html_paths.append(str(html_path))
            except Exception as e:
                console.print(f"[yellow]Failed to save HTML for {result['url']}: {e}[/yellow]")

    return json_path, html_paths


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT HTML Fetcher — Get and Display Web Page HTML",
        epilog="Examples:\n"
               "  python3 get-html.py --url https://example.com --length 1000\n"
               "  python3 get-html.py --url https://site1.com --url https://site2.com --save-full --debug"
    )
    parser.add_argument("--url", "-u", action="append", help="URL(s) to fetch HTML from (can be used multiple times)")
    parser.add_argument("--file", "-f", help="File containing URLs (one per line)")
    parser.add_argument("--length", "-l", type=int, default=DEFAULT_LENGTH, help=f"Number of characters to display (default: {DEFAULT_LENGTH})")
    parser.add_argument("--save-full", action="store_true", help="Save full HTML content to files")
    parser.add_argument("--syntax", action="store_true", help="Use syntax highlighting for HTML output")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (shows headers, encoding, response time)")
    # ✅ --help is handled automatically by argparse

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT HTML Fetcher[/bold green]")

    # If no URL provided, fallback to interactive mode
    if not args.url and not args.file:
        url = Prompt.ask("[bold cyan]Enter the URL of the website")
        if not url:
            console.print("[red]No URL provided. Exiting.[/red]")
            return

        length_input = Prompt.ask(f"[bold cyan]Enter how many characters you want to see (default: {DEFAULT_LENGTH})", default=str(DEFAULT_LENGTH))
        length = int(length_input) if length_input.isdigit() else DEFAULT_LENGTH

        save_full = Confirm.ask("[bold cyan]Save full HTML to file?", default=False)
        use_syntax = Confirm.ask("[bold cyan]Use syntax highlighting?", default=False)
        debug = Confirm.ask("[bold cyan]Enable debug mode?", default=False)

        urls = [url.strip()]
    else:
        # CLI mode
        debug = args.debug
        length = args.length
        save_full = args.save_full
        use_syntax = args.syntax
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

    # Run fetch
    console.print(f"\n[bold yellow]🔍 Fetching HTML from [bold green]{len(urls)}[/bold green] URLs...[/bold yellow]\n")

    start_time = time.time()
    results = fetch_multiple_urls(urls, length, save_full, debug)
    duration = time.time() - start_time

    # Display results
    display_results(results, use_syntax=use_syntax)
    console.print(f"\n[bold green]✅ Fetch finished in {duration:.1f}s.[/bold green]")

    # Save results
    json_path, html_paths = save_results(results, prefix="html_fetch")
    saved = []
    if json_path:
        saved.append(str(json_path))
    if html_paths:
        saved.append(f"{len(html_paths)} HTML files")
    if saved:
        console.print(f"[green]💾 Results saved to:[/green] {', '.join(saved)}")
    else:
        console.print("[yellow]⚠️  No results were saved (I/O error).[/yellow]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]🛑 Fetch interrupted by user.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
