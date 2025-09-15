import requests
import socket
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

console = Console()

def get_geoip(target: str):
    # Resolve domain to IP if needed
    try:
        ip = socket.gethostbyname(target)
    except Exception as e:
        console.print(Panel(f"[ERROR] Could not resolve domain: {e}", style="red"))
        return

    # Query free GeoIP API
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,query"
    try:
        resp = requests.get(url, timeout=10).json()
    except Exception as e:
        console.print(Panel(f"[ERROR] Could not query GeoIP API: {e}", style="red"))
        return

    if resp.get("status") != "success":
        console.print(Panel(f"[ERROR] {resp.get('message', 'Unknown error')}", style="red"))
        return

    # Display results in a table
    table = Table(title=f"GeoIP Information for {target} ({ip})", show_lines=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    data_fields = ["country", "regionName", "city", "zip", "lat", "lon", "timezone", "isp", "query"]
    for field in data_fields:
        table.add_row(field.capitalize(), str(resp.get(field, "N/A")))

    console.print(table)
    console.print("\n✅ GeoIP scan finished.\n", style="green")

def main():
    console.rule("[bold green]PYSINT GeoIP Scanner[/bold green]")
    target = Prompt.ask("[bold cyan]Enter an IP address or domain[/bold cyan]").strip()
    get_geoip(target)

if __name__ == "__main__":
    main()
