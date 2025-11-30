#!/bin/bash
#
# Krakenly - Kubernetes Prerequisites Installer
# Installs kubectl and minikube for local Kubernetes development
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

# Show help
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Install Kubernetes prerequisites for local Krakenly development."
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "This script will install:"
    echo "  - Docker (via install-docker-prereqs.sh)"
    echo "  - kubectl (Kubernetes CLI)"
    echo "  - minikube (local Kubernetes cluster)"
    echo ""
    echo "After installation, run: ./scripts/deploy-k8s-local.sh"
    exit 0
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    log_error "Please do not run this script as root/sudo. It will prompt for sudo when needed."
    exit 1
fi

echo "========================================="
echo "  Krakenly - K8s Prereqs Installer"
echo "  https://github.com/krakenly/krakenly"
echo "========================================="
echo ""

# Check system
log_info "Checking system requirements..."
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
CPU_CORES=$(nproc)

log_info "System specs:"
echo "  - RAM: ${TOTAL_MEM}GB"
echo "  - CPU Cores: ${CPU_CORES}"
echo ""

if [ "$TOTAL_MEM" -lt 8 ]; then
    log_warning "Less than 8GB RAM detected. Minikube may run slowly."
fi

# Install Docker first (required for minikube)
log_info "Checking Docker..."
if ! command -v docker &> /dev/null; then
    log_info "Docker not found. Installing..."
    "$(dirname "$0")/install-docker-prereqs.sh"
else
    log_success "Docker is installed"
fi

# Install kubectl
log_info "Checking kubectl..."
if command -v kubectl &> /dev/null; then
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null | head -1 || kubectl version --client 2>/dev/null | head -1)
    log_success "kubectl is installed: $KUBECTL_VERSION"
else
    log_info "Installing kubectl..."
    
    # Download kubectl
    KUBECTL_STABLE=$(curl -L -s https://dl.k8s.io/release/stable.txt)
    curl -LO "https://dl.k8s.io/release/${KUBECTL_STABLE}/bin/linux/amd64/kubectl"
    
    # Verify checksum
    curl -LO "https://dl.k8s.io/release/${KUBECTL_STABLE}/bin/linux/amd64/kubectl.sha256"
    if echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check --status 2>/dev/null; then
        log_success "kubectl checksum verified"
    else
        log_warning "kubectl checksum verification skipped"
    fi
    rm -f kubectl.sha256
    
    # Install
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/
    log_success "kubectl installed: $KUBECTL_STABLE"
fi

# Install minikube
log_info "Checking minikube..."
if command -v minikube &> /dev/null; then
    MINIKUBE_VERSION=$(minikube version --short 2>/dev/null || minikube version | head -1)
    log_success "minikube is installed: $MINIKUBE_VERSION"
else
    log_info "Installing minikube..."
    
    # Download minikube
    curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
    
    # Install
    chmod +x minikube-linux-amd64
    sudo mv minikube-linux-amd64 /usr/local/bin/minikube
    log_success "minikube installed"
fi

# Verify installations
echo ""
echo "========================================="
echo "  Verification Summary"
echo "========================================="
echo ""

ALL_OK=true

check_and_report() {
    local cmd=$1
    local name=$2
    if command -v $cmd &> /dev/null; then
        echo -e "${GREEN}✓${NC} $name is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $name is NOT installed"
        return 1
    fi
}

check_and_report docker "Docker" || ALL_OK=false
check_and_report kubectl "kubectl" || ALL_OK=false
check_and_report minikube "minikube" || ALL_OK=false

echo ""
if [ "$ALL_OK" = true ]; then
    log_success "All K8s prerequisites are installed!"
    echo ""
    log_info "Next steps:"
    echo "  1. Start minikube:     minikube start"
    echo "  2. Deploy Krakenly:    ./scripts/deploy-k8s-local.sh"
    echo ""
    log_info "Or deploy directly (starts minikube automatically):"
    echo "  ./scripts/deploy-k8s-local.sh"
    echo ""
else
    log_error "Some prerequisites are missing. Please check the errors above."
    exit 1
fi

echo "========================================="
