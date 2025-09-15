import requests

def wayback_lookup(domain, limit=10):
    url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=timestamp,original&collapse=digest"
    try:
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            return

        data = response.json()
        if len(data) <= 1:
            print("No archived versions found.")
            return

        print(f"\n🔍 Archived versions for {domain} (showing up to {limit}):\n")
        for entry in data[1:limit+1]:  # skip header row
            timestamp, original_url = entry
            date = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
            print(f"{date} -> {original_url}")

    except requests.RequestException as e:
        print(f"Error fetching Wayback data: {e}")

if __name__ == "__main__":
    domain = input("Enter the website (without http/https): ").strip()
    limit_input = input("Enter maximum number of snapshots to show (0 = all, max 50): ").strip()
    limit = int(limit_input) if limit_input.isdigit() else 10
    limit = min(limit, 50)  # limit max to avoid too many results
    wayback_lookup(domain, limit)
