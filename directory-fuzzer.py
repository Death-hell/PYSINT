import asyncio
import httpx
from asyncio import Semaphore
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.prompt import Prompt

# Configurações
WORDLIST_FILE = "directory-wordlist.txt"
MAX_CONCURRENT_REQUESTS = 10  # Limite de requisições simultâneas

console = Console()

async def test_path(client, domain, path, active_paths, sem: Semaphore, progress_task, progress):
    async with sem:
        url = f"{domain.rstrip('/')}/{path.lstrip('/')}"
        try:
            r = await client.get(url)
            if r.status_code < 400:
                active_paths.append((path, url, r.status_code))
                progress.update(progress_task, description=f"[green]ACTIVE[/green] {path}")
            else:
                progress.update(progress_task, description=f"[yellow]INACTIVE[/yellow] {path}")
        except httpx.RequestError:
            progress.update(progress_task, description=f"[red]FAILED[/red] {path}")
        finally:
            progress.advance(progress_task)

async def scan_paths(domain, paths):
    active_paths = []
    sem = Semaphore(MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        with Progress() as progress:
            task = progress.add_task(f"[cyan]Scanning {domain}...", total=len(paths))
            tasks = [test_path(client, domain, path, active_paths, sem, task, progress) for path in paths]
            await asyncio.gather(*tasks)
    return active_paths

def load_wordlist(file_path, limit=0):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            paths = [line.strip() for line in f if line.strip()]
        if limit > 0:
            return paths[:limit]
        return paths
    except FileNotFoundError:
        console.print(f"[bold red]Wordlist file {file_path} not found![/bold red]")
        return []

def main():
    console.rule("[bold red]PYSINT Directory Fuzzer[/bold red]")
    domain = Prompt.ask("[bold cyan]Enter the website to scan (with http/https)[/bold cyan]").strip()
    limit_input = Prompt.ask("[bold yellow]Enter maximum number of directories/files to test (0 = all)[/bold yellow]").strip()
    limit = int(limit_input) if limit_input.isdigit() else 0

    paths = load_wordlist(WORDLIST_FILE, limit)
    if not paths:
        return

    console.print(f"\n🔍 Scanning {domain} for [bold green]{len(paths)}[/bold green] directories/files...\n")
    found = asyncio.run(scan_paths(domain, paths))

    table = Table(title=f"Active Directories/Files for {domain}")
    table.add_column("Path", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("URL", style="magenta")

    for path, url, status in found:
        table.add_row(path, str(status), url)

    console.print(table)
    console.print(f"\n✅ Scan finished. [bold green]{len(found)}[/bold green] active directories/files found.")

if __name__ == "__main__":
    main()
