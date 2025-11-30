#!/bin/bash
#
# Krakenly - Kubernetes Deployment
# Deploys to Kubernetes cluster using official DockerHub images
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

# Parse arguments
SKIP_CONFIRM=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
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
            echo "Deploy Krakenly to a Kubernetes cluster using official DockerHub images."
            echo ""
            echo "Options:"
            echo "  -y, --yes       Skip confirmation prompts"
            echo "  -v, --verbose   Enable verbose output"
            echo "  -h, --help      Show this help message"
            echo ""
            echo "Prerequisites:"
            echo "  - kubectl configured with cluster access"
            echo "  - Kubernetes cluster running"
            echo ""
            echo "This script will:"
            echo "  1. Deploy all Krakenly components to the 'krakenly' namespace"
            echo "  2. Wait for pods to be ready"
            echo "  3. Offer to start port-forward for local access"
            echo ""
            echo "For local development with minikube, use: ./scripts/deploy-k8s-local.sh"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# Record start time (uses TZ env var if set, otherwise system timezone)
START_TIME=$(date +%s)
START_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')

echo "========================================="
echo "  Krakenly - Kubernetes Deployment"
echo "  (Using Official Images)"
echo "  https://github.com/krakenly/krakenly"
echo "========================================="
echo ""
log_info "Start time: $START_TIME_STR"

# Check for kubectl
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl not found. Please install kubectl first:"
    echo "  https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    log_error "Cannot connect to Kubernetes cluster."
    echo "  Please ensure your kubeconfig is properly configured."
    exit 1
fi

# Display cluster info
log_info "Connected to Kubernetes cluster:"
kubectl cluster-info | head -1
echo ""

# Confirm deployment
CONTEXT=$(kubectl config current-context)
log_warning "Deploying to context: $CONTEXT"
if [[ "$SKIP_CONFIRM" != true ]]; then
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled."
        exit 0
    fi
else
    log_info "Confirmation skipped (--yes flag provided)"
fi

echo ""

# Deploy using kustomize
log_info "Deploying Krakenly to Kubernetes..."
kubectl apply -k k8s/

echo ""

# Wait for pods to be ready
log_info "Waiting for pods to be ready (this may take a few minutes)..."
echo ""

wait_for_pod() {
    local label=$1
    local name=$2
    local timeout=${3:-300}
    
    if kubectl -n krakenly wait --for=condition=ready pod -l app.kubernetes.io/name=$label --timeout=${timeout}s 2>/dev/null; then
        echo -e "  ${name}:    ${GREEN}✓ ready${NC}"
        return 0
    else
        echo -e "  ${name}:    ${RED}✗ not ready${NC}"
        return 1
    fi
}

wait_for_pod "ollama" "Ollama" 300
wait_for_pod "chromadb" "ChromaDB" 120
wait_for_pod "krakenly" "Krakenly" 180

echo ""
log_info "Pod status:"
kubectl -n krakenly get pods

echo ""
log_info "Services:"
kubectl -n krakenly get svc

echo ""
log_success "Deployment complete!"
echo ""

log_info "Access options:"
echo ""
echo "  Option 1: Port Forward"
echo "    kubectl -n krakenly port-forward svc/krakenly 8080:80 5000:5000"
echo "    Then open: http://localhost:8080"
echo ""
echo "  Option 2: LoadBalancer (if supported)"
echo "    kubectl -n krakenly patch svc krakenly -p '{\"spec\": {\"type\": \"LoadBalancer\"}}'"
echo "    kubectl -n krakenly get svc krakenly -w"
echo ""
echo "  Option 3: Ingress"
echo "    Edit k8s/ingress.yaml with your domain"
echo "    Uncomment ingress in k8s/kustomization.yaml"
echo "    kubectl apply -k k8s/"
echo ""

log_info "Useful commands:"
echo "  - View logs:     kubectl -n krakenly logs -l app.kubernetes.io/name=krakenly -f"
echo "  - Pod status:    kubectl -n krakenly get pods"
echo "  - Delete:        kubectl delete -k k8s/"
echo "  - Health check:  kubectl -n krakenly exec -it deploy/krakenly -- curl localhost:5000/health"
echo ""

# Offer to start port-forward
if [[ "$SKIP_CONFIRM" != true ]]; then
    read -p "Start port-forward now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Starting port-forward... (Ctrl+C to stop)"
        echo ""
        echo -e "${GREEN}🐙 Open the Web UI: http://localhost:8080${NC}"
        echo ""
        kubectl -n krakenly port-forward svc/krakenly 8080:80 5000:5000
    fi
else
    log_info "Skipping port-forward prompt (--yes flag provided)"
    echo "  To access, run: kubectl -n krakenly port-forward svc/krakenly 8080:80 5000:5000"
fi

# Calculate and display duration
END_TIME=$(date +%s)
END_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

log_info "End time: $END_TIME_STR"
log_info "Total duration: ${MINUTES}m ${SECONDS}s"
