#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Metasploit Installer & Launcher
Author: YourName
Description:
    Detects OS (Termux, Linux, macOS, Windows),
    Installs Metasploit Framework using recommended scripts,
    Avoids leaving Git repositories behind,
    Provides user-friendly interface using Rich.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()

def detect_os():
    """Detect the operating system and environment."""
    if "ANDROID_ROOT" in os.environ:
        return "Termux"
    elif sys.platform.startswith("linux"):
        return "Linux"
    elif sys.platform.startswith("darwin"):
        return "macOS"
    elif sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
        return "Windows"
    else:
        return "Unknown"

def check_msf_installed():
    """Check if Metasploit is already installed."""
    return shutil.which("msfconsole") is not None

def run_command(cmd, shell=True):
    """Run a shell command and return True if successful."""
    try:
        subprocess.run(cmd, shell=shell, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def install_metasploit_termux():
    """Install Metasploit in Termux using the recommended script."""
    console.print("[cyan]Installing Metasploit in Termux...[/cyan]")
    
    # Ensure wget is installed
    run_command("pkg install -y wget")
    
    # Download the script
    run_command("wget -O metasploit.sh https://github.com/gushmazuko/metasploit_in_termux/raw/master/metasploit.sh")
    
    # Make it executable and run
    run_command("chmod +x metasploit.sh")
    run_command("./metasploit.sh")
    
    # Clean up
    os.remove("metasploit.sh")

def install_metasploit_linux_mac():
    """Install Metasploit on Linux or macOS from GitHub release scripts."""
    console.print("[cyan]Installing Metasploit...[/cyan]")
    tmp_dir = Path("/tmp/msf_install")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    os.chdir(tmp_dir)
    
    # Clone installer repo temporarily
    run_command("git clone https://github.com/471D38UNNUX/Metasploit-Framework-Installer.git .")
    
    # Run installation script
    run_command("chmod +x install.sh")
    run_command("./install.sh")
    
    # Clean up
    os.chdir("/")
    shutil.rmtree(tmp_dir)

def launch_metasploit():
    """Launch Metasploit Framework console."""
    console.print(Panel.fit("[green]Launching Metasploit Framework...[/green]"))
    os.system("msfconsole")

def main():
    console.print(Panel.fit("[bold yellow]Metasploit Installer & Launcher[/bold yellow]"))
    
    os_type = detect_os()
    console.print(f"[blue]Detected OS:[/blue] {os_type}")
    
    if check_msf_installed():
        console.print("[green]Metasploit is already installed.[/green]")
        launch_metasploit()
        sys.exit(0)
    
    if os_type == "Termux":
        install_metasploit_termux()
    elif os_type in ["Linux", "macOS"]:
        install_metasploit_linux_mac()
    else:
        console.print("[red]Unsupported OS. Exiting.[/red]")
        sys.exit(1)
    
    console.print("[green]Installation completed successfully![/green]")
    launch_metasploit()

if __name__ == "__main__":
    main()
