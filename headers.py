import httpx

def scan_headers(domain):
    try:
        with httpx.Client(follow_redirects=True, timeout=5) as client:
            response = client.get(domain)
            print(f"\n🔍 HTTP Headers for {domain}:\n")
            for header, value in response.headers.items():
                print(f"{header}: {value}")
    except httpx.RequestError as e:
        print(f"Error fetching headers: {e}")

if __name__ == "__main__":
    domain = input("Enter the website (with http/https): ").strip()
    scan_headers(domain)
