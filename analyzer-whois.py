import whois
from ipwhois import IPWhois

def URL():
    try:
        url = input("enter your URL: ")
        info = whois.whois(url)
        print(info)
    except Exception as e:
        print("ERRO! INVALID URL:", e)

def IP():
    try:
        ip = input("put your IP: ")
        obj = IPWhois(ip)
        res = obj.lookup_rdap()
        print(res)
    except Exception as e:
        print("ERROR! INVALID IP:", e)

def main():
    what = input("DO YOU WANT TO CHECK IP OR URL?: ").strip().lower()
    
    if what == "url":
        URL()
    elif what == "ip":
        IP()
    else:
        print("INVALID COMMAND!")

if __name__ == "__main__":
    main()
