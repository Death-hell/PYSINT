import socket
from concurrent.futures import ThreadPoolExecutor

# Dicionário simples de serviços comuns (port -> service)
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 3306: "MySQL", 3389: "RDP", 8080: "HTTP-Alt"
}

def scan_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            if result == 0:
                service = COMMON_PORTS.get(port, "Unknown")
                print(f"[OPEN] Port {port} -> {service}")
                return port, service
    except Exception:
        pass
    return None

def port_scan(host, ports):
    open_ports = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(scan_port, host, port) for port in ports]
        for f in futures:
            res = f.result()
            if res:
                open_ports.append(res)
    return open_ports

if __name__ == "__main__":
    host = input("Enter the website or IP to scan: ").strip()
    try:
        ip = socket.gethostbyname(host)
        print(f"\nScanning {host} ({ip}) for common ports...\n")
        ports_to_scan = list(COMMON_PORTS.keys())
        found_ports = port_scan(ip, ports_to_scan)

        print(f"\n✅ Scan finished. Open ports ({len(found_ports)}):")
        for port, service in found_ports:
            print(f"{port} -> {service}")

    except socket.gaierror:
        print("Error: Could not resolve host.")
