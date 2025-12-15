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
    echo "  --droids      Install/update Factory Droid specialists only"
    echo "  --statusline  Install/update K-LEAN statusline only"
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
    "$VENV_DIR/bin/pip" install -q txtai sentence-transformers python-toon 2>/dev/null || {
        log_warn "Failed to install dependencies - knowledge search may not work"
    }

    log_success "Knowledge database system ready"
}

# Setup knowledge server auto-start
install_knowledge_server_autostart() {
    log_info "Setting up knowledge server auto-start..."

    local bashrc="${HOME}/.bashrc"
    local marker="# K-LEAN Knowledge Server Auto-Start"

    # Check if already installed
    if grep -q "$marker" "$bashrc" 2>/dev/null; then
        log_info "Knowledge server auto-start already configured"
        return 0
    fi

    # Add auto-start to bashrc
    cat >> "$bashrc" << 'EOF'

# K-LEAN Knowledge Server Auto-Start
# Keeps txtai embeddings in memory for fast searches (~30ms vs ~17s)
if [ ! -S /tmp/knowledge-server.sock ]; then
    if [ -f ~/.claude/scripts/knowledge-server.py ]; then
        (cd ~ && nohup ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-server.py start > /tmp/knowledge-server.log 2>&1 &)
    fi
fi
EOF

    log_success "Knowledge server auto-start added to ~/.bashrc"
    log_info "Server will start on next terminal open"
}

# Install LiteLLM configuration (modular approach with .env)
install_litellm_config() {
    local config_dir="${HOME}/.config/litellm"
    ensure_dir "$config_dir"

    log_info "Setting up LiteLLM configuration..."

    # Install provider templates
    if [ -f "$SCRIPT_DIR/config/litellm/config.yaml" ]; then
        cp "$SCRIPT_DIR/config/litellm/config.yaml" "$config_dir/config.yaml"
        log_success "Installed NanoGPT config template"
    fi

    if [ -f "$SCRIPT_DIR/config/litellm/openrouter.yaml" ]; then
        cp "$SCRIPT_DIR/config/litellm/openrouter.yaml" "$config_dir/openrouter.yaml"
        log_success "Installed OpenRouter config template"
    fi

    if [ -f "$SCRIPT_DIR/config/litellm/ollama.yaml" ]; then
        cp "$SCRIPT_DIR/config/litellm/ollama.yaml" "$config_dir/ollama.yaml"
        log_success "Installed Ollama config template"
    fi

    # Install .env.example template
    if [ -f "$SCRIPT_DIR/config/litellm/.env.example" ]; then
        cp "$SCRIPT_DIR/config/litellm/.env.example" "$config_dir/.env.example"
        log_success "Installed .env.example template"
    fi

    # Create .env from template if it doesn't exist
    if [ ! -f "$config_dir/.env" ]; then
        if [ -f "$config_dir/.env.example" ]; then
            cp "$config_dir/.env.example" "$config_dir/.env"
            log_warn "Created .env from template - edit with your API keys!"
            log_info "  Edit: $config_dir/.env"
        fi
    else
        log_info "Keeping existing .env file"
    fi

    # Legacy: migrate from old nanogpt.yaml if present
    if [ -f "$config_dir/nanogpt.yaml" ] && [ ! -f "$config_dir/config.yaml.bak" ]; then
        mv "$config_dir/nanogpt.yaml" "$config_dir/nanogpt.yaml.bak"
        log_info "Backed up old nanogpt.yaml → nanogpt.yaml.bak"
    fi

    log_success "LiteLLM config ready"
    log_info "Start proxy: ~/.claude/scripts/litellm-start.sh"
}

# Interactive LiteLLM setup wizard
setup_litellm_interactive() {
    log_info "Running LiteLLM setup wizard..."

    if [ -x "$CLAUDE_DIR/scripts/setup-litellm.sh" ]; then
        "$CLAUDE_DIR/scripts/setup-litellm.sh"
    else
        log_warn "setup-litellm.sh not found or not executable"
    fi
}

# Install Factory Droid specialists
install_droids() {
    local FACTORY_DIR="${HOME}/.factory/droids"
    local DROID_SOURCE="$SCRIPT_DIR/droids"

    log_info "Installing Factory Droid specialists..."

    # Create Factory droids directory
    ensure_dir "$FACTORY_DIR"

    # List of 8 specialist droids (embedded/Linux focus)
    local DROIDS=(
        "orchestrator.md"
        "code-reviewer.md"
        "security-auditor.md"
        "debugger.md"
        "arm-cortex-expert.md"
        "c-pro.md"
        "rust-expert.md"
        "performance-engineer.md"
    )

    local installed=0

    if [ -d "$DROID_SOURCE" ]; then
        for droid in "${DROIDS[@]}"; do
            if [ -f "$DROID_SOURCE/$droid" ]; then
                cp "$DROID_SOURCE/$droid" "$FACTORY_DIR/$droid"
                ((installed++))
            fi
        done
    else
        log_warn "Droid source directory not found: $DROID_SOURCE"
        log_info "Droids can be installed manually from: https://github.com/aeitroc/Droid-CLI-Orchestrator"
    fi

    if [ $installed -gt 0 ]; then
        log_success "Installed $installed Factory Droid specialists"
        log_info "Available droids:"
        log_info "  orchestrator     - Master coordinator for complex tasks"
        log_info "  code-reviewer    - Quality gatekeeper"
        log_info "  security-auditor - OWASP compliance"
        log_info "  debugger         - Root cause analysis"
        log_info "  arm-cortex-expert - Embedded/microcontroller specialist"
        log_info "  c-pro            - C systems programming"
        log_info "  rust-expert      - Safe systems programming"
        log_info "  performance-engineer - Optimization specialist"
    else
        log_warn "No droids installed - Factory Droid may not be fully functional"
    fi
}

# Install K-LEAN statusline
install_statusline() {
    log_info "Installing K-LEAN statusline..."

    # Copy statusline script
    if [ -f "$SCRIPT_DIR/scripts/klean-statusline.py" ]; then
        cp "$SCRIPT_DIR/scripts/klean-statusline.py" "$CLAUDE_DIR/scripts/"
        chmod +x "$CLAUDE_DIR/scripts/klean-statusline.py"
        log_success "Installed klean-statusline.py"
    else
        log_warn "klean-statusline.py not found in source"
        return 1
    fi

    # Configure settings.json with statusline
    if [ -f "$CLAUDE_DIR/settings.json" ]; then
        # Check if statusLine already configured
        if ! grep -q '"statusLine"' "$CLAUDE_DIR/settings.json" 2>/dev/null; then
            # Add statusLine config before the closing brace
            sed -i 's/}$/,\n  "statusLine": {\n    "type": "command",\n    "command": "~\/.claude\/scripts\/klean-statusline.py",\n    "padding": 0\n  }\n}/' "$CLAUDE_DIR/settings.json"
            log_success "Configured statusline in settings.json"
        else
            log_info "Statusline already configured in settings.json"
        fi
    else
        log_warn "settings.json not found - statusline not configured"
    fi
}

# Install nano profile (for claude-nano command)
install_nano_profile() {
    local NANO_DIR="${HOME}/.claude-nano"

    log_info "Setting up nano profile..."

    # Create nano profile directory
    ensure_dir "$NANO_DIR"

    # Create settings.json with nano configuration
    cat > "$NANO_DIR/settings.json" << 'EOF'
{
  "defaultModel": "qwen3-coder",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "qwen3-coder",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v3-thinking",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-4.6-thinking"
  }
}
EOF

    # Create symlinks to shared resources
    ln -sf "$CLAUDE_DIR/commands" "$NANO_DIR/commands" 2>/dev/null || true
    ln -sf "$CLAUDE_DIR/scripts" "$NANO_DIR/scripts" 2>/dev/null || true
    ln -sf "$CLAUDE_DIR/hooks" "$NANO_DIR/hooks" 2>/dev/null || true
    ln -sf "$CLAUDE_DIR/CLAUDE.md" "$NANO_DIR/CLAUDE.md" 2>/dev/null || true
    ln -sf "$CLAUDE_DIR/.credentials.json" "$NANO_DIR/.credentials.json" 2>/dev/null || true

    log_success "Nano profile ready at $NANO_DIR"
    log_info "Use 'claude-nano' to run with NanoGPT models"
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

    # Check Statusline
    echo -n "  Statusline: "
    if [ -x "$CLAUDE_DIR/scripts/klean-statusline.py" ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}NOT INSTALLED${NC}"
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

    # Check nano profile
    echo -n "  Nano Profile: "
    if [ -d "${HOME}/.claude-nano" ] && [ -f "${HOME}/.claude-nano/settings.json" ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}NOT INSTALLED${NC}"
    fi

    # Check Factory Droids
    echo -n "  Factory Droids: "
    local droid_count=$(ls -1 "${HOME}/.factory/droids"/*.md 2>/dev/null | wc -l)
    if [ "$droid_count" -ge 8 ]; then
        echo -e "${GREEN}OK ($droid_count specialists)${NC}"
    elif [ "$droid_count" -gt 0 ]; then
        echo -e "${YELLOW}PARTIAL ($droid_count specialists)${NC}"
    else
        echo -e "${YELLOW}NOT INSTALLED${NC}"
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
    install_statusline
    install_knowledge
    install_knowledge_server_autostart
    install_litellm_config
    install_nano_profile
    install_droids

    # Optionally run LiteLLM setup wizard
    echo ""
    read -p "Setup LiteLLM provider now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_litellm_interactive
    fi

    echo ""
    verify_installation

    echo ""
    log_success "K-LEAN v$VERSION installed successfully!"
    echo ""
    echo "Profile system:"
    echo "  claude        - Native Anthropic (default)"
    echo "  claude-nano   - NanoGPT via LiteLLM"
    echo ""
    echo "Next steps:"
    echo "  1. Reload shell: source ~/.bashrc"
    echo "  2. Start LiteLLM: ~/.claude/scripts/litellm-start.sh"
    echo "  3. Test: claude-nano (for NanoGPT) or claude (for native)"
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
        --droids)
            install_droids
            ;;
        --statusline)
            install_statusline
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
