# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting Vulnerabilities

**Do not open public GitHub issues for security vulnerabilities.**

Email security concerns to: calinfaja@gmail.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within 48 hours.

## Security Model

### Agent Sandboxing

K-LEAN agents are sandboxed:
- **Blocked imports**: `os`, `subprocess`, `sys`, `socket`, `pathlib`, `shutil`, `io`
- **Read-only tools**: Agents can read files but cannot write or execute
- **Step limits**: Agents have max_steps (5-10) to prevent runaway execution
- **Timeouts**: All subprocess and HTTP calls have timeouts

### API Key Handling

- API keys are stored in `~/.config/litellm/.env` (not in repo)
- Keys are never logged or transmitted beyond the configured LLM provider
- The `.env` file is in `.gitignore`

### LiteLLM Proxy

- Runs on `localhost:4000` only (not exposed to network)
- Acts as a local gateway to external LLM providers
