import asyncio
import httpx

async def test_param(client, domain, param, active_params):
    url = f"{domain}?{param}=test"
    try:
        r = await client.get(url)
        if r.status_code < 400:
            active_params.append((param, url, r.status_code))
            print(f"[ACTIVE] {param} -> {r.status_code} | URL: {url}")
        else:
            print(f"[INACTIVE] {param} -> {r.status_code}")
    except httpx.RequestError:
        print(f"[FAILED] {param}")

async def scan_parameters(domain, params):
    active_params = []
    async with httpx.AsyncClient(follow_redirects=True, timeout=5) as client:
        tasks = [test_param(client, domain, param, active_params) for param in params]
        await asyncio.gather(*tasks)
    return active_params

def load_wordlist(file_path, limit=0):
    with open(file_path, "r") as f:
        params = [line.strip() for line in f if line.strip()]
    if limit > 0:
        return params[:limit]
    return params

if __name__ == "__main__":
    domain = input("Enter the website to scan (with http/https): ").strip()
    limit_input = input("Enter maximum number of parameters to test (0 = all): ").strip()
    limit = int(limit_input) if limit_input.isdigit() else 0

    wordlist_file = "large-params.txt"
    params = load_wordlist(wordlist_file, limit)

    print(f"\n🔍 Scanning {domain} for {len(params)} parameters...\n")
    found = asyncio.run(scan_parameters(domain, params))

    print(f"\n✅ Scan finished. Active parameters ({len(found)}):")
    for param, url, status in found:
        print(f"{param} -> {status} | URL: {url}")
