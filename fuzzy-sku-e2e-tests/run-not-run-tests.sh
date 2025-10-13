#!/bin/bash

# Script to rerun only the NOT_RUN test cases

echo "🔍 Finding NOT_RUN test cases..."

# Extract test numbers from CSV where status is NOT_RUN (excluding header line)
NOT_RUN_TESTS=$(awk -F',' 'NR>1 && $2=="NOT_RUN" {print $1}' fuzzy-sku-test-results.csv | tr '\n' '|' | sed 's/|$//')

if [ -z "$NOT_RUN_TESTS" ]; then
    echo "✅ No NOT_RUN test cases found! All tests have been executed."
    exit 0
fi

# Count the number of NOT_RUN tests
NOT_RUN_COUNT=$(echo "$NOT_RUN_TESTS" | tr '|' '\n' | wc -l)

echo "📊 Found $NOT_RUN_COUNT NOT_RUN test case(s)"
echo "🔢 Test numbers: $(echo $NOT_RUN_TESTS | tr '|' ', ')"
echo ""

# Build grep pattern for test names (TC001, TC002, etc.)
GREP_PATTERN=""
for num in $(echo "$NOT_RUN_TESTS" | tr '|' ' '); do
    # Pad the number to 3 digits (TC001, TC002, etc.)
    PADDED=$(printf "TC%03d" $num)
    if [ -z "$GREP_PATTERN" ]; then
        GREP_PATTERN="$PADDED"
    else
        GREP_PATTERN="$GREP_PATTERN|$PADDED"
    fi
done

echo "🎯 Running tests matching pattern: $GREP_PATTERN"
echo ""
echo "▶️  Starting Playwright tests..."
echo ""

# Run Playwright with grep pattern
pnpm playwright test fuzzy-sku-search.spec.ts --grep "$GREP_PATTERN"

echo ""
echo "✨ Test execution completed!"
echo "📄 Check fuzzy-sku-test-results.csv for updated results"
