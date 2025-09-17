#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 BUFFER OVERFLOW ANALYZER v1.0 — STATIC FILE ANALYSIS
Analyzes files (binaries, scripts, logs) for potential buffer overflow indicators.
Does NOT execute or exploit — static analysis only.
Saves detailed reports to ~/PyToolKit/PYSINT/results/
Professional, efficient, zero errors. Interactive + CLI flags.
"""

import os
import sys
import re
import argparse
import subprocess
import platform
from pathlib import Path
from datetime import datetime
import shutil

# ======================
# RICH UI SETUP
# ======================

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("❌ 'rich' not installed. Run: pip install rich")
    sys.exit(1)

console = Console()

# ======================
# CONFIG & PATHS
# ======================

BASE_DIR = Path.home() / "PyToolKit" / "PYSINT" / "results"
BASE_DIR.mkdir(parents=True, exist_ok=True)

# ======================
# PATTERN DATABASE
# ======================

UNSAFE_FUNCTIONS = [
    r"\bstrcpy\b", r"\bstrcat\b", r"\bgets\b", r"\bscanf\b", r"\bfgets\b",
    r"\bsprintf\b", r"\bsnprintf\b", r"\bmemcpy\b", r"\bmemmove\b", r"\bstrncpy\b",
    r"\bstrncat\b", r"\bvscanf\b", r"\bvsscanf\b", r"\bsscanf\b",
]

DANGEROUS_PATTERNS = [
    r"char\s+\w+\s*\[\s*\d{1,3}\s*\]",  # small static buffers: char buf[64]
    r"malloc\s*\(\s*\d{1,3}\s*\)",      # small malloc: malloc(128)
    r"alloca\s*\(",                     # stack allocation
    r"read\s*\(.*,\s*\d{1,3}\s*\)",     # read with small size
]

# ======================
# CORE UTILS
# ======================

def hash_file(filepath: str) -> str:
    import hashlib
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]
    except Exception as e:
        return "error_" + str(hash(filepath))[:10]

def is_binary_file(filepath: str) -> bool:
    """Check if file is binary (not text)."""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
            text_chars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
            return bool(chunk.translate(None, text_chars))
    except:
        return False

def check_file_exists(filepath: str) -> bool:
    return os.path.exists(filepath) and os.path.isfile(filepath)

# ======================
# ANALYSIS ENGINE
# ======================

def analyze_text_file(filepath: str):
    """Analyze text-based files (source code, scripts, logs)."""
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        total_lines = len(lines)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("🔍 Scanning text file...", total=total_lines)

            for i, line in enumerate(lines, 1):
                line_num = i
                content = line.strip()

                # Check for unsafe functions
                for pattern in UNSAFE_FUNCTIONS:
                    if re.search(pattern, content):
                        findings.append({
                            "type": "unsafe_function",
                            "line": line_num,
                            "content": content,
                            "pattern": pattern,
                            "risk": "HIGH",
                            "description": f"Use of potentially unsafe function: {pattern}"
                        })

                # Check for dangerous patterns
                for pattern in DANGEROUS_PATTERNS:
                    if re.search(pattern, content):
                        findings.append({
                            "type": "dangerous_pattern",
                            "line": line_num,
                            "content": content,
                            "pattern": pattern,
                            "risk": "MEDIUM",
                            "description": f"Dangerous pattern detected: {pattern}"
                        })

                progress.update(task, advance=1)

    except Exception as e:
        findings.append({
            "type": "error",
            "line": 0,
            "content": str(e),
            "pattern": "N/A",
            "risk": "ERROR",
            "description": f"Failed to analyze file: {e}"
        })

    return findings

def analyze_binary_file(filepath: str):
    """Analyze binary files using strings + pattern matching."""
    findings = []
    try:
        # Extract strings from binary
        result = subprocess.run(["strings", filepath], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception("strings command failed")

        lines = result.stdout.splitlines()
        total_lines = len(lines)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("🧬 Extracting strings from binary...", total=total_lines)

            for i, line in enumerate(lines, 1):
                content = line.strip()

                # Look for error messages or debug strings that indicate BOF
                if any(kw in content.lower() for kw in ["stack smashing", "buffer overflow", "corrupted", "overrun"]):
                    findings.append({
                        "type": "binary_string",
                        "line": i,
                        "content": content,
                        "pattern": "error_keyword",
                        "risk": "HIGH",
                        "description": "Error/debug string indicating possible buffer overflow"
                    })

                # Look for format strings that might be exploitable
                if re.search(r"%[0-9]*[sdxc]", content) and len(content) > 20:
                    findings.append({
                        "type": "format_string",
                        "line": i,
                        "content": content,
                        "pattern": "format_string",
                        "risk": "MEDIUM",
                        "description": "Long string with format specifiers — possible format string vulnerability"
                    })

                progress.update(task, advance=1)

    except FileNotFoundError:
        findings.append({
            "type": "error",
            "line": 0,
            "content": "strings command not found",
            "pattern": "N/A",
            "risk": "ERROR",
            "description": "Install 'strings' tool (usually part of binutils)"
        })
    except Exception as e:
        findings.append({
            "type": "error",
            "line": 0,
            "content": str(e),
            "pattern": "N/A",
            "risk": "ERROR",
            "description": f"Failed to analyze binary: {e}"
        })

    return findings

def run_analysis(filepath: str):
    """Main analysis dispatcher."""
    if is_binary_file(filepath):
        console.print("[bold blue]🧬 Detected as BINARY file. Extracting strings...[/bold blue]")
        return analyze_binary_file(filepath)
    else:
        console.print("[bold blue]📄 Detected as TEXT file. Scanning line by line...[/bold blue]")
        return analyze_text_file(filepath)

# ======================
# REPORTING
# ======================

def save_results(filepath: str, findings: list):
    """Save results to structured directory."""
    file_hash = hash_file(filepath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = BASE_DIR / f"bufferoverflow_{file_hash}_{timestamp}"
    dir_name.mkdir(exist_ok=True)

    # Copy original file for reference
    try:
        shutil.copy2(filepath, dir_name / "original_file")
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not copy original file: {e}[/yellow]")

    # Save findings
    results = {
        "target_file": filepath,
        "file_hash": file_hash,
        "analyzed_at": datetime.utcnow().isoformat() + "Z",
        "tool": "BUFFER OVERFLOW ANALYZER v1.0",
        "total_findings": len([f for f in findings if f.get("risk") not in ["ERROR"]]),
        "findings": findings
    }

    with open(dir_name / "FINDINGS.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    generate_report(filepath, findings, dir_name)
    return dir_name

def generate_report(filepath: str, findings: list, output_dir: Path):
    """Generate human-readable report."""
    lines = [
        "# 🔥 BUFFER OVERFLOW ANALYZER v1.0 — STATIC ANALYSIS REPORT",
        "="*70,
        f"🎯 TARGET FILE: {filepath}",
        f"📅 ANALYZED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"📂 OUTPUT: {output_dir}",
        f"🧮 TOTAL FINDINGS: {len([f for f in findings if f.get('risk') not in ['ERROR']])}",
        "="*70,
        ""
    ]

    if not findings:
        lines.append("✅ No potential buffer overflow indicators found.")
    else:
        for finding in findings:
            if finding.get("risk") == "ERROR":
                lines.append(f"❌ [ERROR] {finding.get('description')}")
            else:
                lines.append(f"## 🔍 Finding at line {finding.get('line', 'N/A')}")
                lines.append(f"- **Type**: {finding.get('type', 'N/A')}")
                lines.append(f"- **Risk**: {finding.get('risk', 'N/A')}")
                lines.append(f"- **Pattern**: `{finding.get('pattern', 'N/A')}`")
                lines.append(f"- **Content**: `{finding.get('content', 'N/A')[:200]}`")
                lines.append("")

    report_path = output_dir / "REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    console.print(f"\n📄 [bold green]FULL REPORT SAVED TO:[/bold green] [cyan]{report_path}[/cyan]")

    # Also print summary to console
    table = Table(title="✅ ANALYSIS SUMMARY", box=box.ROUNDED)
    table.add_column("Line", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Risk", style="bold")
    table.add_column("Snippet", style="dim")

    for finding in findings:
        if finding.get("risk") != "ERROR":
            line = str(finding.get("line", "?"))
            ftype = finding.get("type", "unknown")[:15]
            risk = finding.get("risk", "INFO")
            snippet = finding.get("content", "")[:50]
            table.add_row(line, ftype, risk, snippet)

    console.print("\n", table)

# ======================
# INTERACTIVE & CLI
# ======================

def analyze_single_file(filepath: str):
    """Main function to analyze a single file."""
    if not check_file_exists(filepath):
        console.print(f"[red]❌ File not found: {filepath}[/red]")
        return

    console.print(Panel.fit(
        f"[bold blue]🚀 Starting Buffer Overflow Analysis on:[/bold blue]\n[cyan]{filepath}[/cyan]",
        border_style="blue"
    ))

    findings = run_analysis(filepath)
    output_dir = save_results(filepath, findings)

    console.print(f"\n🎉 [bold green]Analysis complete![/bold green]")
    console.print(f"📂 Results saved to: [bold cyan]{output_dir}[/bold cyan]")

def main():
    parser = argparse.ArgumentParser(description="Buffer Overflow Static Analyzer")
    parser.add_argument("--file", "-f", help="Path to file to analyze")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive mode")

    args = parser.parse_args()

    if args.interactive:
        console.print(Panel.fit(
            "[bold red]🔥 BUFFER OVERFLOW ANALYZER v1.0[/bold red]\n"
            "[dim]Static Analysis Only — No Execution — No Risk[/dim]",
            border_style="red"
        ))

        while True:
            filepath = Prompt.ask("\n[bold green]➡️  Enter file path to analyze (or 'quit' to exit)[/bold green]").strip()
            if filepath.lower() in ['quit', 'exit', 'q']:
                break
            if filepath:
                analyze_single_file(filepath)
            else:
                console.print("[yellow]Please enter a valid file path.[/yellow]")

        console.print("\n[bold green]👋 Thank you for using Buffer Overflow Analyzer![/bold green]")

    elif args.file:
        analyze_single_file(args.file)
    else:
        console.print("[yellow]No file provided. Use --interactive or --file.[/yellow]")
        console.print("Example: python bufferoverflow-analyzer.py -f /path/to/file")

# ======================
# ENTRY POINT
# ======================

if __name__ == "__main__":
    try:
        import json  # needed for save_results
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow bold]🛑 Interrupted by user.[/yellow bold]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red bold]💥 Fatal error:[/red bold] {e}")
        sys.exit(1)
