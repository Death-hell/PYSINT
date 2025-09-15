import httpx
import re
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

console = Console()

def find_emails(url: str):
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        # Regex para encontrar emails
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", response.text)

        if emails:
            table = Table(title=f"Emails found on {url}", show_lines=True)
            table.add_column("Email Address", style="cyan")
            for email in sorted(set(emails)):
                table.add_row(email)
            console.print(table)
        else:
            console.print(Panel(f"No emails found on [bold]{url}[/bold].", style="yellow"))

    except httpx.RequestError as e:
        console.print(Panel(f"Error accessing the website: {e}", style="red"))
    except httpx.HTTPStatusError as e:
        console.print(Panel(f"HTTP error: {e}", style="red"))

def main():
    console.rule("[bold green]PYSINT Email Extractor[/bold green]")
    url = Prompt.ask("[bold cyan]Enter the URL of the website to search for emails[/bold cyan]").strip()
    find_emails(url)
    console.print("\n✅ Email scan finished.")

if __name__ == "__main__":
    main()
