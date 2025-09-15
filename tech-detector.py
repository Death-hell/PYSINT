import asyncio
import httpx
import re

# Dicionário de padrões para CMS / Frameworks / JS libs
TECH_PATTERNS = {
    "WordPress": [r"wp-content", r"wp-includes", r"wordpress"],
    "Joomla": [r"Joomla!", r"index.php\?option="],
    "Drupal": [r"drupal", r"sites/all"],
    "Magento": [r"Magento", r"/skin/frontend/"],
    "Laravel": [r"/public/", r"laravel"],
    "Django": [r"csrftoken", r"django_session"],
    "React": [r"react", r"__reactinternal"],
    "Angular": [r"angular", r"ng-version"],
    "Vue.js": [r"vue", r"v-cloak"],
    "Nginx": [],  # Detect via header
    "Apache": [],
    "IIS": []
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
    results = []
    async with httpx.AsyncClient(follow_redirects=True, timeout=5) as client:
        tasks = [detect_tech(client, domain) for domain in domains]
        results = await asyncio.gather(*tasks)
    return results

if __name__ == "__main__":
    input_domains = input("Enter website(s) (comma-separated, with http/https): ").strip()
    domains = [d.strip() for d in input_domains.split(",")]

    results = asyncio.run(scan_domains(domains))

    print("\n🔍 Technology Detection Results:\n")
    for domain, detected in results:
        print(f"{domain}:")
        if detected:
            for tech in detected:
                print(f"- {tech}")
        else:
            print("- No known technologies detected")
        print()
