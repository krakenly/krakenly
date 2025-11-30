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

echo "========================================="
echo "  Krakenly - K8s Local Deployment"
echo "  (Build from Source + Minikube)"
echo "  https://github.com/krakenly/krakenly"
echo "========================================="
echo ""

# Function to install kubectl
install_kubectl() {
    log_info "Installing kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/
    log_success "kubectl installed"
}

# Function to install minikube
install_minikube() {
    log_info "Installing minikube..."
    curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
    chmod +x minikube-linux-amd64
    sudo mv minikube-linux-amd64 /usr/local/bin/minikube
    log_success "minikube installed"
}

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

# Check and install kubectl
log_info "Checking kubectl..."
if ! command -v kubectl &> /dev/null; then
    install_kubectl
else
    log_success "kubectl is installed"
fi

# Check and install minikube
log_info "Checking minikube..."
if ! command -v minikube &> /dev/null; then
    install_minikube
else
    log_success "minikube is installed"
fi

echo ""

# Check if minikube is running
if ! minikube status &> /dev/null; then
    log_info "Starting minikube..."
    minikube start --memory=8192 --cpus=4
    log_success "Minikube started"
else
    log_success "Minikube is running"
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

# Create a temporary kustomization overlay for local image
log_info "Creating local deployment configuration..."
TEMP_DIR=$(mktemp -d)
cat > "$TEMP_DIR/kustomization.yaml" << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../k8s/namespace.yaml
  - ../k8s/pvc.yaml
  - ../k8s/ollama.yaml
  - ../k8s/chromadb.yaml
  - ../k8s/krakenly.yaml

namespace: krakenly

patches:
  - patch: |-
      - op: replace
        path: /spec/template/spec/containers/0/image
        value: krakenly/krakenly:local
      - op: replace
        path: /spec/template/spec/containers/0/imagePullPolicy
        value: Never
    target:
      kind: Deployment
      name: krakenly
EOF

# Deploy to minikube
log_info "Deploying to Minikube..."
kubectl apply -k "$TEMP_DIR"

# Cleanup temp dir
rm -rf "$TEMP_DIR"

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
read -p "Start port-forward and run tests? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Starting port-forward in background..."
    kubectl -n krakenly port-forward svc/krakenly 8080:80 5000:5000 &
    PORT_FORWARD_PID=$!
    
    # Wait for port-forward to be ready
    sleep 3
    
    # Pull the model if needed
    log_info "Ensuring LLM model is available..."
    OLLAMA_POD=$(kubectl -n krakenly get pod -l app.kubernetes.io/name=ollama -o jsonpath='{.items[0].metadata.name}')
    kubectl -n krakenly exec "$OLLAMA_POD" -- ollama pull qwen2.5:3b 2>/dev/null || true
    
    echo ""
    log_info "Running tests..."
    echo ""
    "$(dirname "$0")/test.sh"
    
    echo ""
    echo -e "${GREEN}Open the Web UI: http://localhost:8080${NC}"
    echo ""
    log_info "Port-forward running in background (PID: $PORT_FORWARD_PID)"
    log_info "To stop: kill $PORT_FORWARD_PID"
fi
