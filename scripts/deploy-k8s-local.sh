#!/bin/bash
#
# Krakenly - K8s Local Deployment
# Builds from source and deploys to local Minikube cluster
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
PUBLIC_ACCESS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --yes|-y)
            SKIP_CONFIRM=true
            shift
            ;;
        --public|-p)
            PUBLIC_ACCESS=true
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
            echo "Build Krakenly from source and deploy to local Minikube cluster."
            echo ""
            echo "Options:"
            echo "  -y, --yes       Skip confirmation prompts"
            echo "  -p, --public    Expose services on all interfaces (0.0.0.0)"
            echo "  -v, --verbose   Enable verbose output"
            echo "  -h, --help      Show this help message"
            echo ""
            echo "This script will:"
            echo "  1. Install Docker, kubectl, and minikube if not present"
            echo "  2. Start minikube cluster if not running"
            echo "  3. Build Krakenly image from local source"
            echo "  4. Deploy all components to minikube"
            echo "  5. Offer to start port-forward and run tests"
            echo ""
            echo "For production deployment, use: ./scripts/deploy-k8s.sh"
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
echo "  Krakenly - K8s Local Deployment"
echo "  (Build from Source + Minikube)"
echo "  https://github.com/krakenly/krakenly"
echo "========================================="
echo ""
log_info "Start time: $START_TIME_STR"

# Function to install kubectl
# Check and install Docker (via existing prereq script)
log_info "Checking Docker..."
if ! command -v docker &> /dev/null; then
    log_info "Docker not found. Installing prerequisites..."
    "$(dirname "$0")/install-docker-prereqs.sh"
fi

if ! docker info &> /dev/null; then
    log_error "Docker is not accessible. You may need to log out and back in for group permissions."
    exit 1
fi
log_success "Docker is ready"

# Check and install kubectl and minikube (via existing prereq script)
log_info "Checking kubectl..."
if ! command -v kubectl &> /dev/null; then
    log_info "kubectl not found. Installing k8s prerequisites..."
    "$(dirname "$0")/install-k8s-prereqs.sh"
else
    log_success "kubectl is installed"
fi

log_info "Checking minikube..."
if ! command -v minikube &> /dev/null; then
    log_info "minikube not found. Installing k8s prerequisites..."
    "$(dirname "$0")/install-k8s-prereqs.sh"
else
    log_success "minikube is installed"
fi

echo ""

# Check if minikube is running and healthy
start_minikube() {
    log_info "Starting minikube..."
    minikube start --memory=8192 --cpus=4
    log_success "Minikube started"
}

# Check minikube status - handle stale/broken state
if minikube status &> /dev/null; then
    # Verify the docker daemon is actually accessible
    if ! eval $(minikube docker-env) 2>/dev/null || ! docker info &> /dev/null; then
        log_warning "Minikube state is stale. Restarting..."
        minikube delete --purge 2>/dev/null || true
        start_minikube
    else
        log_success "Minikube is running"
    fi
else
    start_minikube
fi

# Enable required addons
log_info "Enabling minikube addons..."
minikube addons enable ingress 2>/dev/null || true
minikube addons enable storage-provisioner 2>/dev/null || true

# Point docker to minikube's docker daemon
log_info "Configuring Docker to use Minikube's daemon..."
eval $(minikube docker-env)

# Build the Krakenly image locally
log_info "Building Krakenly image from source..."
docker build -t krakenly/krakenly:local .

# Deploy base manifests first
log_info "Deploying base manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/ollama.yaml
kubectl apply -f k8s/chromadb.yaml

# Deploy krakenly with local image override
log_info "Deploying Krakenly with local image..."
cat k8s/krakenly.yaml | sed 's|krakenly/krakenly:latest|krakenly/krakenly:local|g' | sed 's|imagePullPolicy: IfNotPresent|imagePullPolicy: Never|g' | kubectl apply -f -

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
log_success "Deployment complete!"
echo ""

# Get access URL
MINIKUBE_IP=$(minikube ip)

log_info "Access options:"
echo ""
echo "  Option 1: Port Forward (recommended)"
echo "    kubectl -n krakenly port-forward svc/krakenly 8080:80 5000:5000"
echo "    Then open: http://localhost:8080"
echo ""
echo "  Option 2: Minikube Service"
echo "    minikube -n krakenly service krakenly --url"
echo ""
echo "  Option 3: Minikube Tunnel (for LoadBalancer)"
echo "    minikube tunnel"
echo ""

log_info "Useful commands:"
echo "  - View logs:     kubectl -n krakenly logs -l app.kubernetes.io/name=krakenly -f"
echo "  - Pod status:    kubectl -n krakenly get pods"
echo "  - Delete:        kubectl delete -k k8s/"
echo ""

# Offer to start port-forward and run tests
if [[ "$SKIP_CONFIRM" != true ]]; then
    read -p "Start port-forward and run tests? (y/n) " -n 1 -r
    echo ""
else
    REPLY="y"
    log_info "Auto-starting port-forward and tests (--yes flag provided)"
fi

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Starting port-forward in background..."
    if [[ "$PUBLIC_ACCESS" = true ]]; then
        log_warning "Exposing services on all interfaces (0.0.0.0)"
        kubectl -n krakenly port-forward --address 0.0.0.0 svc/krakenly 8080:80 5000:5000 &
    else
        kubectl -n krakenly port-forward svc/krakenly 8080:80 5000:5000 &
    fi
    PORT_FORWARD_PID=$!
    
    # Wait for port-forward to be ready
    sleep 3
    
    # Pull the model if needed (this can take a few minutes for first run)
    log_info "Ensuring LLM model is available (this may take a few minutes on first run)..."
    OLLAMA_POD=$(kubectl -n krakenly get pod -l app.kubernetes.io/name=ollama -o jsonpath='{.items[0].metadata.name}')
    kubectl -n krakenly exec "$OLLAMA_POD" -- ollama pull qwen2.5:3b
    log_success "LLM model is ready"
    
    echo ""
    log_info "Running tests..."
    echo ""
    "$(dirname "$0")/test.sh"
    
    echo ""
    echo -e "${GREEN}Open the Web UI:${NC}"
    echo -e "  Local:  http://localhost:8080"
    if [[ "$PUBLIC_ACCESS" = true ]]; then
        PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
        echo -e "  Public: http://${PUBLIC_IP}:8080"
    fi
    echo ""
    log_info "Port-forward running in background (PID: $PORT_FORWARD_PID)"
    log_info "To stop: kill $PORT_FORWARD_PID"
fi

# Calculate and display duration
END_TIME=$(date +%s)
END_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

log_info "End time: $END_TIME_STR"
log_info "Total duration: ${MINUTES}m ${SECONDS}s"
