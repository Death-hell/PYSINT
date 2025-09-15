import asyncio
import httpx
import urllib.parse
from asyncio import Semaphore
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

WORDLIST_FILE = "LFI-wordlist.txt"
MAX_CONCURRENT_REQUESTS = 10  # Limite de requisições simultâneas

console = Console()

async def test_lfi(client, url, param, payload, sem: Semaphore):
    async with sem:
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            query_params[param] = payload
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            full_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"

            response = await client.get(full_url, timeout=15.0)

            indicators = [
                "root:",
                "bin/bash",
                "etc/passwd",
                "No such file or directory",
                "Warning"
            ]

            if any(indicator in response.text for indicator in indicators):
                return (param, full_url, response.status_code, True)
            else:
                return (param, full_url, response.status_code, False)

        except httpx.RequestError as e:
            return (param, None, None, f"Request failed: {e}")
        except Exception as e:
            return (param, None, None, f"Error: {e}")

async def run_lfi_scan():
    console.rule("[bold red]PYSINT LFI Scanner[/bold red]")

    url = console.input("[bold cyan]Enter target URL (with http/https and at least one parameter): [/bold cyan]").strip()
    params_input = console.input("[bold cyan]Enter comma-separated parameters to test (or leave blank for all): [/bold cyan]").strip()
    
    if params_input:
        parameters = [p.strip() for p in params_input.split(",")]
    else:
        parsed = urllib.parse.urlparse(url)
        parameters = list(urllib.parse.parse_qs(parsed.query).keys())
        if not parameters:
            console.print("[bold red]No parameters found in URL. Exiting.[/bold red]")
            return

    max_payloads_input = console.input("[bold cyan]Enter maximum number of payloads to test (0 = all): [/bold cyan]").strip()
    max_payloads = int(max_payloads_input) if max_payloads_input.isdigit() else 0

    try:
        with open(WORDLIST_FILE, "r", encoding="utf-8") as f:
            payloads = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        console.print(f"[bold red]Wordlist file {WORDLIST_FILE} not found. Exiting.[/bold red]")
        return

    if max_payloads > 0:
        payloads = payloads[:max_payloads]

    console.print(f"\n[bold yellow]🔍 Testing {len(payloads)} LFI payloads on {len(parameters)} parameters...[/bold yellow]\n")

    sem = Semaphore(MAX_CONCURRENT_REQUESTS)
    results = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("[green]Scanning...", total=len(parameters)*len(payloads))
            tasks = []
            for param in parameters:
                for payload in payloads:
                    coro = test_lfi(client, url, param, payload, sem)
                    coro = asyncio.create_task(coro)
                    coro.add_done_callback(lambda _: progress.update(task, advance=1))
                    tasks.append(coro)
            results = await asyncio.gather(*tasks)

    table = Table(title="LFI Scan Results", show_lines=True)
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Status/Code", style="magenta")
    table.add_column("URL", style="green")

    vulns = 0
    for r in results:
        param, full_url, status, info = r
        if info is True:
            table.add_row(param, f"[bold red]VULNERABLE ({status})[/bold red]", full_url)
            vulns += 1
        elif info is False:
            table.add_row(param, f"[green]SAFE ({status})[/green]", full_url)
        else:  # error message
            table.add_row(param, f"[yellow]ERROR[/yellow]", str(info))

    console.print(table)
    console.print(f"\n[bold yellow]✅ Scan finished. Vulnerable parameters found: {vulns}[/bold yellow]")

if __name__ == "__main__":
    asyncio.run(run_lfi_scan())
