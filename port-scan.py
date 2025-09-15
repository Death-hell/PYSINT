import socket
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

# Dicionário atualizado de portas comuns (port -> service)
COMMON_PORTS = {
    20: "FTP-Data", 21: "FTP", 22: "SSH", 23: "Telnet",
    25: "SMTP", 53: "DNS", 67: "DHCP", 68: "DHCP", 69: "TFTP",
    80: "HTTP", 110: "POP3", 111: "RPCBind", 123: "NTP",
    135: "MSRPC", 139: "NetBIOS", 143: "IMAP", 161: "SNMP",
    194: "IRC", 443: "HTTPS", 445: "SMB", 465: "SMTPS",
    587: "SMTP-Alt", 993: "IMAPS", 995: "POP3S", 1433: "MSSQL",
    1521: "Oracle", 1723: "PPTP", 2049: "NFS", 3306: "MySQL",
    3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 9000: "Webmin"
}

MAX_THREADS = 100  # Limite de threads simultâneas

def scan_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            result = s.connect_ex((host, port))
            if result == 0:
                service = COMMON_PORTS.get(port, "Unknown")
                console.print(f"[bold green][OPEN][/bold green] Port {port} -> {service}")
                return port, service
    except Exception:
        pass
    return None

def port_scan(host, ports):
    open_ports = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(scan_port, host, port) for port in ports]
        for f in futures:
            res = f.result()
            if res:
                open_ports.append(res)
    return open_ports

def main():
    console.rule("[bold green]PYSINT Port Scanner[/bold green]")
    host = Prompt.ask("[bold cyan]Enter the website or IP to scan[/bold cyan]").strip()

    try:
        ip = socket.gethostbyname(host)
        console.print(f"\nScanning [bold]{host}[/bold] ({ip}) for {len(COMMON_PORTS)} common ports...\n")
        found_ports = port_scan(ip, list(COMMON_PORTS.keys()))

        console.print(Panel(f"✅ Scan finished. Open ports: {len(found_ports)}", style="green"))
        if found_ports:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Port", style="cyan")
            table.add_column("Service", style="yellow")
            for port, service in found_ports:
                table.add_row(str(port), service)
            console.print(table)

    except socket.gaierror:
        console.print("[red]Error: Could not resolve host.[/red]")

if __name__ == "__main__":
    main()
