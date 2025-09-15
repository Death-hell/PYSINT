import asyncio
import httpx
import re
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.prompt import Prompt

console = Console()

# Padrões ampliados para CMS / Frameworks / JS libs / Servidores
TECH_PATTERNS = {
    "WordPress": [r"wp-content", r"wp-includes", r"wordpress"],
    "Joomla": [r"Joomla!", r"index.php\?option="],
    "Drupal": [r"drupal", r"sites/all"],
    "Magento": [r"Magento", r"/skin/frontend/"],
    "Laravel": [r"/public/", r"laravel"],
    "Django": [r"csrftoken", r"django_session"],
    "React": [r"react", r"__reactinternal", r"data-reactroot"],
    "Angular": [r"angular", r"ng-version"],
    "Vue.js": [r"vue", r"v-cloak"],
    "Bootstrap": [r"bootstrap"],
    "jQuery": [r"jquery"],
    "Nginx": [],
    "Apache": [],
    "IIS": [],
    "Express": [r"express"],
    "Flask": [r"flask"],
    "Next.js": [r"_next"],
    "Gatsby": [r"gatsby"]
}

async def detect_tech(client, domain):
    detected = set()
    try:
        response = await client.get(domain)
        html = response.text.lower()
        headers = {k.lower(): v.lower() for k, v in response.headers.items()}

        # Detect by HTML patterns
        for tech, patterns in TECH_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern.lower(), html):
                    detected.add(tech)

        # Detect by headers (server)
        server = headers.get("server", "")
        if "nginx" in server:
            detected.add("Nginx")
        elif "apache" in server:
            detected.add("Apache")
        elif "iis" in server:
            detected.add("IIS")

        return domain, detected

    except httpx.RequestError:
        return domain, set()

async def scan_domains(domains):
    async with httpx.AsyncClient(follow_redirects=True, timeout=5) as client:
        tasks = [detect_tech(client, domain) for domain in domains]
        results = []
        for coro in track(asyncio.as_completed(tasks), total=len(tasks), description="Scanning domains..."):
            result = await coro
            results.append(result)
        return results

def main():
    console.rule("[bold green]PYSINT Technology Detector[/bold green]")
    input_domains = Prompt.ask("Enter website(s) (comma-separated, with http/https)").strip()
    domains = [d.strip() for d in input_domains.split(",")]

    results = asyncio.run(scan_domains(domains))

    table = Table(title="Technology Detection", header_style="bold magenta")
    table.add_column("Domain", style="cyan")
    table.add_column("Detected Technologies", style="green")

    for domain, detected in results:
        tech_list = ", ".join(sorted(detected)) if detected else "None detected"
        table.add_row(domain, tech_list)

    console.print(table)

if __name__ == "__main__":
    main()
