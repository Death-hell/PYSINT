import requests
import httpx
import re

def get_subdomains(domain, limit=50):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    # First try JSON
    url_json = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        resp = requests.get(url_json, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        subdomains = set()
        for entry in data:
            names = entry['name_value'].split("\n")
            for name in names:
                if domain in name:
                    subdomains.add(name.strip())
        return list(subdomains)[:limit]
    except Exception:
        print("JSON fetch failed, trying HTML parsing...")
        # Fallback: HTML parsing
        url_html = f"https://crt.sh/?q=%25.{domain}"
        try:
            resp = requests.get(url_html, headers=headers, timeout=10)
            resp.raise_for_status()
            subdomains = set(re.findall(rf"[a-zA-Z0-9._-]+\.{re.escape(domain)}", resp.text))
            return list(subdomains)[:limit]
        except Exception as e:
            print("HTML fetch also failed:", e)
            return []

def check_subdomains(subdomains):
    active = []
    with httpx.Client(follow_redirects=True, timeout=5) as client:
        for sub in subdomains:
            try:
                r = client.get(f"http://{sub}")
                if r.status_code < 400:
                    active.append(sub)
                    print(f"[ACTIVE] {sub} -> {r.status_code}")
                else:
                    print(f"[INACTIVE] {sub} -> {r.status_code}")
            except httpx.RequestError:
                print(f"[FAILED] {sub}")
    return active

if __name__ == "__main__":
    domain = input("Enter the domain to search for subdomains: ").strip()
    limit_input = input("Enter the maximum number of subdomains to check (0 = unlimited): ").strip()
    limit = int(limit_input) if limit_input.isdigit() and int(limit_input) > 0 else 50

    print(f"\n🔍 Fetching up to {limit} subdomains for {domain}...\n")
    subdomains = get_subdomains(domain, limit)
    
    if subdomains:
        print(f"\nFound {len(subdomains)} subdomains. Checking which ones are active...\n")
        active_subs = check_subdomains(subdomains)
        print(f"\n✅ Active subdomains ({len(active_subs)}):")
        for sub in active_subs:
            print(sub)
    else:
        print("No subdomains found.")
