import dns.resolver
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()

def query_dns(domain):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # Google e Cloudflare

    record_types = ["A", "MX", "NS", "TXT", "CNAME"]

    for rtype in record_types:
        try:
            answers = resolver.resolve(domain, rtype)
            table = Table(title=f"{rtype} records for {domain}", show_lines=True)
            table.add_column("Record", style="cyan")

            for rdata in answers:
                table.add_row(rdata.to_text())

            console.print(table)

        except dns.resolver.NoAnswer:
            console.print(f"[yellow]{rtype} records for {domain}: No answer[/yellow]")
        except dns.resolver.NXDOMAIN:
            console.print(f"[red]{rtype} records for {domain}: Domain does not exist[/red]")
        except Exception as e:
            console.print(f"[red]{rtype} records for {domain}: Error - {e}[/red]")

def main():
    console.rule("[bold green]PYSINT DNS Hunter[/bold green]")
    domain = Prompt.ask("[bold cyan]Enter the domain you want to check DNS records for[/bold cyan]").strip()
    query_dns(domain)
    console.print("\n✅ DNS query finished.")

if __name__ == "__main__":
    main()
