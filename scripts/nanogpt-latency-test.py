#!/usr/bin/env python3
"""
NanoGPT Model Latency & Quality Test
=====================================
Tests top 10 subscription models for coding/agent tasks.
Based on benchmark research: SWE-bench, LiveCodeBench, agentic capabilities.
"""

import time
import json
import statistics
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.run(["pip", "install", "requests", "-q"])
    import requests

# NanoGPT API configuration
NANOGPT_API = "https://nano-gpt.com/api/v1/chat/completions"

# Top 10 Models for Coding/Software Dev/Agents (Research-backed)
TOP_MODELS = {
    # Tier 1: Elite Coding Models
    "qwen3-coder": {
        "id": "qwen/qwen3-coder",
        "name": "Qwen3 Coder 480B",
        "tier": "Elite",
        "strengths": "Best OSS coder, 480B MoE, agentic",
        "ctx": 262000,
        "cost": "$0.13/$0.50"
    },
    "deepseek-r1": {
        "id": "deepseek-ai/DeepSeek-R1-0528",
        "name": "DeepSeek R1 0528",
        "tier": "Elite",
        "strengths": "Top reasoning, 97.3% MATH-500",
        "ctx": 128000,
        "cost": "$0.40/$1.70"
    },
    "kimi-k2-thinking": {
        "id": "moonshotai/kimi-k2-thinking",
        "name": "Kimi K2 Thinking",
        "tier": "Elite",
        "strengths": "Top LiveCodeBench, great agents",
        "ctx": 256000,
        "cost": "$0.30/$1.20"
    },

    # Tier 2: Strong Performers
    "glm-4.6-thinking": {
        "id": "z-ai/glm-4.6:thinking",
        "name": "GLM 4.6 Thinking",
        "tier": "Strong",
        "strengths": "68% SWE-bench, 82.8% LiveCodeBench",
        "ctx": 200000,
        "cost": "$0.40/$1.50"
    },
    "deepseek-v3.2": {
        "id": "deepseek-ai/deepseek-v3.2-exp-thinking",
        "name": "DeepSeek V3.2 Thinking",
        "tier": "Strong",
        "strengths": "Latest V3, improved coding",
        "ctx": 163840,
        "cost": "$0.28/$0.42"
    },
    "devstral-2": {
        "id": "mistralai/devstral-2-123b-instruct-2512",
        "name": "Devstral 2 123B",
        "tier": "Strong",
        "strengths": "Coding-optimized, 262K ctx",
        "ctx": 262144,
        "cost": "$0.40/$1.40"
    },

    # Tier 3: Value Champions
    "qwen3-235b-thinking": {
        "id": "Qwen/Qwen3-235B-A22B-Thinking-2507",
        "name": "Qwen3 235B Thinking",
        "tier": "Value",
        "strengths": "Large MoE, thinking, 256K ctx",
        "ctx": 256000,
        "cost": "$0.30/$0.50"
    },
    "hermes-4-70b": {
        "id": "NousResearch/Hermes-4-70B:thinking",
        "name": "Hermes 4 70B Thinking",
        "tier": "Value",
        "strengths": "Script/agent specialist",
        "ctx": 128000,
        "cost": "$0.20/$0.40"
    },

    # Tier 4: Special Purpose
    "llama-4-maverick": {
        "id": "meta-llama/llama-4-maverick",
        "name": "Llama 4 Maverick",
        "tier": "Special",
        "strengths": "1M ctx, vision, versatile",
        "ctx": 1048576,
        "cost": "$0.18/$0.80"
    },
    "minimax-m2": {
        "id": "MiniMax-M2",
        "name": "MiniMax M2",
        "tier": "Special",
        "strengths": "Good reasoning, 200K ctx",
        "ctx": 200000,
        "cost": "$0.17/$1.53"
    },
}

# Test prompts for different scenarios
TEST_PROMPTS = {
    "coding": {
        "prompt": "Write a Python function that implements a thread-safe LRU cache with TTL expiration. Include type hints and docstring.",
        "expected_keywords": ["def", "class", "cache", "lock", "ttl"]
    },
    "reasoning": {
        "prompt": "Explain step by step: If a function has O(n log n) complexity and processes 1 million items in 2 seconds, approximately how long will it take to process 10 million items?",
        "expected_keywords": ["log", "time", "factor", "complexity"]
    },
    "agent": {
        "prompt": "I need to refactor a Python codebase. List the exact steps and commands you would use to: 1) Find all deprecated API calls, 2) Create a migration plan, 3) Apply changes safely. Be specific with tool/command names.",
        "expected_keywords": ["grep", "git", "test", "refactor", "branch"]
    }
}


def get_api_key():
    """Get NanoGPT API key from environment or LiteLLM config."""
    import os

    # Try environment variable first
    key = os.environ.get("NANOGPT_API_KEY")
    if key:
        return key

    # Try LiteLLM config
    config_paths = [
        os.path.expanduser("~/.config/litellm/config.yaml"),
        os.path.expanduser("~/litellm_config.yaml"),
    ]

    for path in config_paths:
        if os.path.exists(path):
            try:
                import yaml
                with open(path) as f:
                    config = yaml.safe_load(f)
                    for entry in config.get("model_list", []):
                        params = entry.get("litellm_params", {})
                        if "nano-gpt" in params.get("api_base", ""):
                            return params.get("api_key")
            except:
                pass

    return None


def test_model(model_key: str, model_info: dict, prompt_type: str, api_key: str, timeout: int = 60) -> dict:
    """Test a single model and return metrics."""
    prompt_data = TEST_PROMPTS[prompt_type]

    result = {
        "model": model_key,
        "name": model_info["name"],
        "tier": model_info["tier"],
        "prompt_type": prompt_type,
        "success": False,
        "latency_ttfb": None,  # Time to first byte
        "latency_total": None,
        "tokens_output": 0,
        "tokens_per_sec": 0,
        "quality_score": 0,
        "error": None
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_info["id"],
        "messages": [
            {"role": "system", "content": "You are an expert software engineer. Be concise and precise."},
            {"role": "user", "content": prompt_data["prompt"]}
        ],
        "max_tokens": 1000,
        "temperature": 0.3,
        "stream": True
    }

    try:
        start_time = time.time()
        first_token_time = None
        full_response = ""

        response = requests.post(
            NANOGPT_API,
            headers=headers,
            json=payload,
            stream=True,
            timeout=timeout
        )

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            return result

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                if first_token_time is None:
                                    first_token_time = time.time()
                                full_response += content
                    except json.JSONDecodeError:
                        pass

        end_time = time.time()

        # Calculate metrics
        result["latency_total"] = round(end_time - start_time, 2)
        result["latency_ttfb"] = round(first_token_time - start_time, 2) if first_token_time else None
        result["tokens_output"] = len(full_response.split())  # Approximate

        if result["latency_total"] > 0 and result["tokens_output"] > 0:
            result["tokens_per_sec"] = round(result["tokens_output"] / result["latency_total"], 1)

        # Quality scoring (presence of expected keywords)
        response_lower = full_response.lower()
        matches = sum(1 for kw in prompt_data["expected_keywords"] if kw in response_lower)
        result["quality_score"] = round(matches / len(prompt_data["expected_keywords"]) * 100)

        result["success"] = True
        result["response_preview"] = full_response[:200] + "..." if len(full_response) > 200 else full_response

    except requests.Timeout:
        result["error"] = f"Timeout after {timeout}s"
    except Exception as e:
        result["error"] = str(e)[:200]

    return result


def run_tests(api_key: str, models: list = None, prompt_types: list = None, parallel: bool = False):
    """Run tests on selected models."""
    if models is None:
        models = list(TOP_MODELS.keys())
    if prompt_types is None:
        prompt_types = ["coding"]  # Default to coding test

    results = []
    total_tests = len(models) * len(prompt_types)

    print(f"\n🧪 NanoGPT Model Latency Test")
    print(f"{'='*60}")
    print(f"Testing {len(models)} models × {len(prompt_types)} prompts = {total_tests} tests")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    if parallel:
        # Parallel execution
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for model_key in models:
                if model_key not in TOP_MODELS:
                    print(f"⚠️  Unknown model: {model_key}")
                    continue
                for prompt_type in prompt_types:
                    future = executor.submit(
                        test_model, model_key, TOP_MODELS[model_key], prompt_type, api_key
                    )
                    futures[future] = (model_key, prompt_type)

            completed = 0
            for future in as_completed(futures):
                model_key, prompt_type = futures[future]
                result = future.result()
                results.append(result)
                completed += 1

                status = "✅" if result["success"] else "❌"
                latency = f"{result['latency_total']}s" if result['latency_total'] else "N/A"
                print(f"[{completed}/{total_tests}] {status} {result['name'][:25]:25} | {prompt_type:10} | {latency:8} | {result.get('tokens_per_sec', 0):5.1f} tok/s")
    else:
        # Sequential execution
        completed = 0
        for model_key in models:
            if model_key not in TOP_MODELS:
                print(f"⚠️  Unknown model: {model_key}")
                continue
            for prompt_type in prompt_types:
                completed += 1
                print(f"[{completed}/{total_tests}] Testing {TOP_MODELS[model_key]['name'][:30]} ({prompt_type})...", end=" ", flush=True)

                result = test_model(model_key, TOP_MODELS[model_key], prompt_type, api_key)
                results.append(result)

                if result["success"]:
                    print(f"✅ {result['latency_total']}s | {result['tokens_per_sec']} tok/s | Q:{result['quality_score']}%")
                else:
                    print(f"❌ {result['error'][:50]}")

    return results


def generate_ranking(results: list) -> str:
    """Generate a markdown ranking table."""
    # Aggregate results by model
    model_stats = {}
    for r in results:
        if not r["success"]:
            continue
        key = r["model"]
        if key not in model_stats:
            model_stats[key] = {
                "name": r["name"],
                "tier": r["tier"],
                "latencies": [],
                "ttfbs": [],
                "speeds": [],
                "qualities": [],
                "info": TOP_MODELS.get(key, {})
            }
        model_stats[key]["latencies"].append(r["latency_total"])
        if r["latency_ttfb"]:
            model_stats[key]["ttfbs"].append(r["latency_ttfb"])
        model_stats[key]["speeds"].append(r["tokens_per_sec"])
        model_stats[key]["qualities"].append(r["quality_score"])

    # Calculate averages and composite score
    rankings = []
    for key, stats in model_stats.items():
        avg_latency = statistics.mean(stats["latencies"]) if stats["latencies"] else 999
        avg_ttfb = statistics.mean(stats["ttfbs"]) if stats["ttfbs"] else 999
        avg_speed = statistics.mean(stats["speeds"]) if stats["speeds"] else 0
        avg_quality = statistics.mean(stats["qualities"]) if stats["qualities"] else 0

        # Composite score: Lower latency + higher quality = better
        # Normalize: speed weight 0.3, quality 0.4, low latency 0.3
        composite = (avg_speed * 0.3) + (avg_quality * 0.4) + ((100 / max(avg_latency, 1)) * 0.3)

        rankings.append({
            "key": key,
            "name": stats["name"],
            "tier": stats["tier"],
            "avg_latency": round(avg_latency, 2),
            "avg_ttfb": round(avg_ttfb, 2),
            "avg_speed": round(avg_speed, 1),
            "avg_quality": round(avg_quality),
            "composite": round(composite, 1),
            "cost": stats["info"].get("cost", "N/A"),
            "ctx": stats["info"].get("ctx", 0),
            "strengths": stats["info"].get("strengths", "")
        })

    # Sort by composite score (higher is better)
    rankings.sort(key=lambda x: x["composite"], reverse=True)

    # Generate markdown
    md = []
    md.append("\n## 🏆 NanoGPT Model Ranking (Subscription Tier)")
    md.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    md.append("### Top 10 for Coding/Software Dev/Agents\n")
    md.append("| Rank | Model | Tier | TTFB | Total | Speed | Quality | Score | Cost |")
    md.append("|:----:|:------|:----:|-----:|------:|------:|--------:|------:|:-----|")

    medals = ["🥇", "🥈", "🥉"] + [""] * 7
    for i, r in enumerate(rankings[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        md.append(f"| {medal} | **{r['name'][:25]}** | {r['tier']} | {r['avg_ttfb']}s | {r['avg_latency']}s | {r['avg_speed']} t/s | {r['avg_quality']}% | {r['composite']} | {r['cost']} |")

    md.append("\n### Legend")
    md.append("- **TTFB**: Time to First Byte (streaming start)")
    md.append("- **Total**: Total response time")
    md.append("- **Speed**: Tokens per second")
    md.append("- **Quality**: Keyword match score")
    md.append("- **Score**: Composite (speed×0.3 + quality×0.4 + latency×0.3)")

    md.append("\n### Model Details\n")
    for r in rankings:
        md.append(f"- **{r['name']}** ({r['key']}): {r['strengths']} | Context: {r['ctx']:,} tokens")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="NanoGPT Model Latency Test")
    parser.add_argument("--models", "-m", nargs="+", help="Models to test (default: all)")
    parser.add_argument("--prompts", "-p", nargs="+", choices=["coding", "reasoning", "agent"],
                        default=["coding"], help="Prompt types to test")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick test (first 5 models only)")
    parser.add_argument("--output", "-o", help="Output file for results")
    parser.add_argument("--list", "-l", action="store_true", help="List available models")
    args = parser.parse_args()

    if args.list:
        print("\n📋 Available Models for Testing:\n")
        for key, info in TOP_MODELS.items():
            print(f"  {key:25} | {info['name']:25} | {info['tier']:8} | {info['cost']}")
        return

    api_key = get_api_key()
    if not api_key:
        print("❌ No API key found. Set NANOGPT_API_KEY environment variable.")
        print("   Or configure in ~/.config/litellm/config.yaml")
        return

    models = args.models
    if args.quick:
        models = list(TOP_MODELS.keys())[:5]

    results = run_tests(api_key, models, args.prompts, args.parallel)

    # Generate ranking
    ranking = generate_ranking(results)
    print(ranking)

    # Save results
    if args.output:
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "ranking_md": ranking
        }
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")


if __name__ == "__main__":
    main()
