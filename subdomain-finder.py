import requests
import httpx
import re
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.prompt import Prompt

console = Console()

def get_subdomains(domain, limit=50):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    # First attempt: JSON from crt.sh
    url_json = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        resp = requests.get(url_json, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        subdomains = set()
        for entry in data:
            names = entry['name_value'].split("\n")
            for name in names:
                if domain in name:
                    subdomains.add(name.strip())
        return list(subdomains)[:limit]
    except Exception:
        console.print("[yellow]JSON fetch failed, trying HTML parsing...[/yellow]")

    # Fallback: HTML parsing
    url_html = f"https://crt.sh/?q=%25.{domain}"
    try:
        resp = requests.get(url_html, headers=headers, timeout=10)
        resp.raise_for_status()
        subdomains = set(re.findall(rf"[a-zA-Z0-9._-]+\.{re.escape(domain)}", resp.text))
        return list(subdomains)[:limit]
    except Exception as e:
        console.print(f"[red]HTML fetch failed: {e}[/red]")
        return []

def check_subdomains(subdomains):
    active = []
    console.print("\n🔍 Checking which subdomains are active...\n")
    table = Table(title="Subdomain Status", header_style="bold magenta")
    table.add_column("Subdomain", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("HTTP Code", style="green")

    with httpx.Client(follow_redirects=True, timeout=5) as client:
        for sub in track(subdomains, description="Checking subdomains..."):
            try:
                r = client.get(f"http://{sub}")
                status = "[green]ACTIVE[/green]" if r.status_code < 400 else "[red]INACTIVE[/red]"
                table.add_row(sub, status, str(r.status_code))
                if r.status_code < 400:
                    active.append(sub)
            except httpx.RequestError:
                table.add_row(sub, "[red]FAILED[/red]", "-")
    console.print(table)
    return active

def main():
    console.rule("[bold green]PYSINT Subdomain Finder[/bold green]")
    domain = Prompt.ask("Enter the domain to search for subdomains").strip()
    limit_input = Prompt.ask("Maximum number of subdomains to check (0 = unlimited)", default="50")
    limit = int(limit_input) if limit_input.isdigit() and int(limit_input) > 0 else 50

    console.print(f"\n🔍 Fetching up to {limit} subdomains for {domain}...\n")
    subdomains = get_subdomains(domain, limit)

    if subdomains:
        console.print(f"[bold green]Found {len(subdomains)} subdomains[/bold green]")
        active_subs = check_subdomains(subdomains)
        console.print(f"\n✅ [bold green]Active subdomains ({len(active_subs)})[/bold green]")
    else:
        console.print("[red]No subdomains found[/red]")

if __name__ == "__main__":
    main()
