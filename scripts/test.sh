#!/bin/bash
#
# Krakenly - Test Script
# Runs end-to-end tests for all services
# https://github.com/krakenly/krakenly
#
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

API_URL="http://localhost:5000"
TESTS_PASSED=true

# Track individual test results
declare -A TEST_RESULTS
TEST_ORDER=("Health Check" "Indexing" "Search" "RAG Query" "Generation")

check_result() {
    local result="$1"
    local test_name="$2"
    
    # Check for error in response (key or value containing error/Error)
    if echo "$result" | grep -qiE '"error"|"response":\s*"Error'; then
        log_error "$test_name failed!"
        TEST_RESULTS["$test_name"]="failed"
        TESTS_PASSED=false
        return 1
    fi
    log_success "$test_name passed!"
    TEST_RESULTS["$test_name"]="passed"
    return 0
}

echo "========================================="
echo "  Krakenly - End-to-End Test"
echo "========================================="
echo ""

# Step 1: Health check
log_info "Checking service health..."
HEALTH=$(curl -s "$API_URL/health")
echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"

# Check if model is loaded
if echo "$HEALTH" | grep -q '"model_loaded": false'; then
    log_error "Model not loaded! Run: docker exec ollama ollama pull qwen2.5:3b"
    TEST_RESULTS["Health Check"]="failed"
    TESTS_PASSED=false
else
    TEST_RESULTS["Health Check"]="passed"
fi
echo ""

# Step 2: Index sample document
echo "========================================="
log_info "Indexing sample document..."
echo "========================================="

SAMPLE_TEXT="Krakenly is a microservices application with three components: Ollama for LLM inference on port 11434, ChromaDB for vector storage on port 8000, and a unified API service on port 5000. It supports document indexing, semantic search, and RAG-based question answering."

INDEX_RESULT=$(curl -s -X POST "$API_URL/index" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$SAMPLE_TEXT\", \"metadata\": {\"source\": \"test-doc.md\"}}")

echo "$INDEX_RESULT" | python3 -m json.tool 2>/dev/null || echo "$INDEX_RESULT"
check_result "$INDEX_RESULT" "Indexing"
echo ""

# Step 3: Search
echo "========================================="
log_info "Testing semantic search..."
echo "========================================="

SEARCH_RESULT=$(curl -s -X POST "$API_URL/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What port does ChromaDB run on?", "top_k": 3}')

echo "$SEARCH_RESULT" | python3 -m json.tool 2>/dev/null || echo "$SEARCH_RESULT"
check_result "$SEARCH_RESULT" "Search"
echo ""

# Step 4: RAG Query
echo "========================================="
log_info "Testing RAG query (search + AI)..."
echo "========================================="

RAG_RESULT=$(curl -s -X POST "$API_URL/search/rag" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the three components of Krakenly?", "top_k": 3, "max_tokens": 150}')

echo "$RAG_RESULT" | python3 -m json.tool 2>/dev/null || echo "$RAG_RESULT"
check_result "$RAG_RESULT" "RAG Query"
echo ""

# Step 5: Direct generation
echo "========================================="
log_info "Testing direct AI generation..."
echo "========================================="

GEN_RESULT=$(curl -s -X POST "$API_URL/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Docker? Answer in one sentence.", "max_tokens": 50}')

echo "$GEN_RESULT" | python3 -m json.tool 2>/dev/null || echo "$GEN_RESULT"
check_result "$GEN_RESULT" "Generation"
echo ""

echo "========================================="
if [ "$TESTS_PASSED" = true ]; then
    log_success "All tests passed!"
else
    log_error "Some tests failed!"
fi
echo "========================================="
echo ""

# Print test summary
echo "========================================="
echo "           TEST SUMMARY"
echo "========================================="
for test_name in "${TEST_ORDER[@]}"; do
    status="${TEST_RESULTS[$test_name]}"
    if [ "$status" = "passed" ]; then
        echo -e "  ${GREEN}☑${NC} $test_name"
    elif [ "$status" = "failed" ]; then
        echo -e "  ${RED}☒${NC} $test_name"
    else
        echo -e "  ${YELLOW}☐${NC} $test_name (skipped)"
    fi
done
echo "========================================="

# Count results
PASSED=0
FAILED=0
for test_name in "${TEST_ORDER[@]}"; do
    status="${TEST_RESULTS[$test_name]}"
    if [ "$status" = "passed" ]; then
        PASSED=$((PASSED + 1))
    elif [ "$status" = "failed" ]; then
        FAILED=$((FAILED + 1))
    fi
done

TOTAL=${#TEST_ORDER[@]}
echo ""
if [ "$TESTS_PASSED" = true ]; then
    echo -e "${GREEN}Results: $PASSED/$TOTAL tests passed${NC}"
else
    echo -e "${RED}Results: $PASSED/$TOTAL tests passed, $FAILED failed${NC}"
    exit 1
fi
