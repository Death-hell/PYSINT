import httpx
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markup import escape

console = Console()

def fetch_html(url: str, length: int):
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        with httpx.Client(follow_redirects=True, timeout=10) as client:
            response = client.get(url)
            response.raise_for_status()
            html_content = response.text[:length]

            console.print(Panel(f"[bold cyan]First {length} characters of {url} HTML content[/bold cyan]", style="green"))
            console.print(escape(html_content))  # Escape to show HTML safely

    except httpx.RequestError as e:
        console.print(Panel(f"[ERROR] Error accessing the website: {e}", style="red"))
    except httpx.HTTPStatusError as e:
        console.print(Panel(f"[ERROR] HTTP error: {e}", style="red"))

def main():
    console.rule("[bold green]PYSINT HTML Fetcher[/bold green]")
    url = Prompt.ask("[bold cyan]Enter the URL of the website[/bold cyan]").strip()
    length_input = Prompt.ask("[bold cyan]Enter how many characters you want to see[/bold cyan]").strip()

    if length_input.isdigit():
        length = int(length_input)
        fetch_html(url, length)
    else:
        console.print(Panel("[ERROR] Invalid number of characters", style="red"))

if __name__ == "__main__":
    main()
