"""
K-LEAN CLI - Command line interface for K-LEAN installation and management.

Usage:
    k-lean install [--dev] [--component COMPONENT]
    k-lean uninstall
    k-lean status
    k-lean version
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from klean import __version__, CLAUDE_DIR, FACTORY_DIR, VENV_DIR, CONFIG_DIR, DATA_DIR

console = Console()


def get_source_data_dir() -> Path:
    """Get the source data directory - handles both editable and regular installs."""
    # In editable install, DATA_DIR points to src/klean/data
    # But we want the actual data from the repo root

    # Check if we're in an editable install by looking for the repo structure
    possible_repo = DATA_DIR.parent.parent.parent  # src/klean/data -> src/klean -> src -> repo

    # Look for data in multiple locations
    candidates = [
        DATA_DIR,  # Package data (regular install)
        possible_repo / "src" / "klean" / "data",  # Editable install with data in package
        Path(__file__).parent.parent.parent / "scripts",  # Legacy location during transition
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return DATA_DIR


def print_banner():
    """Print the K-LEAN banner."""
    console.print(Panel.fit(
        f"[bold cyan]K-LEAN Companion v{__version__}[/bold cyan]\n"
        "[dim]Multi-Model Code Review & Knowledge Capture System[/dim]",
        border_style="cyan"
    ))


def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def copy_files(src: Path, dst: Path, pattern: str = "*", symlink: bool = False) -> int:
    """Copy or symlink files from source to destination."""
    ensure_dir(dst)
    count = 0

    if not src.exists():
        console.print(f"[yellow]Warning: Source not found: {src}[/yellow]")
        return 0

    for item in src.glob(pattern):
        if item.is_file():
            dst_file = dst / item.name
            if symlink:
                # Remove existing file/symlink
                if dst_file.exists() or dst_file.is_symlink():
                    dst_file.unlink()
                dst_file.symlink_to(item.resolve())
            else:
                shutil.copy2(item, dst_file)
            count += 1
        elif item.is_dir() and pattern == "*":
            # Recursively copy directories
            dst_subdir = dst / item.name
            if symlink:
                if dst_subdir.exists() or dst_subdir.is_symlink():
                    if dst_subdir.is_symlink():
                        dst_subdir.unlink()
                    else:
                        shutil.rmtree(dst_subdir)
                dst_subdir.symlink_to(item.resolve())
            else:
                if dst_subdir.exists():
                    shutil.rmtree(dst_subdir)
                shutil.copytree(item, dst_subdir)
            count += 1

    return count


def make_executable(path: Path) -> None:
    """Make shell scripts executable."""
    for script in path.glob("*.sh"):
        script.chmod(script.stat().st_mode | 0o111)


def check_litellm() -> bool:
    """Check if LiteLLM proxy is running."""
    try:
        import urllib.request
        import json
        # Try /models endpoint which LiteLLM supports
        req = urllib.request.Request("http://localhost:4000/models")
        response = urllib.request.urlopen(req, timeout=2)
        data = json.loads(response.read().decode())
        return isinstance(data, dict) and "data" in data
    except Exception:
        return False


def check_command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(cmd) is not None


def check_knowledge_server() -> bool:
    """Check if knowledge server is running via socket."""
    try:
        socket_path = Path("/tmp/knowledge-server.sock")
        return socket_path.exists() and socket_path.is_socket()
    except Exception:
        return False


def start_knowledge_server() -> bool:
    """Start knowledge server in background if not running."""
    if check_knowledge_server():
        return True  # Already running

    try:
        knowledge_script = CLAUDE_DIR / "scripts" / "knowledge-server.py"
        if not knowledge_script.exists():
            return False

        # Start server in background
        subprocess.Popen(
            [sys.executable, str(knowledge_script), "start"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach from parent process
        )

        # Wait for socket to appear (max 3 seconds)
        for _ in range(30):
            time.sleep(0.1)
            if check_knowledge_server():
                return True

        return False
    except Exception:
        return False


def ensure_knowledge_server() -> None:
    """Ensure knowledge server is running, start if needed (silent)."""
    if not check_knowledge_server():
        start_knowledge_server()


@click.group()
@click.version_option(version=__version__, prog_name="k-lean")
def main():
    """K-LEAN: Multi-model code review and knowledge capture system for Claude Code."""
    # Auto-start knowledge server if not running
    ensure_knowledge_server()


@main.command()
@click.option("--dev", is_flag=True, help="Development mode: use symlinks instead of copies")
@click.option("--component", "-c",
              type=click.Choice(["all", "scripts", "commands", "hooks", "droids", "config", "knowledge"]),
              default="all", help="Component to install")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
def install(dev: bool, component: str, yes: bool):
    """Install K-LEAN components to ~/.claude/"""
    print_banner()

    mode = "development (symlinks)" if dev else "production (copies)"
    console.print(f"\n[bold]Installation Mode:[/bold] {mode}")

    # Determine source directory
    # For development, use the repo's actual directories
    if dev:
        # Find the repo root (parent of src/)
        repo_root = Path(__file__).parent.parent.parent
        source_scripts = repo_root / "scripts"
        source_commands = repo_root / "commands"
        source_commands_kln = repo_root / "commands-kln"
        source_hooks = repo_root / "hooks"
        source_droids = repo_root / "droids"
        source_config = repo_root / "config"
        source_lib = repo_root / "lib"
    else:
        # Production: use package data directory
        source_base = DATA_DIR
        source_scripts = source_base / "scripts"
        source_commands = source_base / "commands"
        source_commands_kln = source_base / "commands" / "kln"
        source_hooks = source_base / "hooks"
        source_droids = source_base / "droids"
        source_config = source_base / "config"
        source_lib = source_base / "lib"

    console.print(f"[dim]Source: {source_scripts.parent}[/dim]\n")

    if not yes and not click.confirm("Proceed with installation?"):
        console.print("[yellow]Installation cancelled[/yellow]")
        return

    installed = {}

    # Install scripts
    if component in ["all", "scripts"]:
        console.print("[bold]Installing scripts...[/bold]")
        scripts_dst = CLAUDE_DIR / "scripts"

        # Also copy lib/ for common.sh dependency
        if source_lib.exists():
            lib_dst = CLAUDE_DIR / "lib"
            count = copy_files(source_lib, lib_dst, "*.sh", symlink=dev)
            make_executable(lib_dst)

        if source_scripts.exists():
            count = copy_files(source_scripts, scripts_dst, "*.sh", symlink=dev)
            count += copy_files(source_scripts, scripts_dst, "*.py", symlink=dev)
            make_executable(scripts_dst)
            installed["scripts"] = count
            console.print(f"  [green]Installed {count} scripts[/green]")
        else:
            console.print(f"  [yellow]Scripts source not found: {source_scripts}[/yellow]")

    # Install commands
    if component in ["all", "commands"]:
        console.print("[bold]Installing slash commands...[/bold]")

        # KLN commands
        kln_dst = CLAUDE_DIR / "commands" / "kln"
        if source_commands_kln.exists():
            count = copy_files(source_commands_kln, kln_dst, "*.md", symlink=dev)
            installed["commands_kln"] = count
            console.print(f"  [green]Installed {count} /kln: commands[/green]")

        # SC commands are optional and from external system - skip by default
        # Users can manage SC commands separately

    # Install hooks
    if component in ["all", "hooks"]:
        console.print("[bold]Installing hooks...[/bold]")
        hooks_dst = CLAUDE_DIR / "hooks"
        if source_hooks.exists():
            count = copy_files(source_hooks, hooks_dst, "*.sh", symlink=dev)
            make_executable(hooks_dst)
            installed["hooks"] = count
            console.print(f"  [green]Installed {count} hooks[/green]")
        else:
            console.print(f"  [yellow]Hooks source not found[/yellow]")

    # Install droids
    if component in ["all", "droids"]:
        console.print("[bold]Installing Factory Droid specialists...[/bold]")
        droids_dst = FACTORY_DIR / "droids"
        if source_droids.exists():
            count = copy_files(source_droids, droids_dst, "*.md", symlink=dev)
            installed["droids"] = count
            console.print(f"  [green]Installed {count} droids[/green]")
        else:
            console.print(f"  [yellow]Droids source not found[/yellow]")

    # Install config
    if component in ["all", "config"]:
        console.print("[bold]Installing configuration...[/bold]")

        # CLAUDE.md
        claude_md_src = source_config / "CLAUDE.md" if not dev else source_config.parent / "config" / "CLAUDE.md"
        if not dev:
            claude_md_src = source_base / "config" / "CLAUDE.md"
        else:
            claude_md_src = source_scripts.parent / "config" / "CLAUDE.md"

        if claude_md_src.exists():
            claude_md_dst = CLAUDE_DIR / "CLAUDE.md"
            if dev:
                if claude_md_dst.exists() or claude_md_dst.is_symlink():
                    claude_md_dst.unlink()
                claude_md_dst.symlink_to(claude_md_src.resolve())
            else:
                shutil.copy2(claude_md_src, claude_md_dst)
            console.print("  [green]Installed CLAUDE.md[/green]")

        # LiteLLM config
        litellm_src = source_config / "litellm" if not dev else source_scripts.parent / "config" / "litellm"
        if litellm_src.exists():
            ensure_dir(CONFIG_DIR)
            for cfg_file in litellm_src.glob("*.yaml"):
                dst = CONFIG_DIR / cfg_file.name
                if dev:
                    if dst.exists() or dst.is_symlink():
                        dst.unlink()
                    dst.symlink_to(cfg_file.resolve())
                else:
                    shutil.copy2(cfg_file, dst)
            console.print("  [green]Installed LiteLLM configs[/green]")

    # Install knowledge system
    if component in ["all", "knowledge"]:
        console.print("[bold]Setting up knowledge database...[/bold]")
        if not VENV_DIR.exists():
            console.print("  Creating Python virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)

        # Install dependencies
        pip = VENV_DIR / "bin" / "pip"
        if pip.exists():
            console.print("  Installing Python dependencies...")
            subprocess.run(
                [str(pip), "install", "-q", "--upgrade", "pip"],
                capture_output=True
            )
            result = subprocess.run(
                [str(pip), "install", "-q", "txtai", "sentence-transformers"],
                capture_output=True
            )
            if result.returncode == 0:
                console.print("  [green]Knowledge database ready[/green]")
            else:
                console.print("  [yellow]Warning: Some dependencies may not have installed[/yellow]")

    # Summary
    console.print("\n[bold green]Installation complete![/bold green]")

    if dev:
        console.print("\n[cyan]Development mode:[/cyan] Files are symlinked to source.")
        console.print("Edit source files and changes will be immediately available.")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Reload shell: [cyan]source ~/.bashrc[/cyan]")
    console.print("  2. Start LiteLLM: [cyan]~/.claude/scripts/litellm-start.sh[/cyan]")
    console.print("  3. Verify: [cyan]k-lean status[/cyan]")


@main.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
def uninstall(yes: bool):
    """Remove K-LEAN components from ~/.claude/"""
    print_banner()

    console.print("\n[bold yellow]This will remove K-LEAN components[/bold yellow]")
    console.print("Components to remove:")
    console.print("  - ~/.claude/scripts/")
    console.print("  - ~/.claude/commands/kln/")
    console.print("  - ~/.claude/hooks/")
    console.print("  - ~/.factory/droids/")

    if not yes and not click.confirm("\nProceed with uninstallation?"):
        console.print("[yellow]Uninstallation cancelled[/yellow]")
        return

    # Create backup directory
    backup_dir = CLAUDE_DIR / "backups" / f"k-lean-{__version__}"
    ensure_dir(backup_dir)

    # Backup and remove
    removed = []

    for path in [
        CLAUDE_DIR / "scripts",
        CLAUDE_DIR / "commands" / "kln",
        CLAUDE_DIR / "hooks",
    ]:
        if path.exists():
            backup_path = backup_dir / path.name
            if path.is_symlink():
                path.unlink()
            else:
                shutil.move(str(path), str(backup_path))
            removed.append(str(path))

    console.print(f"\n[green]Removed {len(removed)} components[/green]")
    console.print(f"[dim]Backups saved to: {backup_dir}[/dim]")


@main.command()
def status():
    """Show K-LEAN installation status and health."""
    print_banner()

    table = Table(title="Component Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    # Scripts
    scripts_dir = CLAUDE_DIR / "scripts"
    if scripts_dir.exists():
        count = len(list(scripts_dir.glob("*.sh")))
        is_symlink = any(f.is_symlink() for f in scripts_dir.glob("*.sh"))
        mode = "(symlinked)" if is_symlink else "(copied)"
        table.add_row("Scripts", f"OK ({count})", mode)
    else:
        table.add_row("Scripts", "[red]NOT INSTALLED[/red]", "")

    # Commands
    kln_dir = CLAUDE_DIR / "commands" / "kln"
    if kln_dir.exists():
        count = len(list(kln_dir.glob("*.md")))
        table.add_row("KLN Commands", f"OK ({count})", "/kln:help")
    else:
        table.add_row("KLN Commands", "[red]NOT INSTALLED[/red]", "")

    # SC commands (external system - informational only)
    sc_dir = CLAUDE_DIR / "commands" / "sc"
    if sc_dir.exists():
        count = len(list(sc_dir.glob("*.md")))
        table.add_row("SC Commands", f"OK ({count})", "(external)")
    else:
        table.add_row("SC Commands", "[dim]NOT AVAILABLE[/dim]", "(external system)")

    # Hooks
    hooks_dir = CLAUDE_DIR / "hooks"
    if hooks_dir.exists():
        count = len(list(hooks_dir.glob("*.sh")))
        table.add_row("Hooks", f"OK ({count})", "")
    else:
        table.add_row("Hooks", "[yellow]NOT INSTALLED[/yellow]", "optional")

    # Droids
    droids_dir = FACTORY_DIR / "droids"
    if droids_dir.exists():
        count = len(list(droids_dir.glob("*.md")))
        table.add_row("Factory Droids", f"OK ({count})", "")
    else:
        table.add_row("Factory Droids", "[yellow]NOT INSTALLED[/yellow]", "optional")

    # CLAUDE.md
    claude_md = CLAUDE_DIR / "CLAUDE.md"
    if claude_md.exists():
        is_symlink = claude_md.is_symlink()
        mode = "(symlinked)" if is_symlink else "(copied)"
        table.add_row("CLAUDE.md", "OK", mode)
    else:
        table.add_row("CLAUDE.md", "[red]NOT FOUND[/red]", "")

    # Knowledge DB
    if VENV_DIR.exists():
        python = VENV_DIR / "bin" / "python"
        try:
            result = subprocess.run(
                [str(python), "-c", "import txtai; print('ok')"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                table.add_row("Knowledge DB", "[green]OK[/green]", str(VENV_DIR))
            else:
                # txtai import failed, still check if it exists
                result2 = subprocess.run(
                    [str(python), "-m", "pip", "show", "txtai"],
                    capture_output=True, text=True, timeout=5
                )
                if result2.returncode == 0:
                    table.add_row("Knowledge DB", "[green]OK[/green]", "(installed, import check failed)")
                else:
                    table.add_row("Knowledge DB", "[yellow]PARTIAL[/yellow]", "txtai not installed")
        except subprocess.TimeoutExpired:
            table.add_row("Knowledge DB", "[green]OK[/green]", "(check timeout, likely running)")
        except Exception as e:
            table.add_row("Knowledge DB", "[yellow]PARTIAL[/yellow]", f"check error: {str(e)[:20]}")
    else:
        table.add_row("Knowledge DB", "[yellow]NOT INSTALLED[/yellow]", "run: k-lean install")

    # LiteLLM
    if check_litellm():
        table.add_row("LiteLLM Proxy", "[green]RUNNING[/green]", "localhost:4000")
    else:
        table.add_row("LiteLLM Proxy", "[yellow]NOT RUNNING[/yellow]", "start with litellm-start.sh")

    # Factory Droid CLI
    if check_command_exists("droid"):
        result = subprocess.run(["droid", "--version"], capture_output=True, text=True)
        version = result.stdout.strip() if result.returncode == 0 else "unknown"
        table.add_row("Factory Droid CLI", "OK", version)
    else:
        table.add_row("Factory Droid CLI", "[yellow]NOT INSTALLED[/yellow]", "optional")

    console.print(table)

    # Installation mode detection
    console.print("\n[bold]Installation Info:[/bold]")
    console.print(f"  Version: {__version__}")
    console.print(f"  Claude Dir: {CLAUDE_DIR}")

    # Check if running in dev mode (symlinks present)
    if scripts_dir.exists():
        sample_script = next(scripts_dir.glob("*.sh"), None)
        if sample_script and sample_script.is_symlink():
            target = sample_script.resolve().parent.parent
            console.print(f"  Mode: [cyan]Development (symlinked to {target})[/cyan]")
        else:
            console.print("  Mode: Production (files copied)")


@main.command()
def version():
    """Show K-LEAN version information."""
    console.print(f"K-LEAN version {__version__}")
    console.print(f"Python: {sys.version}")
    console.print(f"Install path: {Path(__file__).parent}")


@main.command()
def doctor():
    """Diagnose common issues with K-LEAN installation."""
    print_banner()
    console.print("\n[bold]Running diagnostics...[/bold]\n")

    issues = []

    # Check Claude directory
    if not CLAUDE_DIR.exists():
        issues.append(("CRITICAL", "~/.claude directory does not exist"))

    # Check scripts
    scripts_dir = CLAUDE_DIR / "scripts"
    if scripts_dir.exists():
        # Check key scripts
        key_scripts = ["quick-review.sh", "deep-review.sh", "droid-execute.sh"]
        for script in key_scripts:
            script_path = scripts_dir / script
            if not script_path.exists():
                issues.append(("WARNING", f"Missing script: {script}"))
            elif not os.access(script_path, os.X_OK):
                issues.append(("WARNING", f"Script not executable: {script}"))
    else:
        issues.append(("ERROR", "Scripts directory not found"))

    # Check lib/common.sh
    common_sh = CLAUDE_DIR / "lib" / "common.sh"
    if not common_sh.exists():
        issues.append(("WARNING", "lib/common.sh not found - scripts may fail"))

    # Check LiteLLM config
    if CONFIG_DIR.exists():
        if not (CONFIG_DIR / "config.yaml").exists():
            issues.append(("INFO", "LiteLLM config.yaml not found - run setup-litellm.sh"))

    # Check Python venv
    if VENV_DIR.exists():
        python = VENV_DIR / "bin" / "python"
        if not python.exists():
            issues.append(("ERROR", "Knowledge DB venv is broken - recreate with k-lean install"))

    # Check for broken symlinks
    for check_dir in [scripts_dir, CLAUDE_DIR / "commands" / "kln", CLAUDE_DIR / "hooks"]:
        if check_dir.exists():
            for item in check_dir.iterdir():
                if item.is_symlink() and not item.resolve().exists():
                    issues.append(("ERROR", f"Broken symlink: {item}"))

    # Report
    if not issues:
        console.print("[green]No issues found![/green]")
    else:
        for level, message in issues:
            if level == "CRITICAL":
                console.print(f"[bold red]CRITICAL:[/bold red] {message}")
            elif level == "ERROR":
                console.print(f"[red]ERROR:[/red] {message}")
            elif level == "WARNING":
                console.print(f"[yellow]WARNING:[/yellow] {message}")
            else:
                console.print(f"[blue]INFO:[/blue] {message}")

        console.print(f"\n[bold]Found {len(issues)} issue(s)[/bold]")
        console.print("Run [cyan]k-lean install --dev[/cyan] to fix most issues")


if __name__ == "__main__":
    main()
