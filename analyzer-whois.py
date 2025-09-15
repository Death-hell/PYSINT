import whois
from ipwhois import IPWhois
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()

def check_url():
    try:
        url = Prompt.ask("[bold cyan]Enter the URL to check[/bold cyan]").strip()
        info = whois.whois(url)

        table = Table(title=f"Whois Information for {url}", show_lines=True)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        for key, value in info.items():
            table.add_row(str(key), str(value))

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]ERROR! Invalid URL:[/bold red] {e}")

def check_ip():
    try:
        ip = Prompt.ask("[bold cyan]Enter the IP to check[/bold cyan]").strip()
        obj = IPWhois(ip)
        res = obj.lookup_rdap()

        table = Table(title=f"IP Whois Information for {ip}", show_lines=True)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        for key, value in res.items():
            # If value is a dict or list, convert to string
            table.add_row(str(key), str(value))

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]ERROR! Invalid IP:[/bold red] {e}")

def main():
    console.rule("[bold red]PYSINT Whois/IP Analyzer[/bold red]")

    while True:
        choice = Prompt.ask("[bold yellow]Do you want to check [url/ip] or type 'exit' to quit[/bold yellow]").strip().lower()
        if choice == "url":
            check_url()
        elif choice == "ip":
            check_ip()
        elif choice == "exit":
            console.print("[bold green]Exiting analyzer. Goodbye![/bold green]")
            break
        else:
            console.print("[bold red]Invalid command! Please type 'url' or 'ip'.[/bold red]")

if __name__ == "__main__":
    main()
