#!/usr/bin/env bash
# K-LEAN Installer
# Multi-model code review and knowledge capture system for Claude Code

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

VERSION=$(get_version)
CLAUDE_DIR="${HOME}/.claude"
VENV_DIR="${HOME}/.venvs/knowledge-db"

# Print banner
print_banner() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║           K-LEAN Companion v$VERSION                        ║"
    echo "║   Multi-Model Code Review & Knowledge Capture System      ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
}

# Usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --full        Full installation (scripts, commands, hooks, knowledge-db)"
    echo "  --minimal     Minimal installation (scripts only)"
    echo "  --scripts     Install/update scripts only"
    echo "  --commands    Install/update slash commands only"
    echo "  --hooks       Install/update hooks only"
    echo "  --knowledge   Install/update knowledge system only"
    echo "  --check       Verify installation without changes"
    echo "  --uninstall   Remove K-LEAN (keeps backups)"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --full       # Fresh install everything"
    echo "  $0 --scripts    # Update scripts only"
    echo "  $0 --check      # Verify current installation"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    local platform=$(detect_platform)
    log_info "Platform: $platform"

    if ! check_dependencies; then
        log_error "Please install missing dependencies and try again"
        exit 1
    fi

    log_success "All prerequisites met"
}

# Install scripts
install_scripts() {
    log_info "Installing scripts..."

    ensure_dir "$CLAUDE_DIR/scripts"
    backup_existing "$CLAUDE_DIR/scripts" "$CLAUDE_DIR/backups"

    copy_files "$SCRIPT_DIR/scripts" "$CLAUDE_DIR/scripts"
    make_executable "$CLAUDE_DIR/scripts"

    local count=$(ls -1 "$CLAUDE_DIR/scripts"/*.sh 2>/dev/null | wc -l)
    log_success "Installed $count scripts"
}

# Install commands
install_commands() {
    log_info "Installing slash commands..."

    ensure_dir "$CLAUDE_DIR/commands/kln"
    ensure_dir "$CLAUDE_DIR/commands/sc"

    # Install KLN commands
    if [ -d "$SCRIPT_DIR/commands/kln" ]; then
        copy_files "$SCRIPT_DIR/commands/kln" "$CLAUDE_DIR/commands/kln" "*.md"
        local kln_count=$(ls -1 "$CLAUDE_DIR/commands/kln"/*.md 2>/dev/null | wc -l)
        log_success "Installed $kln_count KLN commands"
    fi

    # Install SC commands
    if [ -d "$SCRIPT_DIR/commands/sc" ]; then
        copy_files "$SCRIPT_DIR/commands/sc" "$CLAUDE_DIR/commands/sc" "*.md"
        local sc_count=$(ls -1 "$CLAUDE_DIR/commands/sc"/*.md 2>/dev/null | wc -l)
        log_success "Installed $sc_count SC commands"
    fi
}

# Install hooks
install_hooks() {
    log_info "Installing hooks..."

    ensure_dir "$CLAUDE_DIR/hooks"

    if [ -d "$SCRIPT_DIR/hooks" ]; then
        copy_files "$SCRIPT_DIR/hooks" "$CLAUDE_DIR/hooks" "*.sh"
        make_executable "$CLAUDE_DIR/hooks"
        local count=$(ls -1 "$CLAUDE_DIR/hooks"/*.sh 2>/dev/null | wc -l)
        log_success "Installed $count hooks"
    else
        log_warn "No hooks found in source"
    fi
}

# Install configuration
install_config() {
    log_info "Installing configuration..."

    # CLAUDE.md
    if [ -f "$SCRIPT_DIR/config/CLAUDE.md" ]; then
        if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
            backup_existing "$CLAUDE_DIR" "$CLAUDE_DIR/backups"
        fi
        cp "$SCRIPT_DIR/config/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
        log_success "Installed CLAUDE.md"
    fi

    # settings.json (only if not exists)
    if [ ! -f "$CLAUDE_DIR/settings.json" ]; then
        if [ -f "$SCRIPT_DIR/config/settings.json" ]; then
            cp "$SCRIPT_DIR/config/settings.json" "$CLAUDE_DIR/settings.json"
            log_success "Installed settings.json"
        fi
    else
        log_info "Keeping existing settings.json"
    fi
}

# Install knowledge database system
install_knowledge() {
    log_info "Installing knowledge database system..."

    # Create virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creating Python virtual environment..."
        create_venv "$VENV_DIR"
    fi

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    "$VENV_DIR/bin/pip" install -q --upgrade pip 2>/dev/null
    "$VENV_DIR/bin/pip" install -q txtai sentence-transformers 2>/dev/null || {
        log_warn "Failed to install txtai - knowledge search may not work"
    }

    log_success "Knowledge database system ready"
}

# Install LiteLLM configuration
install_litellm_config() {
    local config_dir="${HOME}/.config/litellm"
    ensure_dir "$config_dir"

    if [ -f "$SCRIPT_DIR/config/nanogpt.yaml" ]; then
        if [ ! -f "$config_dir/nanogpt.yaml" ]; then
            cp "$SCRIPT_DIR/config/nanogpt.yaml" "$config_dir/nanogpt.yaml"
            log_success "Installed LiteLLM configuration"
        else
            log_info "LiteLLM config already exists - keeping current"
        fi
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."

    local errors=0

    # Check scripts
    echo -n "  Scripts: "
    if [ -d "$CLAUDE_DIR/scripts" ] && [ -x "$CLAUDE_DIR/scripts/quick-review.sh" ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}MISSING${NC}"
        ((errors++))
    fi

    # Check commands
    echo -n "  Commands: "
    if [ -d "$CLAUDE_DIR/commands/kln" ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}PARTIAL${NC}"
    fi

    # Check hooks
    echo -n "  Hooks: "
    if [ -d "$CLAUDE_DIR/hooks" ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}NOT INSTALLED${NC}"
    fi

    # Check CLAUDE.md
    echo -n "  CLAUDE.md: "
    if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}MISSING${NC}"
        ((errors++))
    fi

    # Check Python venv
    echo -n "  Knowledge DB: "
    if [ -d "$VENV_DIR" ] && "$VENV_DIR/bin/python" -c "import txtai" 2>/dev/null; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}NOT INSTALLED${NC}"
    fi

    # Check LiteLLM
    echo -n "  LiteLLM: "
    if check_litellm; then
        echo -e "${GREEN}RUNNING${NC}"
    else
        echo -e "${YELLOW}NOT RUNNING${NC}"
    fi

    if [ $errors -eq 0 ]; then
        log_success "Installation verified successfully"
        return 0
    else
        log_error "Installation has $errors errors"
        return 1
    fi
}

# Full installation
install_full() {
    check_prerequisites

    install_scripts
    install_commands
    install_hooks
    install_config
    install_knowledge
    install_litellm_config

    echo ""
    verify_installation

    echo ""
    log_success "K-LEAN v$VERSION installed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Start LiteLLM: ~/.claude/scripts/start-litellm.sh"
    echo "  2. Test models: healthcheck"
    echo "  3. Try a review: /kln:quickReview qwen"
}

# Minimal installation
install_minimal() {
    check_prerequisites

    install_scripts
    install_config

    echo ""
    verify_installation
}

# Uninstall
uninstall() {
    log_warn "This will remove K-LEAN components"
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cancelled"
        exit 0
    fi

    # Backup before removal
    backup_existing "$CLAUDE_DIR/scripts" "$CLAUDE_DIR/backups"
    backup_existing "$CLAUDE_DIR/commands" "$CLAUDE_DIR/backups"

    # Remove directories
    rm -rf "$CLAUDE_DIR/scripts" 2>/dev/null || true
    rm -rf "$CLAUDE_DIR/commands/kln" 2>/dev/null || true
    rm -rf "$CLAUDE_DIR/hooks" 2>/dev/null || true

    log_success "K-LEAN removed (backups preserved in $CLAUDE_DIR/backups)"
}

# Main
main() {
    print_banner

    case "${1:-}" in
        --full)
            install_full
            ;;
        --minimal)
            install_minimal
            ;;
        --scripts)
            check_prerequisites
            install_scripts
            ;;
        --commands)
            install_commands
            ;;
        --hooks)
            install_hooks
            ;;
        --knowledge)
            install_knowledge
            ;;
        --check)
            verify_installation
            ;;
        --uninstall)
            uninstall
            ;;
        -h|--help)
            usage
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"
