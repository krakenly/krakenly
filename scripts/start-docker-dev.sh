#!/bin/bash
#
# Krakenly - Docker Compose Development Script
# Installs prerequisites, builds from source, and starts all services
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

cd "$(dirname "$0")"/..

# Show help
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Start Krakenly using Docker Compose, building from local source code."
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "This script will:"
    echo "  1. Install Docker and Docker Compose if not present"
    echo "  2. Build Docker images from local source"
    echo "  3. Start all services (Ollama, ChromaDB, Krakenly)"
    echo "  4. Wait for health checks to pass"
    echo "  5. Run end-to-end tests"
    echo ""
    echo "Use this script for development when you want to test local changes."
    echo "For production, use: ./scripts/start-docker.sh"
    exit 0
fi

# Record start time
START_TIME=$(date +%s)
START_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')

echo "========================================="
echo "  Krakenly - Docker Compose Dev"
echo "  (Build from Source)"
echo "  https://github.com/krakenly/krakenly"
echo "========================================="
echo ""
log_info "Start time: $START_TIME_STR"

# Install prerequisites
log_info "Checking prerequisites..."
"$(dirname "$0")/install-docker-prereqs.sh"
echo ""

# Verify docker is accessible
if ! docker info &> /dev/null; then
    log_error "Docker is not accessible. You may need to log out and back in for group permissions."
    exit 1
fi

# Build and start services
log_info "Building and starting services from local source..."
docker-compose -f docker-compose.dev.yml up -d --build

echo ""
log_info "Waiting for services to become healthy..."

wait_for_health() {
    local name=$1
    local url=$2
    local max_attempts=${3:-30}
    
    for i in $(seq 1 $max_attempts); do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "  ${name}:    ${GREEN}✓ healthy${NC}"
            return 0
        fi
        sleep 2
    done
    echo -e "  ${name}:    ${RED}✗ not ready${NC}"
    return 1
}

wait_for_health "ollama" "http://localhost:11434/api/tags" 30
wait_for_health "chromadb" "http://localhost:8000/api/v2/heartbeat" 30
wait_for_health "krakenly API" "http://localhost:5000/health" 90
wait_for_health "krakenly Web UI" "http://localhost:8080/health" 90

echo ""
log_info "Container status:"
docker-compose -f docker-compose.dev.yml ps

echo ""
log_success "All services are running!"
echo ""
log_info "Service endpoints:"
echo "  - Web UI:   http://localhost:8080"
echo "  - API:      http://localhost:5000"
echo "  - Ollama:   http://localhost:11434"
echo "  - ChromaDB: http://localhost:8000"
echo ""
log_info "Quick test:"
echo "  curl -X POST http://localhost:5000/generate \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"prompt\": \"Hello!\"}'"
echo ""
log_info "Useful commands:"
echo "  - View logs:     docker-compose -f docker-compose.dev.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.dev.yml down"
echo "  - Restart:       docker-compose -f docker-compose.dev.yml restart"
echo ""

# Calculate and display duration
END_TIME=$(date +%s)
END_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

log_info "End time: $END_TIME_STR"
log_info "Total duration: ${MINUTES}m ${SECONDS}s"
echo "========================================="

# Run tests
echo ""
log_info "Running tests..."
if "$(dirname "$0")/test.sh"; then
    echo ""
    echo "========================================="
    echo -e "${GREEN}🐙 Congratulations! Krakenly is ready!${NC}"
    echo "========================================="
    echo ""
    echo "Krakenly is now running and fully tested."
    echo ""
    echo -e "${GREEN}Open the Web UI: http://localhost:8080${NC}"
    echo ""
    echo "Other endpoints:"
    echo "  - API:      http://localhost:5000"
    echo "  - Ollama:   http://localhost:11434"
    echo "  - ChromaDB: http://localhost:8000"
    echo ""
    echo "For full API documentation, see README.md"
    echo "========================================="
fi
