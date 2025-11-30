#!/bin/bash
#
# Krakenly - Docker Prerequisites Installer
# Installs Docker and Docker Compose
# https://github.com/krakenly/krakenly
#
set -e

# Show help
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Install Docker and Docker Compose prerequisites for Krakenly."
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo ""
    echo "This script will:"
    echo "  1. Check system requirements (RAM, CPU, disk space)"
    echo "  2. Install Docker if not present"
    echo "  3. Install Docker Compose if not present"
    echo "  4. Add current user to docker group"
    echo ""
    echo "Note: You may need to log out and back in after installation"
    echo "for docker group permissions to take effect."
    exit 0
fi

# Enable verbose mode if -v or --verbose flag is passed
VERBOSE=false
if [[ "$1" == "-v" ]] || [[ "$1" == "--verbose" ]]; then
    VERBOSE=true
    set -x
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    log_error "Please do not run this script as root/sudo. It will prompt for sudo when needed."
    exit 1
fi

# Record start time (local timezone)
START_TIME=$(date +%s)
START_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')

echo "========================================="
echo "  Krakenly - Docker Prereqs Installer"
echo "  https://github.com/krakenly/krakenly"
echo "========================================="
echo ""
log_info "Start time: $START_TIME_STR"

# Check system
log_info "Checking system requirements..."
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
CPU_CORES=$(nproc)
DISK_FREE=$(df -BG /home | tail -1 | awk '{print $4}' | sed 's/G//')

log_info "System specs:"
echo "  - RAM: ${TOTAL_MEM}GB"
echo "  - CPU Cores: ${CPU_CORES}"
echo "  - Free Disk Space: ${DISK_FREE}GB"
echo ""

if [ "$TOTAL_MEM" -lt 8 ]; then
    log_warning "Less than 8GB RAM detected. Krakenly may run slowly."
fi

if [ "$DISK_FREE" -lt 30 ]; then
    log_warning "Less than 30GB free disk space. You may need more space for models."
fi

# 1. Install Docker
log_info "Checking Docker installation..."
if command_exists docker; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    log_success "Docker $DOCKER_VERSION is already installed"
    
    # Check if user is in docker group
    if groups $USER | grep -q '\bdocker\b'; then
        log_success "User is in docker group"
    else
        log_warning "Adding user to docker group..."
        sudo usermod -aG docker $USER
        log_warning "You'll need to log out and back in for docker group to take effect"
    fi
else
    log_info "Installing Docker..."
    sudo apt update -qq
    DEBIAN_FRONTEND=noninteractive sudo apt install -y -qq docker.io
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    log_success "Docker installed"
    log_warning "You'll need to log out and back in for docker group to take effect"
fi

# Verify docker is running
if sudo systemctl is-active --quiet docker; then
    log_success "Docker service is running"
else
    log_info "Starting Docker service..."
    sudo systemctl start docker
    log_success "Docker service started"
fi

# 2. Install Docker Compose
log_info "Checking Docker Compose installation..."
if command_exists docker-compose; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//' 2>/dev/null || docker-compose version --short 2>/dev/null || echo "installed")
    log_success "Docker Compose $COMPOSE_VERSION is already installed"
else
    log_info "Installing Docker Compose..."
    sudo apt update -qq
    DEBIAN_FRONTEND=noninteractive sudo apt install -y -qq docker-compose
    log_success "Docker Compose installed"
fi

# 3. Install Docker BuildKit/buildx plugin (optional but useful)
log_info "Checking Docker buildx plugin..."
if docker buildx version >/dev/null 2>&1; then
    log_success "Docker buildx plugin is already installed"
else
    log_info "Installing Docker buildx plugin..."
    sudo apt update -qq
    DEBIAN_FRONTEND=noninteractive sudo apt install -y -qq docker-buildx 2>/dev/null || log_warning "Docker buildx not available, skipping (optional)"
fi

# 4. Verify installations
echo ""
echo "========================================="
echo "  Verification Summary"
echo "========================================="
echo ""

check_and_report() {
    local cmd=$1
    local name=$2
    if command_exists $cmd; then
        echo -e "${GREEN}✓${NC} $name is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $name is NOT installed"
        return 1
    fi
}

ALL_OK=true

check_and_report docker "Docker" || ALL_OK=false
check_and_report docker-compose "Docker Compose" || ALL_OK=false

echo ""
if [ "$ALL_OK" = true ]; then
    log_success "All prerequisites are installed!"
    echo ""
    log_info "Next steps:"
    echo "  1. If this is your first Docker installation, log out and back in"
    echo "  2. Run: docker-compose up -d"
    echo "  3. Check status: docker-compose ps"
    echo "  4. View logs: docker-compose logs -f"
    echo ""
    log_info "Service endpoint (after startup):"
    echo "  - API Service: http://localhost:5000"
    echo ""
else
    log_error "Some prerequisites are missing. Please check the errors above."
    exit 1
fi

# Calculate and display duration
END_TIME=$(date +%s)
END_TIME_STR=$(date '+%Y-%m-%d %H:%M:%S %Z')
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

log_info "End time: $END_TIME_STR"
log_info "Total duration: ${MINUTES}m ${SECONDS}s"
echo "========================================="
