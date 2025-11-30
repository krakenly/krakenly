#!/bin/bash
#
# Krakenly - Kubernetes Cleanup
# Removes Krakenly deployment from Kubernetes cluster
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

# Record start time (uses TZ env var if set, otherwise system timezone)
START_TIME=$(date +%s)
START_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')

echo "========================================="
echo "  Krakenly - K8s Cleanup"
echo "  https://github.com/krakenly/krakenly"
echo "========================================="
echo ""
log_info "Start time: $START_TIME_STR"

# Parse arguments
DELETE_DATA=false
DELETE_MINIKUBE=false
SKIP_CONFIRM=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --data|-d)
            DELETE_DATA=true
            shift
            ;;
        --minikube|-m)
            DELETE_MINIKUBE=true
            shift
            ;;
        --all|-a)
            DELETE_DATA=true
            DELETE_MINIKUBE=true
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
            echo "  --data, -d      Also delete persistent volume claims (your indexed data)"
            echo "  --minikube, -m  Also delete the minikube cluster (local only)"
            echo "  --all, -a       Delete everything (data + minikube)"
            echo "  --yes, -y       Skip confirmation prompt"
            echo "  --verbose, -v   Enable verbose output"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Remove deployments, keep data"
            echo "  $0 --data       # Remove deployments and data"
            echo "  $0 --minikube   # Remove deployments and minikube cluster"
            echo "  $0 --all        # Remove everything"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check for kubectl
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl not found."
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace krakenly &> /dev/null; then
    log_warning "Krakenly namespace not found. Nothing to clean up."
    exit 0
fi

# Show what will be deleted
log_info "This will delete:"
echo "  - Krakenly deployments and services"
echo "  - ConfigMaps and secrets in krakenly namespace"
if [ "$DELETE_DATA" = true ]; then
    echo -e "  - ${RED}Persistent Volume Claims (your indexed data!)${NC}"
fi
if [ "$DELETE_MINIKUBE" = true ]; then
    echo -e "  - ${RED}Entire minikube cluster${NC}"
fi
echo ""

# Confirm
if [[ "$SKIP_CONFIRM" != true ]]; then
    read -p "Are you sure? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleanup cancelled."
        exit 0
    fi
else
    log_info "Confirmation skipped (--yes flag provided)"
fi

echo ""

# Delete deployments and services (but keep PVCs by default)
log_info "Removing Krakenly deployments..."
kubectl delete deployment -n krakenly --all 2>/dev/null || true
kubectl delete service -n krakenly --all 2>/dev/null || true
kubectl delete ingress -n krakenly --all 2>/dev/null || true

# Delete PVCs if requested
if [ "$DELETE_DATA" = true ]; then
    log_warning "Deleting persistent volume claims..."
    kubectl delete pvc -n krakenly --all 2>/dev/null || true
fi

# Delete namespace
log_info "Removing krakenly namespace..."
kubectl delete namespace krakenly 2>/dev/null || true

log_success "Krakenly removed from Kubernetes"

# Delete minikube if requested
if [ "$DELETE_MINIKUBE" = true ]; then
    if command -v minikube &> /dev/null; then
        echo ""
        log_warning "Deleting minikube cluster..."
        minikube delete 2>/dev/null || true
        log_success "Minikube cluster deleted"
    else
        log_warning "minikube not found, skipping"
    fi
fi

# Prune unused Docker images
if command -v docker &> /dev/null && docker info &> /dev/null; then
    log_info "Pruning unused Docker images..."
    docker image prune -f 2>/dev/null || true
    log_success "Unused Docker images removed"
fi

echo ""
log_success "Cleanup complete!"

# Calculate and display duration
END_TIME=$(date +%s)
END_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

log_info "End time: $END_TIME_STR"
log_info "Total duration: ${MINUTES}m ${SECONDS}s"
echo ""

if [ "$DELETE_DATA" = false ]; then
    log_info "Note: Persistent data was preserved."
    echo "  To also delete data, run: $0 --data"
fi
