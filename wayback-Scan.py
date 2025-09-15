import requests
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.prompt import Prompt

console = Console()

def wayback_lookup(domain, limit=10):
    url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=timestamp,original&collapse=digest"
    try:
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            console.print(f"[red]Error fetching data: {response.status_code}[/red]")
            return

        data = response.json()
        if len(data) <= 1:
            console.print(f"[yellow]No archived versions found for {domain}[/yellow]")
            return

        table = Table(title=f"Wayback Machine Snapshots for {domain}", header_style="bold magenta")
        table.add_column("Date", style="cyan")
        table.add_column("URL", style="green")

        # Skip header row
        snapshots = data[1:]
        if limit > 0:
            snapshots = snapshots[:limit]

        for entry in track(snapshots, description="Fetching snapshots..."):
            timestamp, original_url = entry
            date = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
            table.add_row(date, original_url)

        console.print(table)

    except requests.RequestException as e:
        console.print(f"[red]Error fetching Wayback data: {e}[/red]")

def main():
    console.rule("[bold green]PYSINT Wayback Scanner[/bold green]")
    domain = Prompt.ask("Enter the website (without http/https)").strip()
    limit_input = Prompt.ask("Enter maximum number of snapshots to show (0 = all, max 50)", default="10")
    
    limit = int(limit_input) if limit_input.isdigit() else 10
    limit = min(limit, 50)  # cap to avoid too many results

    wayback_lookup(domain, limit)

if __name__ == "__main__":
    main()
