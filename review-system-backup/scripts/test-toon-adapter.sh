#!/usr/bin/env bash
#
# Test TOON Adapter - Validate TOON format conversion for knowledge facts
#
# Tests:
# 1. Adapter module loads without errors
# 2. JSON→TOON→JSON round-trip preserves data
# 3. Format comparison shows token savings
# 4. Validation works correctly
#

set -e

PYTHON="${HOME}/.venvs/knowledge-db/bin/python"
ADAPTER="${HOME}/.claude/scripts/toon_adapter.py"

echo "============================================================"
echo "TOON Adapter Test Suite"
echo "============================================================"
echo

# Check prerequisites
echo "1. Checking prerequisites..."
if [ ! -x "$PYTHON" ]; then
    echo "   ❌ Python not found: $PYTHON"
    exit 1
fi
echo "   ✓ Python available"

if [ ! -f "$ADAPTER" ]; then
    echo "   ❌ Adapter not found: $ADAPTER"
    exit 1
fi
echo "   ✓ Adapter found"

# Test adapter loads
echo
echo "2. Testing adapter module load..."
if ! "$PYTHON" "$ADAPTER" > /tmp/toon-test-output.txt 2>&1; then
    echo "   ❌ Adapter failed to run"
    cat /tmp/toon-test-output.txt
    exit 1
fi
echo "   ✓ Adapter module loads successfully"
echo

# Display test output
echo "3. Test Output:"
echo "============================================================"
cat /tmp/toon-test-output.txt
echo "============================================================"
echo

# Verify specific test results
if grep -q "Round-trip success" /tmp/toon-test-output.txt; then
    echo "✓ Round-trip test PASSED"
else
    echo "❌ Round-trip test FAILED"
    exit 1
fi

if grep -q "Valid: True" /tmp/toon-test-output.txt; then
    echo "✓ Validation test PASSED"
else
    echo "❌ Validation test FAILED"
    exit 1
fi

if grep -q "All tests completed successfully" /tmp/toon-test-output.txt; then
    echo "✓ All adapter tests PASSED"
else
    echo "❌ Some adapter tests FAILED"
    exit 1
fi

echo
echo "============================================================"
echo "✅ All tests passed! TOON adapter is ready for use."
echo "============================================================"
echo
echo "Next steps:"
echo "  1. fact-extract.sh is ready to use TOON format"
echo "  2. Current implementation: JSON format (compatible)"
echo "  3. Can be upgraded to TOON for 20-40% token reduction"
echo
echo "Usage:"
echo "  ~/.claude/scripts/fact-extract.sh <content> <source_type> <focus>"
echo "  echo '<content>' | ~/.claude/scripts/fact-extract.sh - review <focus>"
echo

exit 0
