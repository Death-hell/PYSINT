import asyncio
import httpx

async def test_path(client, domain, path, active_paths):
    url = f"{domain}/{path}"
    try:
        r = await client.get(url)
        if r.status_code < 400:
            active_paths.append((path, url, r.status_code))
            print(f"[ACTIVE] {path} -> {r.status_code} | URL: {url}")
        else:
            print(f"[INACTIVE] {path} -> {r.status_code}")
    except httpx.RequestError:
        print(f"[FAILED] {path}")

async def scan_paths(domain, paths):
    active_paths = []
    async with httpx.AsyncClient(follow_redirects=True, timeout=5) as client:
        tasks = [test_path(client, domain, path, active_paths) for path in paths]
        await asyncio.gather(*tasks)
    return active_paths

def load_wordlist(file_path, limit=0):
    with open(file_path, "r") as f:
        paths = [line.strip() for line in f if line.strip()]
    if limit > 0:
        return paths[:limit]
    return paths

if __name__ == "__main__":
    domain = input("Enter the website to scan (with http/https): ").strip()
    limit_input = input("Enter maximum number of directories/files to test (0 = all): ").strip()
    limit = int(limit_input) if limit_input.isdigit() else 0

    wordlist_file = "directory-wordlist.txt"
    paths = load_wordlist(wordlist_file, limit)

    print(f"\n🔍 Scanning {domain} for {len(paths)} directories/files...\n")
    found = asyncio.run(scan_paths(domain, paths))

    print(f"\n✅ Scan finished. Active directories/files ({len(found)}):")
    for path, url, status in found:
        print(f"{path} -> {status} | URL: {url}")
