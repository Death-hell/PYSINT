import httpx
import re

def find_emails(url):
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", response.text)

        if emails:
            print(f"\nEmails found on {url}:")
            for email in set(emails):
                print(email)
        else:
            print(f"\nNo emails found on {url}.")

    except httpx.RequestError as e:
        print("Error accessing the website:", e)
    except httpx.HTTPStatusError as e:
        print("HTTP error:", e)

if __name__ == "__main__":
    url = input("Enter the URL of the website to search for emails: ").strip()
    find_emails(url)
