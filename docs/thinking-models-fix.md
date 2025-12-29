# Thinking Models Support in K-LEAN

**Last Updated:** 2025-12-29 (Implementation Complete)

## Problem Summary

**Issue:** Thinking models (glm-4.6-thinking, deepseek-v3-thinking, kimi-k2-thinking, minimax-m2) return responses in `reasoning_content` field instead of `content`. Tools like smolagents only read `content`, causing failures.

**Error:**
```
Error in code parsing:
Expecting value: line 1 column 1 (char 0)
Make sure to provide correct code blobs.
```

---

## Solution: LiteLLM Native Setting (IMPLEMENTED)

LiteLLM has a built-in per-model setting that merges reasoning content into the content field:

```yaml
# ~/.config/litellm/config.yaml
litellm_settings:
  drop_params: true

model_list:
  # Thinking models - add merge_reasoning_content_in_choices: true
  - model_name: deepseek-r1
    litellm_params:
      model: openai/deepseek-ai/DeepSeek-R1-0528
      api_base: os.environ/NANOGPT_API_BASE
      api_key: os.environ/NANOGPT_API_KEY
      merge_reasoning_content_in_choices: true

  - model_name: glm-4.6-thinking
    litellm_params:
      model: openai/z-ai/glm-4.6:thinking
      api_base: os.environ/NANOGPT_API_BASE
      api_key: os.environ/NANOGPT_API_KEY
      merge_reasoning_content_in_choices: true

  - model_name: kimi-k2-thinking
    litellm_params:
      model: openai/moonshotai/kimi-k2-thinking
      api_base: os.environ/NANOGPT_API_BASE
      api_key: os.environ/NANOGPT_API_KEY
      merge_reasoning_content_in_choices: true

  - model_name: minimax-m2
    litellm_params:
      model: openai/MiniMax-M2
      api_base: os.environ/NANOGPT_API_BASE
      api_key: os.environ/NANOGPT_API_KEY
      merge_reasoning_content_in_choices: true
```

**How it works:**
- LiteLLM copies `reasoning_content` to `content` with `<think></think>` tags
- Response includes both fields for maximum compatibility
- Works for regular chat completions

**Verification:**
```bash
curl http://localhost:4000/health | jq '.healthy_endpoints[] | select(.merge_reasoning_content_in_choices == true) | .model'
```

---

## Known Limitation: openai/ Prefix + smolagents

**Critical Finding (2025-12-24):** The `merge_reasoning_content_in_choices` setting **does NOT work** with the `openai/` prefix we use for NanoGPT.

### Root Cause

LiteLLM only activates reasoning content merging for **specific providers** it recognizes as supporting reasoning:
- `deepseek/` - DeepSeek native provider
- `anthropic/` - Anthropic with extended thinking
- `bedrock/` - AWS Bedrock
- `vertex_ai/` - Google Vertex AI
- `openrouter/` - OpenRouter
- `xai/`, `google/`, `perplexity/`, `mistral/`, `groq/`

The `openai/` prefix (used for OpenAI-compatible endpoints like NanoGPT) is **NOT** recognized as a reasoning provider. Even with `merge_reasoning_content_in_choices: true`, LiteLLM treats these as standard OpenAI models and doesn't merge reasoning_content.

### Why smolagents CodeAgent Fails

1. **NanoGPT returns reasoning in a separate field** - `reasoning_content` is populated, `content` has just the answer
2. **LiteLLM doesn't merge for openai/ prefix** - The setting is ignored because the provider isn't recognized
3. **smolagents only reads `content`** - It never sees the reasoning, gets empty/minimal content
4. **JSON parsing fails** - "Error in code parsing: Expecting value: line 1 column 1 (char 0)"

### Test Results (2025-12-24)

| Model | Regular Chat | smolagents CodeAgent |
|-------|-------------|---------------------|
| qwen3-coder | Works | Works |
| hermes-4-70b | Works | Works |
| glm-4.6-thinking | Works | Fails |
| deepseek-v3-thinking | Works | Fails |
| kimi-k2-thinking | Works | Fails |
| minimax-m2 | Works | Fails |

---

## Recommendations

### For SmolKLN Agents (smolagents CodeAgent)

**Use non-thinking models:**
```bash
smol-kln code-reviewer "task" --model qwen3-coder     # Works
smol-kln security-auditor "task" --model hermes-4-70b # Works
```

**Avoid thinking models:**
```bash
# These will fail with smolagents CodeAgent
smol-kln code-reviewer "task" --model glm-4.6-thinking  # Fails
```

### For Other Tools (kln:quick, kln:multi, direct API)

**Thinking models work fine:**
```bash
# These work because they use regular chat completions
~/.claude/scripts/quick-review.sh --model glm-4.6-thinking

# Direct API also works
curl http://localhost:4000/chat/completions \
  -d '{"model": "glm-4.6-thinking", "messages": [...]}'
```

---

## Future Solutions

### Option 1: Wait for smolagents Support

smolagents has open issues for thinking model support:
- [#1774](https://github.com/huggingface/smolagents/issues/1774) - Optimize for reasoning models
- [#1869](https://github.com/huggingface/smolagents/issues/1869) - Interleaved Thinking
- [#430](https://github.com/huggingface/smolagents/issues/430) - DeepSeek Reasoner issues

When smolagents adds native `reasoning_content` support, thinking models will work with CodeAgent.

### Option 2: NanoGPT v1thinking Endpoint (Investigated - Not a Solution)

NanoGPT has a `/api/v1thinking/` endpoint documented for "richer reasoning streams". However:
- It returns reasoning in a separate `reasoning` field, NOT inline `<think>` tags
- LiteLLM normalizes this to `reasoning_content` but doesn't merge into content
- This doesn't solve the smolagents compatibility issue

### Option 3: Use OpenRouter Provider

If NanoGPT models are available through OpenRouter, we could use the `openrouter/` prefix which LiteLLM recognizes as supporting reasoning.

### Option 4: Custom Proxy Middleware

Create a lightweight proxy between smolagents and LiteLLM that merges `reasoning_content` into `content` before returning the response.

### Option 5: Patch smolagents Locally

Fork smolagents and add support for reading `reasoning_content` in the LiteLLMModel class.

---

## Investigation Notes (2025-12-24)

**Phoenix trace analysis** showed that at 12:10 today, thinking models WERE working with smolagents - the response format was `<think>...</think>{"thought":"...","code":"..."}`. However, current NanoGPT API responses return reasoning in a separate field, not inline.

**Possible explanations:**
1. NanoGPT API behavior changed during the day
2. Intermittent behavior based on model load/routing
3. Different backend handling for the same model

**Current recommendation:** Use non-thinking models (qwen3-coder, kimi-k2, devstral-2) for SmolKLN agents until a reliable solution is found.

---

## Deprecated: Custom Callback Approach

Earlier we tried implementing a custom LiteLLM callback (`callbacks.thinking_transform.thinking_handler`). This approach **does not work** because:

1. LiteLLM callbacks are for **logging/observability**, not response transformation
2. The callback fires AFTER the response is sent to the client
3. Modifying the response in a callback has no effect on what the client receives

The `merge_reasoning_content_in_choices: true` per-model setting is the correct approach.

---

## Configuration Files

**Installed by `k-lean install`:**
- `~/.config/litellm/config.yaml` - LiteLLM configuration with thinking models
- `~/.config/litellm/.env` - Environment variables (NANOGPT_API_KEY, NANOGPT_API_BASE)

**CRITICAL: No Quotes Around os.environ Values**

The `os.environ/` syntax in LiteLLM config MUST NOT have quotes:

```yaml
# CORRECT - no quotes
api_base: os.environ/NANOGPT_API_BASE
api_key: os.environ/NANOGPT_API_KEY

# WRONG - quotes break env var loading
api_base: "os.environ/NANOGPT_API_BASE"
api_key: "os.environ/NANOGPT_API_KEY"
```

With quotes, LiteLLM treats the value as a literal string and fails to resolve the environment variable.

**Start LiteLLM:**
```bash
~/.claude/scripts/start-litellm.sh
# or
k-lean start
```

---

## Sources

- [LiteLLM Reasoning Content Documentation](https://docs.litellm.ai/docs/reasoning_content)
- [LiteLLM merge_reasoning_content_in_choices](https://docs.litellm.ai/docs/tutorials/openweb_ui)
- [smolagents GitHub Issues](https://github.com/huggingface/smolagents/issues?q=reasoning)
