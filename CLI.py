import subprocess
import sys

MODULES = {
    "1": ("Whois/IP Lookup", "python analyzer-whois.py"),
    "2": ("DNS Lookup", "python dns-hunter.py"),
    "3": ("HTML Scraper", "python get-html.py"),
    "4": ("Email Extractor", "python find-email-in-html.py"),
    "5": ("Subdomain Finder", "python subdomain-finder.py"),
    "6": ("Parameter Scanner", "python param-finder.py"),
    "7": ("Directory / File Scanner", "python directory-fuzzer.py"),
    "8": ("SSL/TLS Info", "python ssl-info.py"),
    "9": ("HTTP Headers", "python headers.py"),
    "10": ("Wayback / Archive Lookup", "python wayback-Scan.py"),
    "11": ("Technology / CMS Detection", "python tech-detector.py"),
    "12": ("Port / Service Scanner", "python port-scan.py"),
    "0": ("Exit", None)
}

def main():
    while True:
        print("\n=== Master OSINT Scanner ===\n")
        for key, (name, _) in MODULES.items():
            print(f"{key} - {name}")
        choice = input("\nSelect an option: ").strip()
        
        if choice == "0":
            print("Exiting...")
            sys.exit(0)
        
        if choice in MODULES:
            name, command = MODULES[choice]
            print(f"\n🔹 Running {name}...\n")
            try:
                subprocess.run(command, shell=True)
            except Exception as e:
                print(f"Error running module {name}: {e}")
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
