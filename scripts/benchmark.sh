#!/bin/bash
#
# Krakenly - Benchmark Script
# Runs performance benchmarks against the API
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
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments - extract verbose before passing to Python
VERBOSE=false
PASS_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            set -x
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Run performance benchmarks against the Krakenly API."
            echo ""
            echo "Options:"
            echo "  -v, --verbose      Enable verbose output"
            echo "  -h, --help         Show this help message"
            echo "  --api-url URL      API endpoint (default: http://localhost:5000)"
            echo "  --sample-file PATH Sample data file (default: tests/sample_data.md)"
            echo "  --output FILE      Output JSON file (default: benchmark_results.json)"
            echo "  --skip-upload      Skip uploading sample file"
            echo ""
            echo "This script will:"
            echo "  1. Install Python 'requests' library if needed"
            echo "  2. Upload sample data for benchmarking"
            echo "  3. Run queries of varying complexity"
            echo "  4. Generate performance report"
            echo ""
            echo "Prerequisites: Krakenly must be running (Docker or Kubernetes)"
            exit 0
            ;;
        *)
            PASS_ARGS+=("$1")
            shift
            ;;
    esac
done

cd "$(dirname "$0")"/..

# Record start time (uses TZ env var if set, otherwise system timezone)
START_TIME=$(date +%s)
START_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')

echo "========================================="
echo "  🐙 Krakenly - Benchmark"
echo "  https://github.com/krakenly/krakenly"
echo "========================================="
echo ""
log_info "Start time: $START_TIME_STR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed."
    echo "  Install with: sudo apt install python3 python3-pip"
    exit 1
fi

# Check/install requests library
log_info "Checking Python dependencies..."
if ! python3 -c "import requests" &> /dev/null; then
    log_warning "Installing 'requests' library..."
    pip3 install --user requests -q
    log_success "Installed 'requests'"
else
    log_success "Python dependencies OK"
fi

echo ""

# Check if API is accessible
log_info "Checking API availability..."
API_URL="${API_URL:-http://localhost:5000}"

if ! curl -s --connect-timeout 5 "$API_URL/health" > /dev/null; then
    log_error "Cannot connect to API at $API_URL"
    echo ""
    echo "  Make sure Krakenly is running:"
    echo "    Docker:     ./scripts/start-docker.sh"
    echo "    Kubernetes: kubectl -n krakenly port-forward svc/krakenly 5000:5000"
    echo ""
    exit 1
fi
log_success "API is accessible"

echo ""

# Run the benchmark
log_info "Starting benchmark..."
echo ""

python3 "$(dirname "$0")/benchmark.py" "${PASS_ARGS[@]}"

# Calculate and display duration
END_TIME=$(date +%s)
END_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
log_info "End time: $END_TIME_STR"
log_info "Total duration: ${MINUTES}m ${SECONDS}s"
