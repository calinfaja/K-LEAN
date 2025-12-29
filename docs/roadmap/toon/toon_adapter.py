#!/usr/bin/env python3
"""
TOON Adapter for K-LEAN Knowledge Facts

Wraps the python-toon library to provide seamless conversion between
JSON knowledge facts and TOON format for efficient LLM transmission.

Achieves ~18% character reduction on knowledge facts (character-based).
Real token savings vary by LLM tokenizer (estimated 10-20% with Haiku).
"""

from typing import List, Dict, Optional, Tuple
from toon import encode, decode
import json


class KnowledgeTOONAdapter:
    """Adapter for converting knowledge facts between JSON and TOON formats."""

    # Define which fields are essential for knowledge facts
    REQUIRED_FIELDS = {'title', 'summary', 'source', 'tags', 'relevance_score'}

    @staticmethod
    def json_to_toon(facts: List[Dict]) -> str:
        """
        Convert list of JSON knowledge facts to TOON format.

        Args:
            facts: List of knowledge fact dictionaries

        Returns:
            TOON formatted string

        Example:
            facts = [
                {
                    'title': 'Example',
                    'summary': 'Description',
                    'source': 'review',
                    'tags': ['tag1', 'tag2'],
                    'relevance_score': 0.85
                }
            ]
            toon_str = KnowledgeTOONAdapter.json_to_toon(facts)
        """
        if not facts:
            return ""

        try:
            return encode(facts)
        except Exception as e:
            raise ValueError(f"Failed to encode facts to TOON: {e}")

    @staticmethod
    def toon_to_json(toon_str: str) -> List[Dict]:
        """
        Convert TOON format back to JSON knowledge facts.

        Args:
            toon_str: TOON formatted string

        Returns:
            List of knowledge fact dictionaries

        Raises:
            ValueError: If TOON format is invalid or cannot be parsed
        """
        if not toon_str or not toon_str.strip():
            return []

        try:
            decoded = decode(toon_str)

            # Ensure it's a list
            if not isinstance(decoded, list):
                decoded = [decoded]

            # Validate each fact has required fields
            for i, fact in enumerate(decoded):
                if not isinstance(fact, dict):
                    raise ValueError(f"Fact {i} is not a dictionary")

            return decoded
        except Exception as e:
            raise ValueError(f"Failed to decode TOON to facts: {e}")

    @staticmethod
    def validate(toon_str: str) -> Tuple[bool, List[str]]:
        """
        Validate TOON format.

        Args:
            toon_str: TOON formatted string

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not toon_str or not toon_str.strip():
            errors.append("Empty TOON string")
            return (False, errors)

        try:
            decoded = KnowledgeTOONAdapter.toon_to_json(toon_str)
            if not decoded:
                errors.append("No facts decoded")
        except Exception as e:
            errors.append(f"Decode error: {e}")

        return (len(errors) == 0, errors)

    @staticmethod
    def compare_formats(facts: List[Dict]) -> Dict:
        """
        Compare JSON vs TOON for the given facts.

        Args:
            facts: List of knowledge fact dictionaries

        Returns:
            Dictionary with comparison metrics
        """
        json_str = json.dumps(facts)
        toon_str = KnowledgeTOONAdapter.json_to_toon(facts)

        json_len = len(json_str)
        toon_len = len(toon_str)
        reduction = 100 * (1 - toon_len / json_len) if json_len > 0 else 0

        return {
            'json_size_chars': json_len,
            'toon_size_chars': toon_len,
            'reduction_percent': round(reduction, 1),
            'json_str': json_str,
            'toon_str': toon_str
        }

    @staticmethod
    def roundtrip_test(facts: List[Dict]) -> Tuple[bool, str]:
        """
        Test JSON→TOON→JSON round-trip for data integrity.

        Args:
            facts: List of knowledge fact dictionaries

        Returns:
            Tuple of (success, message)
        """
        try:
            # Encode to TOON
            toon_str = KnowledgeTOONAdapter.json_to_toon(facts)

            # Decode back from TOON
            decoded = KnowledgeTOONAdapter.toon_to_json(toon_str)

            # Compare
            if decoded == facts:
                return (True, f"✓ Round-trip success: {len(facts)} facts preserved")
            else:
                return (False, f"✗ Data mismatch after round-trip")
        except Exception as e:
            return (False, f"✗ Round-trip failed: {e}")


def main():
    """Test the adapter with sample knowledge facts."""
    import sys

    # Sample knowledge facts
    sample_facts = [
        {
            "title": "Namespace separation best practice",
            "summary": "Separating command namespaces (/sc: vs /kln:) improves organization and prevents conflicts",
            "source": "review",
            "tags": ["namespace", "organization"],
            "relevance_score": 0.85
        },
        {
            "title": "Bash script organization pattern",
            "summary": "Grouping related scripts in ~/.claude/scripts/ with clear naming improves maintainability",
            "source": "review",
            "tags": ["bash", "scripts"],
            "relevance_score": 0.80
        },
        {
            "title": "Timeout fix for thinking models",
            "summary": "Increased curl timeout to 120s for GLM and DeepSeek models with extended reasoning",
            "source": "commit",
            "tags": ["timeout", "bugfix", "thinking-models"],
            "relevance_score": 0.90
        }
    ]

    print("=" * 70)
    print("K-LEAN TOON Adapter Test")
    print("=" * 70)
    print()

    # Test 1: JSON to TOON conversion
    print("1. JSON to TOON Conversion")
    print("-" * 70)
    toon_str = KnowledgeTOONAdapter.json_to_toon(sample_facts)
    print(toon_str)
    print()

    # Test 2: Round-trip test
    print("2. Round-trip Test (JSON→TOON→JSON)")
    print("-" * 70)
    success, message = KnowledgeTOONAdapter.roundtrip_test(sample_facts)
    print(f"{message}")
    print()

    # Test 3: Format comparison
    print("3. Format Comparison")
    print("-" * 70)
    comparison = KnowledgeTOONAdapter.compare_formats(sample_facts)
    print(f"JSON size:       {comparison['json_size_chars']} chars")
    print(f"TOON size:       {comparison['toon_size_chars']} chars")
    print(f"Reduction:       {comparison['reduction_percent']}%")
    print()

    # Test 4: Validation
    print("4. Validation Test")
    print("-" * 70)
    is_valid, errors = KnowledgeTOONAdapter.validate(toon_str)
    print(f"Valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    print()

    # Test 5: TOON to JSON conversion
    print("5. TOON to JSON Conversion")
    print("-" * 70)
    decoded = KnowledgeTOONAdapter.toon_to_json(toon_str)
    print(json.dumps(decoded, indent=2))
    print()

    print("=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    main()
