import asyncio
import httpx
from asyncio import Semaphore
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()
MAX_CONCURRENT_REQUESTS = 10  # Limite de requisições simultâneas

async def test_param(client, domain, param, sem: Semaphore, active_params):
    async with sem:
        url = f"{domain}?{param}=test"
        try:
            r = await client.get(url, timeout=10)
            if r.status_code < 400:
                active_params.append((param, url, r.status_code))
                console.print(f"[bold green][ACTIVE][/bold green] {param} -> {r.status_code} | URL: {url}")
            else:
                console.print(f"[yellow][INACTIVE][/yellow] {param} -> {r.status_code}")
        except httpx.RequestError as e:
            console.print(f"[red][FAILED][/red] {param} -> {e}")

async def scan_parameters(domain, params):
    active_params = []
    sem = Semaphore(MAX_CONCURRENT_REQUESTS)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [test_param(client, domain, param, sem, active_params) for param in params]
        await asyncio.gather(*tasks)
    return active_params

def load_wordlist(file_path, limit=0):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            params = [line.strip() for line in f if line.strip()]
        if limit > 0:
            return params[:limit]
        return params
    except FileNotFoundError:
        console.print(f"[red]Wordlist file {file_path} not found![/red]")
        return []

def main():
    console.rule("[bold green]PYSINT Parameter Finder[/bold green]")

    domain = Prompt.ask("[bold cyan]Enter the website to scan (with http/https)[/bold cyan]").strip()
    limit_input = Prompt.ask("[bold cyan]Enter maximum number of parameters to test (0 = all)[/bold cyan]").strip()
    limit = int(limit_input) if limit_input.isdigit() else 0

    wordlist_file = "large-params.txt"
    params = load_wordlist(wordlist_file, limit)

    if not params:
        console.print("[red]No parameters to test. Exiting.[/red]")
        return

    console.print(f"\n🔍 Scanning [bold]{domain}[/bold] for [bold]{len(params)}[/bold] parameters...\n")
    found = asyncio.run(scan_parameters(domain, params))

    console.print(Panel(f"✅ Scan finished. Active parameters: {len(found)}", style="green"))
    if found:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Parameter", style="cyan")
        table.add_column("Status URL", style="yellow")
        table.add_column("HTTP Status", style="green")

        for param, url, status in found:
            table.add_row(param, url, str(status))

        console.print(table)

if __name__ == "__main__":
    main()
