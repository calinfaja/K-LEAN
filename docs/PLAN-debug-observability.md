# Implementation Plan: K-LEAN Debug Observability

**Status: [OK] IMPLEMENTED** (2024-12-22, docs updated 2024-12-23)

## Overview

Enhance `kln debug` with:
1. **LiteLLM Routing Health** - Via `/health` endpoint (on-demand via `kln models --health`)
2. **SmolKLN Agent Telemetry** - Trace agent execution with Phoenix [OK]

> **Note:** LiteLLM Admin UI was evaluated but requires prisma/database setup.
> The `/health` endpoint takes 60s (makes real API calls) so it's not suitable for
> the live dashboard. Use `kln models --health` for deep diagnostics instead.

---

## Part 1: LiteLLM UI Integration

### Current State
- LiteLLM runs on `localhost:4000`
- Has built-in Admin UI at `/ui` (requires master_key + database)
- `kln debug` shows services but no link to UI

### Implementation Steps

#### Step 1.1: Enable LiteLLM Database (for UI)

**[WARN] Note:** The Admin UI requires additional dependencies. Install with:
```bash
pipx inject litellm prisma
cd ~/.local/share/pipx/venvs/litellm && bin/prisma generate
```

**File:** `~/.config/litellm/config.yaml`

```yaml
general_settings:
  master_key: "sk-klean-master"
  database_url: "sqlite:///~/.config/litellm/litellm.db"
```

**File:** `src/klean/data/config/litellm/config.yaml` (template)

Add to the template so new installs get it (commented out by default).

#### Step 1.2: Add UI Link to `kln debug`
**File:** `src/klean/cli.py` - `render_services_panel()`

```python
def render_services_panel() -> Panel:
    # ... existing code ...

    # LiteLLM
    if litellm_info["running"]:
        latency_str = f" {litellm_latency}ms" if litellm_latency else ""
        lines.append(f"[bold]LiteLLM[/bold]  [green]● ON[/green]{latency_str}")
        lines.append(f"  [dim]UI: http://localhost:4000/ui[/dim]")  # ADD THIS
```

#### Step 1.3: Add `--ui` flag to open browser
**File:** `src/klean/cli.py`

```python
@main.command()
@click.option("--ui", is_flag=True, help="Open LiteLLM Admin UI in browser")
def debug(follow, component_filter, lines, compact, interval, ui):
    if ui:
        import webbrowser
        webbrowser.open("http://localhost:4000/ui")
        return
    # ... rest of debug ...
```

#### Step 1.4: Show Recent Requests in Debug
Add a panel showing last 5 requests from LiteLLM spend logs:

```python
def render_requests_panel() -> Panel:
    """Show recent LiteLLM requests."""
    try:
        response = urllib.request.urlopen(
            "http://localhost:4000/spend/logs?limit=5",
            timeout=2
        )
        logs = json.loads(response.read().decode())
        # Format and display
    except:
        return Panel("[dim]No request logs available[/dim]", title="Recent Requests")
```

---

## Part 2: SmolKLN Agent Telemetry

### The Simplest Approach: Phoenix (Local)

Phoenix runs locally, no cloud account needed, provides a web UI to inspect agent runs.

### Implementation Steps

#### Step 2.1: Add Telemetry Dependencies
**File:** `pyproject.toml`

```toml
[project.optional-dependencies]
telemetry = [
    "arize-phoenix>=4.0",
    "opentelemetry-sdk",
    "opentelemetry-exporter-otlp",
    "openinference-instrumentation-smolagents",
]
```

Install: `pipx inject k-lean 'k-lean[telemetry]'`

#### Step 2.2: Add `--telemetry` Flag to smol-kln.py
**File:** `src/klean/data/scripts/smol-kln.py`

```python
parser.add_argument("--telemetry", "-t", action="store_true",
                    help="Enable Phoenix telemetry (view at localhost:6006)")

# In main(), before running agent:
if args.telemetry:
    try:
        from phoenix.otel import register
        from openinference.instrumentation.smolagents import SmolagentsInstrumentor

        register(project_name="smolkln")
        SmolagentsInstrumentor().instrument()
        print(" Telemetry enabled - view at http://localhost:6006")
    except ImportError:
        print("[WARN]  Telemetry not installed. Run: pipx inject k-lean 'k-lean[telemetry]'")
```

#### Step 2.3: Add Phoenix Server Management
**File:** `src/klean/cli.py`

```python
def start_phoenix() -> bool:
    """Start Phoenix telemetry server on port 6006."""
    # Check if already running
    try:
        urllib.request.urlopen("http://localhost:6006", timeout=1)
        return True  # Already running
    except:
        pass

    # Start Phoenix
    subprocess.Popen(
        [sys.executable, "-m", "phoenix.server.main", "serve"],
        stdout=open(LOGS_DIR / "phoenix.log", "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    return True

def check_phoenix() -> bool:
    """Check if Phoenix is running."""
    try:
        urllib.request.urlopen("http://localhost:6006", timeout=1)
        return True
    except:
        return False
```

#### Step 2.4: Add Phoenix to Debug Dashboard
**File:** `src/klean/cli.py` - `render_services_panel()`

```python
# Phoenix Telemetry
if check_phoenix():
    lines.append("[bold]Phoenix[/bold]   [green]● ON[/green]")
    lines.append(f"  [dim]UI: http://localhost:6006[/dim]")
else:
    lines.append("[bold]Phoenix[/bold]   [dim]○ OFF[/dim]")
```

#### Step 2.5: Add `kln start --telemetry`
**File:** `src/klean/cli.py`

```python
@click.option("--telemetry", is_flag=True, help="Also start Phoenix telemetry server")
def start(service, telemetry):
    # ... existing service start ...

    if telemetry:
        console.print("[bold]Starting Phoenix telemetry...[/bold]")
        if start_phoenix():
            console.print("  [green][OK][/green] Phoenix: http://localhost:6006")
```

---

## Part 3: Quick Reference After Implementation

### User Workflow

```bash
# Start everything with telemetry
kln start --telemetry

# Run an agent with tracing
smol-kln.py security-auditor "audit auth" --telemetry

# View the dashboards
kln debug --ui        # Opens LiteLLM UI
# Or manually:
# http://localhost:4000/ui   - LiteLLM (spend, requests)
# http://localhost:6006      - Phoenix (agent traces)
```

### What You'll See

**LiteLLM UI (`localhost:4000/ui`):**
- Total spend per model
- Request/response logs
- Token usage over time
- Error rates

**Phoenix UI (`localhost:6006`):**
- Agent execution tree
- Each LLM call with prompt/response
- Tool invocations
- Timing breakdown
- Multi-agent coordination

---

## Implementation Order

| Phase | Task | Status | Files |
|-------|------|--------|-------|
| 1.1 | Add database_url to config template | [OK] | config/litellm/config.yaml |
| 1.2 | Add UI link to debug output | [OK] | cli.py |
| 1.3 | Add `--ui` flag | [OK] | cli.py |
| 2.1 | Add telemetry deps to pyproject | [OK] | pyproject.toml |
| 2.2 | Add `--telemetry` to smol-kln.py | [OK] | smol-kln.py |
| 2.3 | Add Phoenix start/check functions | [OK] | cli.py |
| 2.4 | Add Phoenix to debug dashboard | [OK] | cli.py |
| 2.5 | Add `--telemetry` to kln start | [OK] | cli.py |

**All phases completed.**

---

## Testing Strategy

1. **LiteLLM UI:**
   - Start LiteLLM with database
   - Make a request via `kln models --health`
   - Verify spend shows in UI

2. **Phoenix Telemetry:**
   - Start Phoenix: `python -m phoenix.server.main serve`
   - Run agent: `smol-kln.py code-reviewer "test" --telemetry`
   - Verify trace appears at `localhost:6006`

3. **Integration:**
   - Run `kln debug` and verify both UIs are shown
   - Run `kln debug --ui` opens browser
