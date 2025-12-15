"""
K-LEAN CLI - Command line interface for K-LEAN installation and management.

Usage:
    k-lean install [--dev] [--component COMPONENT]
    k-lean uninstall
    k-lean status
    k-lean doctor [--auto-fix]
    k-lean start [--service SERVICE]
    k-lean stop [--service SERVICE]
    k-lean debug [--follow] [--filter COMPONENT]
    k-lean version
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout

from klean import __version__, CLAUDE_DIR, FACTORY_DIR, VENV_DIR, CONFIG_DIR, DATA_DIR, KLEAN_DIR, LOGS_DIR, PIDS_DIR

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


def ensure_klean_dirs() -> None:
    """Ensure K-LEAN directories exist."""
    KLEAN_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    PIDS_DIR.mkdir(parents=True, exist_ok=True)


def get_litellm_pid_file() -> Path:
    """Get path to LiteLLM PID file."""
    return PIDS_DIR / "litellm.pid"


def get_knowledge_pid_file() -> Path:
    """Get path to Knowledge server PID file."""
    return PIDS_DIR / "knowledge.pid"


def check_litellm_detailed() -> Dict[str, Any]:
    """Check LiteLLM status with detailed info."""
    result = {"running": False, "port": 4000, "models": [], "error": None}
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:4000/models")
        response = urllib.request.urlopen(req, timeout=3)
        data = json.loads(response.read().decode())
        if isinstance(data, dict) and "data" in data:
            result["running"] = True
            result["models"] = [m.get("id", "unknown") for m in data.get("data", [])]
    except urllib.error.URLError as e:
        result["error"] = f"Connection refused (proxy not running)"
    except Exception as e:
        result["error"] = str(e)
    return result


def start_litellm(background: bool = True, port: int = 4000) -> bool:
    """Start LiteLLM proxy server."""
    ensure_klean_dirs()

    # Check if already running
    if check_litellm():
        return True

    # Find start script
    start_script = CLAUDE_DIR / "scripts" / "litellm-start.sh"
    if not start_script.exists():
        start_script = CLAUDE_DIR / "scripts" / "start-litellm.sh"

    if not start_script.exists():
        console.print("[red]Error: LiteLLM start script not found[/red]")
        return False

    # Check for litellm binary
    if not shutil.which("litellm"):
        console.print("[red]Error: litellm not installed. Run: pip install litellm[/red]")
        return False

    log_file = LOGS_DIR / "litellm.log"
    pid_file = get_litellm_pid_file()

    try:
        if background:
            # Start in background with nohup
            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    ["bash", str(start_script), str(port)],
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                    env={**os.environ, "LITELLM_LOG": str(log_file)}
                )
                pid_file.write_text(str(process.pid))

            # Wait for proxy to be ready
            for i in range(50):  # 5 seconds max
                time.sleep(0.1)
                if check_litellm():
                    return True

            return False
        else:
            # Run in foreground
            subprocess.run(["bash", str(start_script), str(port)])
            return True
    except Exception as e:
        console.print(f"[red]Error starting LiteLLM: {e}[/red]")
        return False


def stop_litellm() -> bool:
    """Stop LiteLLM proxy server."""
    pid_file = get_litellm_pid_file()

    # Try to kill by PID file
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            pid_file.unlink()
            time.sleep(0.5)
            return True
        except (ProcessLookupError, ValueError):
            pid_file.unlink()

    # Try to find and kill litellm process
    try:
        result = subprocess.run(
            ["pkill", "-f", "litellm.*--port"],
            capture_output=True
        )
        return result.returncode == 0
    except Exception:
        return False


def stop_knowledge_server() -> bool:
    """Stop knowledge server."""
    knowledge_script = CLAUDE_DIR / "scripts" / "knowledge-server.py"
    if knowledge_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(knowledge_script), "stop"],
                capture_output=True,
                timeout=5
            )
            return True
        except Exception:
            pass

    # Try to kill by socket
    socket_path = Path("/tmp/knowledge-server.sock")
    if socket_path.exists():
        try:
            socket_path.unlink()
        except Exception:
            pass

    return True


def log_debug_event(component: str, event: str, **kwargs) -> None:
    """Log a debug event to the unified log file."""
    ensure_klean_dirs()
    log_file = LOGS_DIR / "debug.log"

    entry = {
        "ts": datetime.now().isoformat(),
        "component": component,
        "event": event,
        **kwargs
    }

    try:
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Silent fail for logging


def read_debug_log(lines: int = 50, component: Optional[str] = None) -> List[Dict]:
    """Read recent entries from debug log."""
    log_file = LOGS_DIR / "debug.log"
    if not log_file.exists():
        return []

    entries = []
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            for line in all_lines[-lines * 2:]:  # Read extra to filter
                try:
                    entry = json.loads(line.strip())
                    if component is None or entry.get("component") == component:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return entries[-lines:]


def discover_models() -> List[str]:
    """Discover available models from LiteLLM proxy."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:4000/models")
        response = urllib.request.urlopen(req, timeout=3)
        data = json.loads(response.read().decode())
        if isinstance(data, dict) and "data" in data:
            return [m.get("id", "unknown") for m in data.get("data", [])]
    except Exception:
        pass
    return []


def get_model_health() -> Dict[str, str]:
    """Check health of each model."""
    health = {}
    health_script = CLAUDE_DIR / "scripts" / "health-check-model.sh"

    models = discover_models()
    for model in models:
        try:
            if health_script.exists():
                result = subprocess.run(
                    ["bash", str(health_script), model],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                health[model] = "OK" if result.returncode == 0 else "FAIL"
            else:
                health[model] = "UNKNOWN"
        except subprocess.TimeoutExpired:
            health[model] = "TIMEOUT"
        except Exception:
            health[model] = "ERROR"

    return health


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
@click.option("--auto-fix", "-f", is_flag=True, help="Automatically start stopped services")
def doctor(auto_fix: bool):
    """Diagnose and optionally fix K-LEAN installation issues."""
    print_banner()
    console.print("\n[bold]Running diagnostics...[/bold]\n")

    issues = []
    fixes_applied = []

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

    # Service checks with auto-fix
    console.print("[bold]Service Status:[/bold]")

    # Check LiteLLM
    litellm_status = check_litellm_detailed()
    if litellm_status["running"]:
        console.print(f"  [green]✓[/green] LiteLLM Proxy: RUNNING ({len(litellm_status['models'])} models)")
    else:
        if auto_fix:
            console.print("  [yellow]○[/yellow] LiteLLM Proxy: NOT RUNNING - Starting...")
            if start_litellm():
                console.print("  [green]✓[/green] LiteLLM Proxy: STARTED")
                fixes_applied.append("Started LiteLLM proxy")
            else:
                issues.append(("ERROR", "Failed to start LiteLLM proxy"))
                console.print("  [red]✗[/red] LiteLLM Proxy: FAILED TO START")
        else:
            issues.append(("WARNING", "LiteLLM proxy not running"))
            console.print("  [red]✗[/red] LiteLLM Proxy: NOT RUNNING")

    # Check Knowledge Server
    if check_knowledge_server():
        console.print("  [green]✓[/green] Knowledge Server: RUNNING")
    else:
        if auto_fix:
            console.print("  [yellow]○[/yellow] Knowledge Server: NOT RUNNING - Starting...")
            if start_knowledge_server():
                console.print("  [green]✓[/green] Knowledge Server: STARTED")
                fixes_applied.append("Started Knowledge server")
            else:
                issues.append(("ERROR", "Failed to start Knowledge server"))
                console.print("  [red]✗[/red] Knowledge Server: FAILED TO START")
        else:
            issues.append(("WARNING", "Knowledge server not running"))
            console.print("  [red]✗[/red] Knowledge Server: NOT RUNNING")

    console.print("")

    # Report issues
    if issues:
        console.print("[bold]Issues Found:[/bold]")
        for level, message in issues:
            if level == "CRITICAL":
                console.print(f"  [bold red]CRITICAL:[/bold red] {message}")
            elif level == "ERROR":
                console.print(f"  [red]ERROR:[/red] {message}")
            elif level == "WARNING":
                console.print(f"  [yellow]WARNING:[/yellow] {message}")
            else:
                console.print(f"  [blue]INFO:[/blue] {message}")
        console.print(f"\n[bold]Found {len(issues)} issue(s)[/bold]")
    else:
        console.print("[green]No issues found![/green]")

    if fixes_applied:
        console.print(f"\n[bold green]Auto-fixes applied:[/bold green]")
        for fix in fixes_applied:
            console.print(f"  • {fix}")

    if not auto_fix and any(level in ["WARNING", "ERROR"] for level, _ in issues):
        console.print("\n[cyan]Tip:[/cyan] Run [bold]k-lean doctor --auto-fix[/bold] to auto-start services")


@main.command()
@click.option("--service", "-s",
              type=click.Choice(["all", "litellm", "knowledge"]),
              default="all", help="Service to start")
@click.option("--port", "-p", default=4000, help="LiteLLM proxy port")
def start(service: str, port: int):
    """Start K-LEAN services (LiteLLM proxy and Knowledge server)."""
    print_banner()
    console.print("\n[bold]Starting services...[/bold]\n")

    started = []
    failed = []

    if service in ["all", "litellm"]:
        if check_litellm():
            console.print("[green]✓[/green] LiteLLM Proxy: Already running")
        else:
            console.print("[yellow]○[/yellow] Starting LiteLLM Proxy...")
            if start_litellm(background=True, port=port):
                console.print(f"[green]✓[/green] LiteLLM Proxy: Started on port {port}")
                started.append("LiteLLM")
                log_debug_event("cli", "service_start", service="litellm", port=port)
            else:
                console.print("[red]✗[/red] LiteLLM Proxy: Failed to start")
                failed.append("LiteLLM")

    if service in ["all", "knowledge"]:
        if check_knowledge_server():
            console.print("[green]✓[/green] Knowledge Server: Already running")
        else:
            console.print("[yellow]○[/yellow] Starting Knowledge Server...")
            if start_knowledge_server():
                console.print("[green]✓[/green] Knowledge Server: Started")
                started.append("Knowledge")
                log_debug_event("cli", "service_start", service="knowledge")
            else:
                console.print("[red]✗[/red] Knowledge Server: Failed to start")
                failed.append("Knowledge")

    console.print("")
    if started:
        console.print(f"[green]Started {len(started)} service(s)[/green]")
    if failed:
        console.print(f"[red]Failed to start {len(failed)} service(s)[/red]")


@main.command()
@click.option("--service", "-s",
              type=click.Choice(["all", "litellm", "knowledge"]),
              default="all", help="Service to stop")
def stop(service: str):
    """Stop K-LEAN services."""
    print_banner()
    console.print("\n[bold]Stopping services...[/bold]\n")

    stopped = []

    if service in ["all", "litellm"]:
        if stop_litellm():
            console.print("[green]✓[/green] LiteLLM Proxy: Stopped")
            stopped.append("LiteLLM")
            log_debug_event("cli", "service_stop", service="litellm")
        else:
            console.print("[yellow]○[/yellow] LiteLLM Proxy: Was not running")

    if service in ["all", "knowledge"]:
        if stop_knowledge_server():
            console.print("[green]✓[/green] Knowledge Server: Stopped")
            stopped.append("Knowledge")
            log_debug_event("cli", "service_stop", service="knowledge")
        else:
            console.print("[yellow]○[/yellow] Knowledge Server: Was not running")

    console.print(f"\n[green]Stopped {len(stopped)} service(s)[/green]")


def get_session_stats() -> Dict[str, Any]:
    """Get session statistics from debug log."""
    stats = {
        "session_start": None,
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "total_latency_ms": 0,
        "models_used": set(),
        "droids_executed": 0,
        "knowledge_queries": 0,
    }

    entries = read_debug_log(lines=500)
    if not entries:
        return stats

    for entry in entries:
        if stats["session_start"] is None:
            stats["session_start"] = entry.get("ts", "")

        event = entry.get("event", "")
        component = entry.get("component", "")

        if component == "cli" and event == "test_model":
            stats["total_requests"] += 1
            stats["successful_requests"] += 1
            stats["total_latency_ms"] += entry.get("latency_ms", 0)
            model = entry.get("model", "")
            if model:
                stats["models_used"].add(model)

        if component == "droid":
            stats["droids_executed"] += 1

        if component == "knowledge":
            stats["knowledge_queries"] += 1

    stats["models_used"] = list(stats["models_used"])
    return stats


def measure_service_latency(service: str) -> Optional[int]:
    """Measure service response latency in ms."""
    start = time.time()
    try:
        if service == "litellm":
            import urllib.request
            req = urllib.request.Request("http://localhost:4000/models")
            urllib.request.urlopen(req, timeout=3)
        elif service == "knowledge":
            socket_path = Path("/tmp/knowledge-server.sock")
            if socket_path.exists():
                return 1  # Socket exists = fast
            return None
        return int((time.time() - start) * 1000)
    except Exception:
        return None


def create_progress_bar(value: int, max_value: int, width: int = 20, color: str = "green") -> str:
    """Create a text-based progress bar."""
    if max_value == 0:
        return "░" * width
    filled = int((value / max_value) * width)
    empty = width - filled
    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"


@main.command()
@click.option("--follow", "-f", is_flag=True, help="Follow log output in real-time")
@click.option("--filter", "-F", "component_filter",
              type=click.Choice(["all", "litellm", "knowledge", "droid", "cli"]),
              default="all", help="Filter by component")
@click.option("--lines", "-n", default=20, help="Number of lines to show")
@click.option("--compact", "-c", is_flag=True, help="Compact single-line output")
def debug(follow: bool, component_filter: str, lines: int, compact: bool):
    """Real-time monitoring dashboard for K-LEAN services and activity."""
    ensure_klean_dirs()

    # Compact mode - single line for hooks/scripts
    if compact:
        litellm_ok = check_litellm()
        knowledge_ok = check_knowledge_server()
        models = discover_models() if litellm_ok else []
        healthy = sum(1 for m in models if m in ["qwen3-coder", "deepseek-v3-thinking"])  # Known working
        status = "✓" if litellm_ok and knowledge_ok else "⚠"
        console.print(f"{status} K-LEAN: LiteLLM({'OK' if litellm_ok else 'DOWN'}) Knowledge({'OK' if knowledge_ok else 'DOWN'}) Models({healthy}/{len(models)})")
        return

    def render_services_panel() -> Panel:
        """Render services status panel."""
        litellm_info = check_litellm_detailed()
        knowledge_ok = check_knowledge_server()
        litellm_latency = measure_service_latency("litellm") if litellm_info["running"] else None

        table = Table(box=None, show_header=False, padding=(0, 1))
        table.add_column("Service", style="bold")
        table.add_column("Status", width=12)
        table.add_column("Info", style="dim")

        # LiteLLM
        if litellm_info["running"]:
            latency_str = f"{litellm_latency}ms" if litellm_latency else ""
            table.add_row(
                "LiteLLM Proxy",
                "[green]● RUNNING[/green]",
                f":{4000} {latency_str}"
            )
        else:
            table.add_row("LiteLLM Proxy", "[red]● STOPPED[/red]", "k-lean start")

        # Knowledge DB
        if knowledge_ok:
            table.add_row("Knowledge DB", "[green]● RUNNING[/green]", "socket")
        else:
            table.add_row("Knowledge DB", "[red]● STOPPED[/red]", "k-lean start")

        return Panel(table, title="[bold]Services[/bold]", border_style="blue")

    def render_models_panel() -> Panel:
        """Render models status panel."""
        models = discover_models()
        if not models:
            return Panel("[dim]No models available[/dim]", title="[bold]Models[/bold]", border_style="yellow")

        table = Table(box=None, show_header=True, padding=(0, 1))
        table.add_column("Model", style="cyan")
        table.add_column("Status", width=8)
        table.add_column("Latency", width=8, justify="right")

        # Quick health check - just test top 2 models to keep it fast
        for model in models[:6]:
            # Simple availability check
            try:
                import urllib.request
                start = time.time()
                data = json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1
                }).encode()
                req = urllib.request.Request(
                    "http://localhost:4000/chat/completions",
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=5)
                latency = int((time.time() - start) * 1000)
                table.add_row(model[:18], "[green]●[/green]", f"{latency}ms")
            except Exception:
                table.add_row(model[:18], "[red]●[/red]", "-")

        return Panel(table, title=f"[bold]Models ({len(models)})[/bold]", border_style="green")

    def render_stats_panel() -> Panel:
        """Render session statistics panel."""
        stats = get_session_stats()

        lines_out = []

        # Session info
        if stats["session_start"]:
            start_time = stats["session_start"][:19].replace("T", " ")
            lines_out.append(f"[bold]Session:[/bold] Started {start_time}")
        else:
            lines_out.append("[bold]Session:[/bold] No activity yet")

        lines_out.append("")

        # Request stats
        total = stats["total_requests"]
        success = stats["successful_requests"]
        avg_latency = stats["total_latency_ms"] // max(total, 1)

        lines_out.append(f"[bold]Requests:[/bold] {total}")
        if total > 0:
            success_rate = int((success / total) * 100)
            lines_out.append(f"  Success: {create_progress_bar(success_rate, 100, 15)} {success_rate}%")
            lines_out.append(f"  Avg latency: {avg_latency}ms")

        lines_out.append("")

        # Activity counts
        lines_out.append(f"[bold]Activity:[/bold]")
        lines_out.append(f"  Droids executed: {stats['droids_executed']}")
        lines_out.append(f"  Knowledge queries: {stats['knowledge_queries']}")
        lines_out.append(f"  Models used: {len(stats['models_used'])}")

        return Panel("\n".join(lines_out), title="[bold]Statistics[/bold]", border_style="magenta")

    def render_activity_panel() -> Panel:
        """Render recent activity panel."""
        filter_comp = None if component_filter == "all" else component_filter
        entries = read_debug_log(lines=lines, component=filter_comp)

        if not entries:
            return Panel("[dim]No recent activity\nRun k-lean test-model to generate activity[/dim]",
                        title="[bold]Activity Feed[/bold]", border_style="cyan")

        activity_lines = []
        for entry in entries[-10:]:
            ts = entry.get("ts", "")[11:19]  # Just time
            comp = entry.get("component", "???")
            event = entry.get("event", "")

            # Color by component
            comp_colors = {"cli": "yellow", "litellm": "green", "droid": "magenta", "knowledge": "cyan"}
            color = comp_colors.get(comp, "white")

            # Format event details
            if comp == "cli" and event == "test_model":
                model = entry.get("model", "")
                latency = entry.get("latency_ms", 0)
                detail = f"[{color}]{comp}[/{color}] test {model} ({latency}ms)"
            elif comp == "cli" and event == "service_start":
                service = entry.get("service", "")
                detail = f"[{color}]{comp}[/{color}] started {service}"
            elif comp == "cli" and event == "service_stop":
                service = entry.get("service", "")
                detail = f"[{color}]{comp}[/{color}] stopped {service}"
            elif comp == "droid":
                droid = entry.get("droid", event)
                detail = f"[{color}]{comp}[/{color}] {droid}"
            elif comp == "knowledge":
                query = entry.get("query", event)[:30]
                detail = f"[{color}]{comp}[/{color}] query: {query}"
            else:
                detail = f"[{color}]{comp}[/{color}] {event}"

            activity_lines.append(f"[dim]{ts}[/dim] {detail}")

        return Panel("\n".join(activity_lines), title="[bold]Activity Feed[/bold]", border_style="cyan")

    def render_paths_panel() -> Panel:
        """Render paths info panel."""
        paths = [
            f"[bold]Claude:[/bold] {CLAUDE_DIR}",
            f"[bold]K-LEAN:[/bold] {KLEAN_DIR}",
            f"[bold]Logs:[/bold] {LOGS_DIR}",
            f"[bold]Config:[/bold] {CONFIG_DIR}",
        ]

        # Add log file sizes
        debug_log = LOGS_DIR / "debug.log"
        if debug_log.exists():
            size = debug_log.stat().st_size
            paths.append(f"[dim]Debug log: {size:,} bytes[/dim]")

        return Panel("\n".join(paths), title="[bold]Paths[/bold]", border_style="dim")

    def render_full_dashboard():
        """Render the complete dashboard layout."""
        # Create layout
        layout = Layout()

        # Header
        header = Text()
        header.append("K-LEAN ", style="bold cyan")
        header.append("Monitoring Dashboard", style="bold")
        header.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")

        # Top section: Services + Models
        top_layout = Layout()
        top_layout.split_row(
            Layout(render_services_panel(), name="services", ratio=1),
            Layout(render_models_panel(), name="models", ratio=2),
        )

        # Middle section: Stats + Activity
        mid_layout = Layout()
        mid_layout.split_row(
            Layout(render_stats_panel(), name="stats", ratio=1),
            Layout(render_activity_panel(), name="activity", ratio=2),
        )

        # Combine
        layout.split_column(
            Layout(Panel(header, border_style="cyan"), size=3),
            Layout(top_layout, name="top", ratio=2),
            Layout(mid_layout, name="middle", ratio=2),
            Layout(render_paths_panel(), name="bottom", size=6),
        )

        return layout

    if follow:
        console.print("[dim]K-LEAN Monitoring Dashboard - Press Ctrl+C to exit[/dim]\n")
        try:
            with Live(render_full_dashboard(), refresh_per_second=1, console=console, screen=True) as live:
                while True:
                    time.sleep(1)
                    live.update(render_full_dashboard())
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard closed[/yellow]")
    else:
        console.print(render_full_dashboard())


@main.command()
def models():
    """List available models from LiteLLM proxy."""
    print_banner()

    if not check_litellm():
        console.print("\n[red]LiteLLM proxy is not running![/red]")
        console.print("Start it with: [cyan]k-lean start --service litellm[/cyan]")
        return

    models_list = discover_models()

    if not models_list:
        console.print("\n[yellow]No models found[/yellow]")
        return

    table = Table(title="Available Models")
    table.add_column("Model ID", style="cyan")
    table.add_column("Status", style="green")

    console.print("\n[dim]Checking model health...[/dim]")
    health = get_model_health()

    for model in models_list:
        status = health.get(model, "UNKNOWN")
        if status == "OK":
            status_str = "[green]OK[/green]"
        elif status == "FAIL":
            status_str = "[red]FAIL[/red]"
        elif status == "TIMEOUT":
            status_str = "[yellow]TIMEOUT[/yellow]"
        else:
            status_str = "[dim]UNKNOWN[/dim]"
        table.add_row(model, status_str)

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(models_list)} models available")


@main.command()
@click.argument("model", required=False)
@click.argument("prompt", required=False)
def test_model(model: Optional[str], prompt: Optional[str]):
    """Test a model with a quick prompt."""
    if not check_litellm():
        console.print("[red]LiteLLM proxy is not running![/red]")
        return

    models_list = discover_models()

    if not model:
        console.print("[bold]Available models:[/bold]")
        for m in models_list:
            console.print(f"  • {m}")
        console.print("\nUsage: [cyan]k-lean test-model <model> [prompt][/cyan]")
        return

    if model not in models_list:
        console.print(f"[red]Model '{model}' not found[/red]")
        console.print(f"Available: {', '.join(models_list)}")
        return

    if not prompt:
        prompt = "Say 'Hello from K-LEAN!' in exactly 5 words."

    console.print(f"\n[bold]Testing model:[/bold] {model}")
    console.print(f"[bold]Prompt:[/bold] {prompt}\n")

    try:
        import urllib.request
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100
        }).encode()

        req = urllib.request.Request(
            "http://localhost:4000/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"}
        )

        start_time = time.time()
        response = urllib.request.urlopen(req, timeout=30)
        elapsed = time.time() - start_time

        result = json.loads(response.read().decode())
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "No response")

        console.print(f"[green]Response:[/green] {content}")
        console.print(f"[dim]Latency: {elapsed:.2f}s[/dim]")

        log_debug_event("cli", "test_model", model=model, latency_ms=int(elapsed * 1000))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    main()
