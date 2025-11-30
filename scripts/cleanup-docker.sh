#!/bin/bash
#
# Krakenly - Docker Compose Cleanup Script
# Removes containers, images, volumes, and cached data
# https://github.com/krakenly/krakenly
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Change to project directory
cd "$(dirname "$0")/.."

echo "========================================="
echo "  Krakenly - Docker Compose Cleanup"
echo "  https://github.com/krakenly/krakenly"
echo "========================================="
echo ""

# Parse arguments
FULL_CLEANUP=false
SKIP_CONFIRM=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --full|-f)
            FULL_CLEANUP=true
            shift
            ;;
        --yes|-y)
            SKIP_CONFIRM=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --full, -f    Full cleanup (remove all images, volumes, and cache)"
            echo "  --yes, -y     Skip confirmation prompt (for automation)"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Basic cleanup (containers and project resources)"
            echo "  $0 --full       # Full cleanup with confirmation prompt"
            echo "  $0 --full --yes # Full cleanup without confirmation (for CI/CD)"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

if [[ "$FULL_CLEANUP" == true ]]; then
    log_warn "Full cleanup requested - this will remove ALL Docker images and volumes!"
    echo ""
    if [[ "$SKIP_CONFIRM" != true ]]; then
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cleanup cancelled."
            exit 0
        fi
    else
        log_info "Confirmation skipped (--yes flag provided)"
    fi
fi

# Stop and remove containers
log_info "Stopping containers..."
docker-compose down -v 2>/dev/null || true
# Also force stop any containers with our names (in case docker-compose is out of sync)
docker stop ollama chromadb api web-manager 2>/dev/null || true
docker rm -f ollama chromadb api web-manager 2>/dev/null || true
log_success "Containers stopped and removed"

# Remove project-specific volumes (must be done after containers are removed)
log_info "Removing project volumes..."
docker volume rm -f krakenly-ollama 2>/dev/null || true
docker volume rm -f krakenly-chroma 2>/dev/null || true
docker volume rm -f krakenly-api 2>/dev/null || true
# Also remove volumes from manual docker run commands
docker volume rm -f ollama_data 2>/dev/null || true
docker volume rm -f ollama-data 2>/dev/null || true
docker volume rm -f chroma_data 2>/dev/null || true
docker volume rm -f chroma-data 2>/dev/null || true
log_success "Project volumes removed"

# Remove project-specific images
log_info "Removing project images..."
docker rmi krakenly-api 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=krakenly*") 2>/dev/null || true
log_success "Project images removed"

if [[ "$FULL_CLEANUP" == true ]]; then
    echo ""
    log_warn "Performing full cleanup..."
    
    # Remove Ollama and ChromaDB images
    log_info "Removing Ollama and ChromaDB images..."
    docker rmi ollama/ollama:latest 2>/dev/null || true
    docker rmi chromadb/chroma:latest 2>/dev/null || true
    
    # Prune everything
    log_info "Pruning unused Docker resources..."
    docker system prune -af --volumes
    
    log_success "Full cleanup complete"
else
    # Just remove dangling images
    log_info "Removing dangling images..."
    docker image prune -f 2>/dev/null || true
fi

echo ""
echo "========================================="
log_success "Cleanup complete!"
echo ""
echo "Removed:"
echo "  - All Krakenly containers"
echo "  - Project volumes (ollama-data, chroma-data)"
echo "  - Project images"
if [[ "$FULL_CLEANUP" == true ]]; then
    echo "  - Ollama and ChromaDB base images"
    echo "  - All unused Docker resources"
fi
echo ""
echo "To start fresh, run: ./scripts/start.sh"
echo "========================================="
