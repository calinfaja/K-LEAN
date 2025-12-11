"""CryptolibImplementationDroid - Specialized droid for cryptography code analysis.

This droid analyzes cryptographic implementations with focus on:
- Nordic nRF SDK cryptography patterns
- PSA Certified API compliance
- FIPS 140-3 requirements
- Side-channel resistance
- Key management practices
- Hardware acceleration integration
- Memory footprint optimization

Features:
- 5-turn multi-turn analysis for comprehensive cryptography assessment
- Supports PSA Crypto, MbedTLS, Oberon, and CryptoCell implementations
- Validates against FIPS 140-3 standards
- Detects common crypto vulnerabilities
- Provides Nordic-specific optimization recommendations
"""

import asyncio
import json
from typing import Any, Dict, Optional
from klean.droids.base import SDKDroid
from klean.utils import get_model_for_task, get_model_info


class CryptolibImplementationDroid(SDKDroid):
    """Specialized droid for cryptographic implementation analysis.

    Analyzes cryptographic code with focus on:
    - Nordic nRF SDK compliance (PSA Crypto, MbedTLS, Oberon, CryptoCell)
    - FIPS 140-3 compliance levels
    - Side-channel resistance and timing attacks
    - Key management and secure storage
    - Hardware acceleration (nRF52840, nRF5340, nRF9160)
    - Memory footprint optimization
    - DFU and secure boot integration

    Performs 5-turn analysis:
    1. Crypto Pattern Detection - Identifies crypto algorithms and patterns
    2. Compliance Assessment - FIPS 140-3 and PSA Certified API validation
    3. Security Analysis - Vulnerability and side-channel risk assessment
    4. Performance & Memory - Hardware acceleration and memory optimization
    5. Recommendations - Nordic SDK best practices and improvements
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize CryptolibImplementationDroid.

        Args:
            model: Optional model override. Defaults to qwen3-coder (best for crypto analysis)
        """
        # Set name and description before calling super().__init__()
        name = "CryptolibImplementationDroid"
        description = (
            "Specialized droid for cryptographic implementation analysis with focus on "
            "Nordic nRF SDK compliance, FIPS 140-3 standards, and embedded crypto best practices"
        )

        # Determine model
        if model:
            selected_model = model
        else:
            selected_model = get_model_for_task("security")  # qwen3-coder

        # Call parent constructor with required arguments
        super().__init__(name, description, model=selected_model)

        self.version = "1.0.0"

        # Nordic SDK crypto context
        self.nordic_context = {
            "sdk_versions": ["nRF5 SDK v17.1.1", "nRF Connect SDK v2.0+", "nRF Connect SDK v3.0+"],
            "crypto_libraries": [
                "PSA Certified Crypto API",
                "MbedTLS (PSA Certified)",
                "Oberon PSA Crypto",
                "CryptoCell-310/312",
                "nrf_oberon",
                "nrf_cc3xx_mbedcrypto",
                "nrf_cc310_bl",
            ],
            "supported_devices": [
                "nRF52840",
                "nRF5340",
                "nRF9160",
                "nRF52833",
                "nRF52832",
            ],
            "compliance_frameworks": [
                "FIPS 140-3 (Levels 1-4)",
                "PSA Certified API",
                "Common Criteria (CC)",
                "CWE Top 25",
                "OWASP Cryptographic Failures (A02:2021)",
            ]
        }

    async def execute(
        self,
        target: str,
        depth: str = "medium",
        focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute comprehensive cryptographic code analysis.

        Args:
            target: File or directory path to analyze
            depth: Analysis depth - "light", "medium", or "deep"
            focus: Optional focus area (e.g., "psa_api", "key_management", "performance")

        Returns:
            Dictionary with 5-turn analysis results containing:
            - crypto_patterns: Identified algorithms and patterns
            - compliance_assessment: FIPS and PSA Certified validation
            - security_analysis: Vulnerabilities and risks
            - performance_metrics: Memory and acceleration analysis
            - recommendations: Nordic-specific improvements
        """
        await self._initialize_client()

        system_prompt = self._build_system_prompt(depth, focus)
        results = {
            "format": "json",
            "droid": self.name,
            "version": self.version,
            "target": target,
            "depth": depth,
            "focus": focus,
            "turns": 0,
            "output": None,
        }

        try:
            # Read target file(s)
            file_content = await self._read_target(target)

            # Turn 1: Crypto Pattern Detection
            turn1_prompt = self._build_turn1_prompt(file_content)
            turn1_response = await self._call_claude(system_prompt, turn1_prompt)
            turn1_result = self._parse_response(turn1_response)

            # Turn 2: Compliance Assessment
            turn2_prompt = self._build_turn2_prompt(file_content, turn1_result)
            turn2_response = await self._call_claude(
                system_prompt,
                f"{turn1_prompt}\n\nAssistant:\n{turn1_response}\n\nUser:\n{turn2_prompt}"
            )
            turn2_result = self._parse_response(turn2_response)

            # Turn 3: Security Analysis
            turn3_prompt = self._build_turn3_prompt(file_content, turn1_result, turn2_result)
            turn3_response = await self._call_claude(
                system_prompt,
                f"{turn1_prompt}\n\nAssistant:\n{turn1_response}\n\n"
                f"User:\n{turn2_prompt}\n\nAssistant:\n{turn2_response}\n\n"
                f"User:\n{turn3_prompt}"
            )
            turn3_result = self._parse_response(turn3_response)

            # Turn 4: Performance & Memory Analysis
            turn4_prompt = self._build_turn4_prompt(file_content, turn1_result, turn3_result)
            turn4_response = await self._call_claude(
                system_prompt,
                f"{turn1_prompt}\n\nAssistant:\n{turn1_response}\n\n"
                f"User:\n{turn2_prompt}\n\nAssistant:\n{turn2_response}\n\n"
                f"User:\n{turn3_prompt}\n\nAssistant:\n{turn3_response}\n\n"
                f"User:\n{turn4_prompt}"
            )
            turn4_result = self._parse_response(turn4_response)

            # Turn 5: Nordic-Specific Recommendations
            turn5_prompt = self._build_turn5_prompt(file_content, turn1_result, turn3_result, turn4_result)
            turn5_response = await self._call_claude(
                system_prompt,
                f"{turn1_prompt}\n\nAssistant:\n{turn1_response}\n\n"
                f"User:\n{turn2_prompt}\n\nAssistant:\n{turn2_response}\n\n"
                f"User:\n{turn3_prompt}\n\nAssistant:\n{turn3_response}\n\n"
                f"User:\n{turn4_prompt}\n\nAssistant:\n{turn4_response}\n\n"
                f"User:\n{turn5_prompt}"
            )
            turn5_result = self._parse_response(turn5_response)

            # Consolidate results
            results["turns"] = 5
            results["output"] = json.dumps({
                "summary": {
                    "file": target,
                    "depth": depth,
                    "analysis_type": "cryptographic_implementation",
                    "nordic_sdk_version": self._detect_sdk_version(file_content),
                    "crypto_libraries_used": turn1_result.get("crypto_libraries_detected", []),
                },
                "turn_1_crypto_patterns": turn1_result,
                "turn_2_compliance_assessment": turn2_result,
                "turn_3_security_analysis": turn3_result,
                "turn_4_performance_metrics": turn4_result,
                "turn_5_recommendations": turn5_result,
                "overall_findings": self._synthesize_findings(
                    turn1_result, turn2_result, turn3_result, turn4_result, turn5_result
                ),
            })

            return results

        except Exception as e:
            results["error"] = str(e)
            results["output"] = json.dumps({"error": str(e), "type": type(e).__name__})
            return results

    def _build_system_prompt(self, depth: str, focus: Optional[str]) -> str:
        """Build system prompt for cryptographic analysis."""
        return f"""You are an expert cryptographer specializing in embedded systems and Nordic nRF SDK implementations.

Your expertise includes:
- PSA Certified Crypto APIs
- MbedTLS cryptography library
- Oberon PSA Crypto implementations
- nRF52/nRF53/nRF91 CryptoCell hardware acceleration
- FIPS 140-3 compliance validation (Levels 1-4)
- Side-channel attack resistance
- Secure key management
- DFU and secure boot integration
- Nordic nRF Connect SDK best practices

Analysis Depth: {depth}
{"Focus Area: " + focus if focus else ""}

Provide detailed, security-focused analysis in JSON format. Focus on:
1. Correct algorithm implementation
2. FIPS 140-3 compliance
3. Side-channel vulnerabilities
4. Key management security
5. Hardware acceleration usage
6. Memory footprint optimization
7. Nordic SDK compliance
"""

    def _build_turn1_prompt(self, file_content: str) -> str:
        """Build Turn 1: Crypto Pattern Detection prompt."""
        return f"""TURN 1: CRYPTOGRAPHIC PATTERN DETECTION

Analyze the provided code and identify:
1. Cryptographic algorithms used (AES, SHA, ECDH, ECDSA, etc.)
2. Crypto libraries detected (PSA Crypto, MbedTLS, Oberon, CryptoCell)
3. Hardware acceleration usage (nrf_cc310, nrf_cc3xx, etc.)
4. Key generation and storage methods
5. Random number generation sources

Code to analyze:
```
{file_content[:2000]}
```

Return JSON with:
{{
  "crypto_libraries_detected": ["library1", "library2"],
  "algorithms_identified": {{"symmetric": [], "asymmetric": [], "hash": [], "hmac": []}},
  "hardware_acceleration": {{"used": bool, "specific": "cc310|cc3xx|none"}},
  "key_sources": ["static", "derived", "hsm", "generated"],
  "rng_sources": ["TRNG", "PRNG", "hardware"],
  "patterns_found": []
}}"""

    def _build_turn2_prompt(self, file_content: str, turn1: Dict[str, Any]) -> str:
        """Build Turn 2: Compliance Assessment prompt."""
        return f"""TURN 2: COMPLIANCE ASSESSMENT

Based on the cryptographic patterns identified:
{json.dumps(turn1, indent=2)}

Validate against:
1. FIPS 140-3 requirements (which level: 1-4)
2. PSA Certified API compliance
3. CWE Top 25 for cryptography
4. OWASP A02:2021 Cryptographic Failures

Code section:
```
{file_content[:2000]}
```

Return JSON with:
{{
  "fips_140_3_level": "1|2|3|4",
  "psa_certified_compliance": {{"compliant": bool, "issues": []}},
  "cwe_violations": [{{"id": "CWE-123", "severity": "high", "description": ""}}],
  "owasp_issues": [{{"category": "A02:2021", "issue": ""}}],
  "compliance_score": 0.0
}}"""

    def _build_turn3_prompt(self, file_content: str, turn1: Dict[str, Any], turn2: Dict[str, Any]) -> str:
        """Build Turn 3: Security Analysis prompt."""
        return f"""TURN 3: SECURITY ANALYSIS

Analyze cryptographic security focusing on:
1. Side-channel attack vulnerabilities
2. Timing attack resistance
3. Key derivation security (PBKDF2, HKDF)
4. Random number generation quality
5. Secure erasure of sensitive data
6. Buffer overflow in crypto operations

Detected libraries: {turn1.get("crypto_libraries_detected", [])}
Compliance level: {turn2.get("fips_140_3_level", "unknown")}

Code:
```
{file_content[:2000]}
```

Return JSON with:
{{
  "side_channel_risks": [{{"type": "timing|power|cache", "severity": "high|medium|low", "description": ""}}],
  "key_management_issues": [],
  "rng_quality": {{"secure": bool, "issues": []}},
  "sensitive_data_erasure": {{"implemented": bool, "quality": "good|poor"}},
  "vulnerabilities": [{{"id": "CWE-123", "severity": "critical|high|medium", "location": "line_x"}}],
  "security_score": 0.0
}}"""

    def _build_turn4_prompt(self, file_content: str, turn1: Dict[str, Any], turn3: Dict[str, Any]) -> str:
        """Build Turn 4: Performance & Memory Analysis prompt."""
        return f"""TURN 4: PERFORMANCE & MEMORY ANALYSIS

Analyze crypto implementation for embedded systems:
1. Memory footprint (flash + RAM usage)
2. Hardware acceleration efficiency
3. Optimization opportunities
4. Stack usage in crypto operations
5. Suitable for nRF52840/nRF5340/nRF9160

Libraries: {turn1.get("crypto_libraries_detected", [])}
Hardware acceleration: {turn1.get("hardware_acceleration", {}).get("specific", "none")}

Code:
```
{file_content[:2000]}
```

Return JSON with:
{{
  "memory_estimate": {{"flash_kb": 0, "ram_kb": 0, "stack_kb": 0}},
  "hardware_acceleration": {{"used": bool, "efficiency": "high|medium|low"}},
  "performance_issues": [],
  "optimization_opportunities": [{{"type": "", "expected_savings_kb": 0}}],
  "nrf_device_compatibility": ["nRF52840", "nRF5340"],
  "memory_score": 0.0
}}"""

    def _build_turn5_prompt(self, file_content: str, turn1: Dict[str, Any],
                            turn3: Dict[str, Any], turn4: Dict[str, Any]) -> str:
        """Build Turn 5: Nordic-Specific Recommendations prompt."""
        return f"""TURN 5: NORDIC SDK RECOMMENDATIONS

Based on complete analysis:

Libraries detected: {turn1.get("crypto_libraries_detected", [])}
Security score: {turn3.get("security_score", "unknown")}
Memory footprint: {turn4.get("memory_estimate", {})}

Provide Nordic nRF SDK specific recommendations:
1. PSA Crypto API best practices
2. Hardware acceleration optimization (CryptoCell)
3. Secure boot and DFU integration
4. Key storage strategies
5. Multi-platform support (nRF5 SDK vs nRF Connect SDK)
6. Power optimization

Return JSON with:
{{
  "nordic_best_practices": [],
  "psa_crypto_optimization": [{{"current": "", "recommended": "", "benefit": ""}}],
  "hardware_acceleration_recommendations": [],
  "secure_boot_improvements": [],
  "dfu_security": {{"secure": bool, "recommendations": []}},
  "code_migration_guide": {{"from": "", "to": "", "steps": []}},
  "estimated_improvements": {{
    "security_increase_percent": 0,
    "memory_savings_percent": 0,
    "performance_gain_percent": 0
  }},
  "priority_fixes": [{{"priority": "critical|high|medium", "issue": "", "effort": "low|medium|high"}}]
}}"""

    def _detect_sdk_version(self, content: str) -> str:
        """Detect Nordic SDK version from code."""
        if "nrf_connect" in content.lower():
            return "nRF Connect SDK"
        elif "nrf5_sdk" in content.lower():
            return "nRF5 SDK"
        else:
            return "unknown"

    def _synthesize_findings(self, turn1: Dict, turn2: Dict, turn3: Dict,
                             turn4: Dict, turn5: Dict) -> Dict[str, Any]:
        """Synthesize all findings into executive summary."""
        return {
            "analysis_complete": True,
            "crypto_libraries": turn1.get("crypto_libraries_detected", []),
            "compliance_level": turn2.get("fips_140_3_level", "unknown"),
            "security_score": turn3.get("security_score", 0.0),
            "memory_score": turn4.get("memory_score", 0.0),
            "critical_issues": len(turn3.get("vulnerabilities", [])),
            "recommended_actions": turn5.get("priority_fixes", []),
            "overall_readiness": self._calculate_readiness(turn2, turn3, turn4),
        }

    def _calculate_readiness(self, turn2: Dict, turn3: Dict, turn4: Dict) -> str:
        """Calculate overall cryptographic implementation readiness."""
        security_score = turn3.get("security_score", 0.0)
        memory_score = turn4.get("memory_score", 0.0)
        compliance_score = turn2.get("compliance_score", 0.0)

        avg_score = (security_score + memory_score + compliance_score) / 3

        if avg_score >= 0.85:
            return "PRODUCTION_READY"
        elif avg_score >= 0.70:
            return "READY_WITH_MINOR_FIXES"
        elif avg_score >= 0.50:
            return "NEEDS_SIGNIFICANT_WORK"
        else:
            return "NOT_READY"

    async def _read_target(self, target: str) -> str:
        """Read target file content."""
        try:
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read {target}: {e}")

    async def _call_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Call Claude API with system and user prompts."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        return message.content[0].text

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from Claude."""
        try:
            # Try to find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {"raw_response": response}
        except json.JSONDecodeError:
            return {"raw_response": response}
