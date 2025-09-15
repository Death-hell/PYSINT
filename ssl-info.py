import ssl
import socket
from datetime import datetime

def get_ssl_info(domain, port=443):
    context = ssl.create_default_context()

    with socket.create_connection((domain, port)) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            
            # Subject
            subject = dict(x[0] for x in cert.get('subject', ()))
            print(f"Subject: {subject.get('commonName', '')}")
            
            # Issuer
            issuer = dict(x[0] for x in cert.get('issuer', ()))
            print(f"Issuer: {issuer.get('commonName', '')}")
            
            # Validity
            not_before = datetime.strptime(cert['notBefore'], "%b %d %H:%M:%S %Y %Z")
            not_after = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
            print(f"Valid From: {not_before}")
            print(f"Valid Until: {not_after}")
            
            # SANs
            sans = cert.get('subjectAltName', ())
            san_list = [x[1] for x in sans]
            print(f"Subject Alternative Names: {', '.join(san_list)}")
            
            # TLS version
            tls_version = ssock.version()
            print(f"TLS Version: {tls_version}")

if __name__ == "__main__":
    domain = input("Enter the website domain (without https://): ").strip()
    try:
        get_ssl_info(domain)
    except Exception as e:
        print(f"Error fetching SSL info: {e}")
