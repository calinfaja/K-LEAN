# Contributing to K-LEAN

Thank you for your interest in contributing to K-LEAN!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/k-lean.git
   cd k-lean
   ```
3. Install in development mode:
   ```bash
   pipx install -e .
   kln install --dev
   ```
4. Verify installation:
   ```bash
   kln test
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Test your changes:
   ```bash
   kln test
   ```
4. Commit with clear messages
5. Push and create a Pull Request

## Code Style

- **Python**: Follow PEP 8
- **Bash**: Use shellcheck, quote variables
- **Documentation**: Update relevant docs with changes

## Pull Request Guidelines

- One feature/fix per PR
- Update documentation as needed
- Add tests for new functionality
- Ensure `kln test` passes

## Reporting Issues

Use GitHub Issues with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- K-LEAN version (`kln version`)

## Questions?

Open a Discussion on GitHub.
