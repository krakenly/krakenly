#!/bin/bash
#
# Krakenly - Docker Compose Cleanup Script
# Removes containers, images, and optionally volumes/data
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
DELETE_DATA=false
DELETE_IMAGES=false
SKIP_CONFIRM=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --data|-d)
            DELETE_DATA=true
            shift
            ;;
        --images|-i)
            DELETE_IMAGES=true
            shift
            ;;
        --all|-a)
            DELETE_DATA=true
            DELETE_IMAGES=true
            shift
            ;;
        --yes|-y)
            SKIP_CONFIRM=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            set -x
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --data, -d    Also delete volumes (your indexed data and models)"
            echo "  --images, -i  Also delete base images (Ollama, ChromaDB)"
            echo "  --all, -a     Delete everything (data + images + prune)"
            echo "  --yes, -y     Skip confirmation prompt (for automation)"
            echo "  --verbose, -v Enable verbose output"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Stop containers, keep data"
            echo "  $0 --data       # Stop containers and delete data"
            echo "  $0 --all        # Full cleanup with confirmation"
            echo "  $0 --all --yes  # Full cleanup without confirmation (for CI/CD)"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# Record start time (uses TZ env var if set, otherwise system timezone)
START_TIME=$(date +%s)
START_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')
log_info "Start time: $START_TIME_STR"
echo ""

# Confirmation for destructive operations
if [[ "$DELETE_DATA" == true ]] || [[ "$DELETE_IMAGES" == true ]]; then
    if [[ "$DELETE_DATA" == true ]] && [[ "$DELETE_IMAGES" == true ]]; then
        log_warn "Full cleanup requested - this will remove ALL data and images!"
    elif [[ "$DELETE_DATA" == true ]]; then
        log_warn "Data cleanup requested - this will remove your indexed data and models!"
    else
        log_warn "Image cleanup requested - this will remove base Docker images!"
    fi
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

# Stop and remove containers (always done)
log_info "Stopping containers..."
docker-compose down 2>/dev/null || true
# Also force stop any containers with our names (in case docker-compose is out of sync)
docker stop ollama chromadb api web-manager 2>/dev/null || true
docker rm -f ollama chromadb api web-manager 2>/dev/null || true
log_success "Containers stopped and removed"

# Remove project-specific images (always done - these are small/rebuildable)
log_info "Removing Krakenly images..."
docker rmi krakenly-api 2>/dev/null || true
docker rmi krakenly/krakenly 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=krakenly*") 2>/dev/null || true
log_success "Krakenly images removed"

# Remove volumes only if --data or --all
if [[ "$DELETE_DATA" == true ]]; then
    echo ""
    log_warn "Deleting data volumes..."
    
    # Remove project-specific volumes
    docker volume rm -f krakenly-ollama 2>/dev/null || true
    docker volume rm -f krakenly-chroma 2>/dev/null || true
    docker volume rm -f krakenly-api 2>/dev/null || true
    # Also remove volumes from manual docker run commands
    docker volume rm -f ollama_data 2>/dev/null || true
    docker volume rm -f ollama-data 2>/dev/null || true
    docker volume rm -f chroma_data 2>/dev/null || true
    docker volume rm -f chroma-data 2>/dev/null || true
    
    log_success "Data volumes removed"
fi

# Remove base images only if --images or --all
if [[ "$DELETE_IMAGES" == true ]]; then
    echo ""
    log_warn "Deleting base images..."
    
    # Remove Ollama and ChromaDB images
    docker rmi ollama/ollama:latest 2>/dev/null || true
    docker rmi chromadb/chroma:latest 2>/dev/null || true
    
    # Prune everything
    log_info "Pruning unused Docker resources..."
    docker system prune -af --volumes
    
    log_success "Base images removed"
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
echo "  - Krakenly project images"
if [[ "$DELETE_DATA" == true ]]; then
    echo "  - Data volumes (ollama-data, chroma-data)"
fi
if [[ "$DELETE_IMAGES" == true ]]; then
    echo "  - Base images (Ollama, ChromaDB)"
    echo "  - All unused Docker resources"
fi
echo ""
if [[ "$DELETE_DATA" == false ]]; then
    log_info "Note: Data volumes were preserved."
    echo "  To also delete data, run: $0 --data"
fi
echo ""
echo "To start fresh, run: ./scripts/start-docker.sh"

# Calculate and display duration
END_TIME=$(date +%s)
END_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

log_info "End time: $END_TIME_STR"
log_info "Total duration: ${MINUTES}m ${SECONDS}s"
echo "========================================="
