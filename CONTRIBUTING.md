# Contributing to K-LEAN

Thank you for your interest in contributing to K-LEAN! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all experience levels.

## Getting Started

### Prerequisites

- **Python 3.9+**
- **pipx** (for CLI installation)
- **Claude Code CLI** (for testing)
- **NanoGPT API key** (for model testing)

### Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/claudeAgentic.git
cd claudeAgentic

# 2. Install in development mode
pipx install -e review-system-backup --force

# 3. Set up your API key
export NANOGPT_API_KEY="your-key"

# 4. Verify installation
k-lean test
```

### Project Structure

```
claudeAgentic/
├── review-system-backup/       # Main source
│   ├── src/klean/              # K-LEAN CLI package
│   │   ├── cli.py              # CLI entry point
│   │   ├── commands/           # CLI subcommands
│   │   └── utils/              # Shared utilities
│   ├── scripts/                # Shell and Python scripts
│   ├── commands/kln/           # Slash command definitions
│   ├── hooks/                  # Claude Code hooks
│   ├── droids/                 # Specialist agent configs
│   └── config/                 # LiteLLM configurations
├── docs/                       # Documentation
│   ├── guides/                 # User guides
│   └── architecture/           # System design docs
└── tests/                      # Test files
```

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use the issue templates when available
3. Include:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version, etc.)

### Submitting Changes

1. **Fork** the repository
2. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following our coding standards
4. **Test your changes**:
   ```bash
   k-lean test
   ```
5. **Commit** with clear messages:
   ```bash
   git commit -m "Add feature: description of what it does"
   ```
6. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request** with:
   - Clear description of changes
   - Link to related issues
   - Test results

## Coding Standards

### Shell Scripts

- Use `#!/usr/bin/env bash` shebang for portability
- Quote all variables: `"$variable"`
- Use `[[ ]]` for conditionals
- Add comments for non-obvious logic
- Test on both Linux and macOS when possible

### Python

- Use `#!/usr/bin/env python3` shebang
- Follow PEP 8 style guidelines
- Use type hints where practical
- Document public functions with docstrings

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- First line: 50 characters or less
- Be descriptive: "Fix memory leak in KB server" not "Fix bug"

## Testing

### Running Tests

```bash
# Run full test suite
k-lean test

# Check specific components
k-lean doctor

# Test models
healthcheck
```

### What to Test

- **Scripts**: Test on fresh environment
- **CLI**: Test all subcommands
- **Integration**: Test with real Claude Code session

## Areas for Contribution

### Good First Issues

- Documentation improvements
- Adding tests
- Fixing typos
- Improving error messages

### Feature Ideas

- New specialist droids
- Additional model providers
- Performance improvements
- Cross-platform compatibility

### Documentation

- Improve existing guides
- Add examples and tutorials
- Translate documentation

## Release Process

Maintainers handle releases. Version numbering follows SemVer:
- **Major**: Breaking changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

## Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Documentation**: Check `/docs` folder

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to K-LEAN!
