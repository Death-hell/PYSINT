import dns.resolver

def query_dns(domain):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # Google e Cloudflare

    record_types = ["A", "MX", "NS", "TXT", "CNAME"]
    for rtype in record_types:
        try:
            answers = resolver.resolve(domain, rtype)
            print(f"\n{rtype} records for {domain}:")
            for rdata in answers:
                print(rdata.to_text())
        except dns.resolver.NoAnswer:
            print(f"\n{rtype} records for {domain}: No answer")
        except dns.resolver.NXDOMAIN:
            print(f"\n{rtype} records for {domain}: Domain does not exist")
        except Exception as e:
            print(f"\n{rtype} records for {domain}: Error - {e}")

if __name__ == "__main__":
    domain = input("Enter the domain you want to check DNS records for: ").strip()
    query_dns(domain)
