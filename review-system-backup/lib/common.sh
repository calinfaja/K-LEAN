#!/usr/bin/env bash
# K-LEAN Common Library
# Shared functions for installer, updater, and utilities

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Version
get_version() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cat "$script_dir/VERSION" 2>/dev/null || echo "unknown"
}

# Platform detection
detect_platform() {
    case "$(uname -s)" in
        Linux*)  echo "linux" ;;
        Darwin*) echo "macos" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *)       echo "unknown" ;;
    esac
}

# Package manager detection
detect_package_manager() {
    if command -v apt-get &>/dev/null; then echo "apt"
    elif command -v dnf &>/dev/null; then echo "dnf"
    elif command -v yum &>/dev/null; then echo "yum"
    elif command -v pacman &>/dev/null; then echo "pacman"
    elif command -v brew &>/dev/null; then echo "brew"
    else echo "unknown"
    fi
}

# Check if command exists
check_command() {
    command -v "$1" &>/dev/null
}

# Check Python version
check_python() {
    if check_command python3; then
        python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null
        return $?
    fi
    return 1
}

# Check dependencies
check_dependencies() {
    local missing=()

    # Required commands
    check_command git || missing+=("git")
    check_command curl || missing+=("curl")
    check_python || missing+=("python3.9+")

    # Optional but recommended
    if ! check_command socat && ! check_command nc; then
        log_warn "Neither socat nor nc found - knowledge-query.sh will be slower"
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        return 1
    fi
    return 0
}

# Backup existing installation
backup_existing() {
    local target="$1"
    local backup_dir="$2"

    if [ -d "$target" ]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_path="$backup_dir/backup_$timestamp"
        mkdir -p "$backup_path"
        cp -r "$target"/* "$backup_path/" 2>/dev/null || true
        log_info "Existing files backed up to: $backup_path"
    fi
}

# Create directory safely
ensure_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    fi
}

# Copy files with permission preservation
copy_files() {
    local src="$1"
    local dest="$2"
    local pattern="${3:-*}"

    if [ -d "$src" ]; then
        cp -rp "$src"/$pattern "$dest/" 2>/dev/null || true
    fi
}

# Make scripts executable
make_executable() {
    local dir="$1"
    find "$dir" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
    find "$dir" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
}

# Install Python package
install_python_package() {
    local package="$1"
    local venv="${2:-}"

    if [ -n "$venv" ]; then
        "$venv/bin/pip" install -q "$package" 2>/dev/null
    else
        pip3 install -q --user "$package" 2>/dev/null
    fi
}

# Create Python virtual environment
create_venv() {
    local venv_path="$1"

    if [ ! -d "$venv_path" ]; then
        python3 -m venv "$venv_path"
        log_info "Created virtual environment: $venv_path"
    fi
}

# Check if LiteLLM is running
check_litellm() {
    curl -s --max-time 2 http://localhost:4000/v1/models &>/dev/null
    return $?
}

# Start LiteLLM if not running
ensure_litellm() {
    if ! check_litellm; then
        log_warn "LiteLLM not running on port 4000"
        return 1
    fi
    return 0
}

# Load configuration from YAML (simple parser)
load_config() {
    local config_file="$1"
    local key="$2"

    if [ -f "$config_file" ]; then
        grep "^$key:" "$config_file" | cut -d: -f2- | xargs
    fi
}

# Validate installation
validate_installation() {
    local claude_dir="$HOME/.claude"
    local errors=0

    # Check scripts directory
    if [ ! -d "$claude_dir/scripts" ]; then
        log_error "Scripts directory missing"
        ((errors++))
    fi

    # Check key scripts
    for script in quick-review.sh knowledge-init.sh async-dispatch.sh; do
        if [ ! -x "$claude_dir/scripts/$script" ]; then
            log_error "Missing or not executable: $script"
            ((errors++))
        fi
    done

    # Check CLAUDE.md
    if [ ! -f "$claude_dir/CLAUDE.md" ]; then
        log_error "CLAUDE.md missing"
        ((errors++))
    fi

    return $errors
}
