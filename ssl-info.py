import ssl
import socket
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

def get_ssl_info(domain, port=443):
    context = ssl.create_default_context()
    try:
        with socket.create_connection((domain, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

                # Subject
                subject = dict(x[0] for x in cert.get('subject', ()))
                common_name = subject.get('commonName', '')

                # Issuer
                issuer = dict(x[0] for x in cert.get('issuer', ()))
                issuer_name = issuer.get('commonName', '')

                # Validity
                not_before = datetime.strptime(cert['notBefore'], "%b %d %H:%M:%S %Y %Z")
                not_after = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")

                # SANs
                sans = cert.get('subjectAltName', ())
                san_list = [x[1] for x in sans] if sans else []

                # TLS version
                tls_version = ssock.version()

                # Exibir informações em tabela
                table = Table(title=f"SSL/TLS Info for {domain}", header_style="bold magenta")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="yellow")
                table.add_row("Common Name", common_name)
                table.add_row("Issuer", issuer_name)
                table.add_row("Valid From", str(not_before))
                table.add_row("Valid Until", str(not_after))
                table.add_row("SANs", ", ".join(san_list) if san_list else "-")
                table.add_row("TLS Version", tls_version if tls_version else "-")

                console.print(table)

    except socket.timeout:
        console.print(f"[red]Error: Connection to {domain}:{port} timed out[/red]")
    except socket.gaierror:
        console.print(f"[red]Error: Could not resolve host {domain}[/red]")
    except ssl.SSLError as e:
        console.print(f"[red]SSL Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")

def main():
    console.rule("[bold green]PYSINT SSL/TLS Scanner[/bold green]")
    domain = Prompt.ask("Enter the website domain (without https://)").strip()
    get_ssl_info(domain)

if __name__ == "__main__":
    main()
