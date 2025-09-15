import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

def scan_headers(domain: str):
    try:
        with httpx.Client(follow_redirects=True, timeout=5) as client:
            response = client.get(domain)

            console.print(Panel(f"🔍 HTTP Headers for {domain}", style="green"))

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Header", style="cyan")
            table.add_column("Value", style="yellow")

            for header, value in response.headers.items():
                table.add_row(header, value)

            console.print(table)

    except httpx.RequestError as e:
        console.print(Panel(f"[ERROR] Error fetching headers: {e}", style="red"))

def main():
    console.rule("[bold green]PYSINT HTTP Headers Scanner[/bold green]")
    domain = Prompt.ask("[bold cyan]Enter the website (with http/https)[/bold cyan]").strip()
    scan_headers(domain)

if __name__ == "__main__":
    main()
