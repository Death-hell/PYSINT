from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
import subprocess
import sys

console = Console()

MODULES = {
    "1": ("Whois/IP Lookup", "python analyzer-whois.py"),
    "2": ("DNS Lookup", "python dns-hunter.py"),
    "3": ("HTML Scraper", "python get-html.py"),
    "4": ("Email Extractor", "python find-email-in-html.py"),
    "5": ("Subdomain Finder", "python subdomain-finder.py"),
    "6": ("Parameter Scanner", "python param-finder.py"),
    "7": ("Directory / File Scanner", "python directory-fuzzer.py"),
    "8": ("SSL/TLS Info", "python ssl-info.py"),
    "9": ("HTTP Headers", "python headers.py"),
    "10": ("Wayback / Archive Lookup", "python wayback-Scan.py"),
    "11": ("Technology / CMS Detection", "python tech-detector.py"),
    "12": ("Port / Service Scanner", "python port-scan.py"),
    "13": ("XSS Scanner", "python XSS-Scanner.py"),
    "14": ("LFI Scanner", "python LFI-Scanner.py"),
    "15": ("SQLi Scanner", "python SQLi-Scanner.py"),
    "16": ("GeoIP Lookup", "python geoip-scan.py"),
    "0": ("Exit", None)
}

def main():
    console.print(Panel.fit("[bold cyan]PYSINT - Master OSINT Scanner[/bold cyan]", border_style="bright_blue"))

    while True:
        table = Table(title="Modules", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="bold yellow")
        table.add_column("Module Name", style="bold green")

        for key, (name, _) in MODULES.items():
            table.add_row(key, name)

        console.print(table)

        choice = Prompt.ask("\nSelect an option", default="0").strip()

        if choice == "0":
            console.print("[bold red]Exiting...[/bold red]")
            sys.exit(0)

        if choice in MODULES:
            name, command = MODULES[choice]
            console.print(f"\n[bold cyan]🔹 Running {name}...[/bold cyan]\n")
            try:
                subprocess.run(command, shell=True)
            except Exception as e:
                console.print(f"[bold red]Error running module {name}:[/bold red] {e}")
        else:
            console.print("[bold red]Invalid choice, try again.[/bold red]")

if __name__ == "__main__":
    main()
