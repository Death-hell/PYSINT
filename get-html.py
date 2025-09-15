import httpx

def fetch_html(url, length):
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        with httpx.Client(follow_redirects=True, timeout=10) as client:
            response = client.get(url)
            response.raise_for_status()
            html_content = response.text[:length]
            print(f"\nFirst {length} characters of {url} HTML content:\n")
            print(html_content)

    except httpx.RequestError as e:
        print("Error accessing the website:", e)
    except httpx.HTTPStatusError as e:
        print("HTTP error:", e)

if __name__ == "__main__":
    url = input("Enter the URL of the website: ").strip()
    length_input = input("Enter how many characters you want to see: ").strip()

    if length_input.isdigit():
        length = int(length_input)
        fetch_html(url, length)
    else:
        print("Invalid number of characters.")
