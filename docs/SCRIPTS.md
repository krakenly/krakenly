# Scripts Reference

This document provides detailed documentation for all scripts in the `scripts/` directory.

## Table of Contents

- [Overview](#overview)
- [Common Options](#common-options)
- [Startup Scripts](#startup-scripts)
  - [start-docker.sh](#start-dockersh)
  - [start-docker-dev.sh](#start-docker-devsh)
  - [deploy-k8s.sh](#deploy-k8ssh)
  - [deploy-k8s-local.sh](#deploy-k8s-localsh)
- [Cleanup Scripts](#cleanup-scripts)
  - [cleanup-docker.sh](#cleanup-dockersh)
  - [cleanup-k8s.sh](#cleanup-k8ssh)
- [Prerequisites Scripts](#prerequisites-scripts)
  - [install-docker-prereqs.sh](#install-docker-prereqssh)
  - [install-k8s-prereqs.sh](#install-k8s-prereqssh)
- [Testing & Benchmarking](#testing--benchmarking)
  - [test.sh](#testsh)
  - [benchmark.sh](#benchmarksh)
- [Common Workflows](#common-workflows)

---

## Overview

All scripts support common options for help, verbose output, and (where applicable) skipping confirmations. Scripts are organized by function:

| Script | Purpose | Platform |
|--------|---------|----------|
| `start-docker.sh` | Start production Docker Compose | Docker |
| `start-docker-dev.sh` | Start development Docker Compose | Docker |
| `deploy-k8s.sh` | Deploy to Kubernetes cluster | Kubernetes |
| `deploy-k8s-local.sh` | Deploy to local minikube | Kubernetes |
| `cleanup-docker.sh` | Clean up Docker resources | Docker |
| `cleanup-k8s.sh` | Clean up Kubernetes resources | Kubernetes |
| `install-docker-prereqs.sh` | Install Docker prerequisites | Docker |
| `install-k8s-prereqs.sh` | Install Kubernetes prerequisites | Kubernetes |
| `test.sh` | Run API tests | Both |
| `benchmark.sh` | Run performance benchmarks | Both |

---

## Common Options

All scripts support these options:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message and exit |
| `--verbose`, `-v` | Enable verbose output (shows commands being executed) |

Scripts with destructive operations also support:

| Option | Description |
|--------|-------------|
| `--yes`, `-y` | Skip confirmation prompts |

---

## Startup Scripts

### start-docker.sh

Start Krakenly using Docker Compose with pre-built images from DockerHub.

**Usage:**
```bash
./scripts/start-docker.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |

**What it does:**
1. Pulls the latest images from DockerHub
2. Starts all services (API, ChromaDB, Ollama, web-manager)
3. Waits for services to be healthy

**Examples:**
```bash
# Basic startup
./scripts/start-docker.sh

# With verbose output
./scripts/start-docker.sh --verbose

# View help
./scripts/start-docker.sh --help
```

**When to use:**
- Production deployments
- Quick local testing without building images
- When you want to use the latest stable release

---

### start-docker-dev.sh

Start Krakenly using Docker Compose with locally built images for development.

**Usage:**
```bash
./scripts/start-docker-dev.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |

**What it does:**
1. Builds images from local source code
2. Starts all services with development configuration
3. Mounts local volumes for hot-reloading (where applicable)

**Examples:**
```bash
# Start development environment
./scripts/start-docker-dev.sh

# Rebuild and start with verbose output
./scripts/start-docker-dev.sh --verbose
```

**When to use:**
- Active development
- Testing local code changes
- Debugging issues

---

### deploy-k8s.sh

Deploy Krakenly to a production Kubernetes cluster.

**Usage:**
```bash
./scripts/deploy-k8s.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |
| `--yes`, `-y` | Skip confirmation prompts |

**What it does:**
1. Validates kubectl is configured and cluster is accessible
2. Applies Kubernetes manifests from `k8s/` directory
3. Creates namespace, deployments, services, and ingress
4. Waits for pods to be ready

**Prerequisites:**
- kubectl configured with cluster access
- Cluster with ingress controller (for external access)
- Sufficient resources (see hardware requirements)

**Examples:**
```bash
# Deploy with confirmation prompt
./scripts/deploy-k8s.sh

# Deploy without confirmation
./scripts/deploy-k8s.sh --yes

# Deploy with verbose output and skip confirmation
./scripts/deploy-k8s.sh --verbose --yes
```

**When to use:**
- Production Kubernetes deployments
- Staging environments
- Any pre-configured Kubernetes cluster

---

### deploy-k8s-local.sh

Deploy Krakenly to a local minikube cluster for development and testing.

**Usage:**
```bash
./scripts/deploy-k8s-local.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |
| `--yes`, `-y` | Skip confirmation prompts |

**What it does:**
1. Starts minikube if not running
2. Enables required addons (ingress, storage)
3. Builds Docker images inside minikube
4. Applies Kubernetes manifests
5. Waits for pods to be ready
6. Runs tests to verify deployment
7. Displays access URLs

**Examples:**
```bash
# Full local deployment
./scripts/deploy-k8s-local.sh

# Quick deployment without prompts
./scripts/deploy-k8s-local.sh --yes

# Debug deployment issues
./scripts/deploy-k8s-local.sh --verbose
```

**When to use:**
- Local Kubernetes development
- Testing K8s manifests before production
- Learning Kubernetes with Krakenly

---

## Cleanup Scripts

### cleanup-docker.sh

Clean up Docker Compose resources. **By default, preserves data volumes.**

**Usage:**
```bash
./scripts/cleanup-docker.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |
| `--yes`, `-y` | Skip confirmation prompts |
| `--data`, `-d` | Also delete data volumes (ChromaDB, Ollama models) |
| `--images`, `-i` | Also delete Docker images |
| `--all`, `-a` | Full cleanup: containers, volumes, and images |

**What it does (default):**
1. Stops running containers
2. Removes containers and networks
3. Preserves data volumes

**What it does (with options):**
- `--data`: Also removes ChromaDB and Ollama data volumes
- `--images`: Also removes Krakenly Docker images
- `--all`: Removes everything (containers, volumes, images)

**Examples:**
```bash
# Stop and remove containers (keep data)
./scripts/cleanup-docker.sh

# Remove everything including data
./scripts/cleanup-docker.sh --all

# Remove containers and images, keep data
./scripts/cleanup-docker.sh --images

# Remove containers and data, keep images
./scripts/cleanup-docker.sh --data

# Full cleanup without confirmation
./scripts/cleanup-docker.sh --all --yes

# Verbose cleanup for debugging
./scripts/cleanup-docker.sh --verbose
```

**Data volumes preserved by default:**
- ChromaDB vector database
- Ollama downloaded models

**When to use each option:**
| Scenario | Command |
|----------|---------|
| Restart services | `./scripts/cleanup-docker.sh` |
| Free disk space (keep data) | `./scripts/cleanup-docker.sh --images` |
| Fresh start (lose data) | `./scripts/cleanup-docker.sh --all` |
| CI/CD cleanup | `./scripts/cleanup-docker.sh --all --yes` |

---

### cleanup-k8s.sh

Clean up Kubernetes resources. **By default, preserves persistent volume claims.**

**Usage:**
```bash
./scripts/cleanup-k8s.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |
| `--yes`, `-y` | Skip confirmation prompts |
| `--data`, `-d` | Also delete persistent volume claims |
| `--minikube`, `-m` | Also delete the minikube cluster |
| `--all`, `-a` | Full cleanup: namespace, PVCs, and minikube |

**What it does (default):**
1. Deletes Krakenly namespace and all resources within
2. Preserves persistent volume claims (data)

**What it does (with options):**
- `--data`: Also removes PVCs (ChromaDB, Ollama data)
- `--minikube`: Also deletes the minikube cluster
- `--all`: Removes everything including minikube

**Examples:**
```bash
# Remove deployments (keep data)
./scripts/cleanup-k8s.sh

# Remove everything including PVCs
./scripts/cleanup-k8s.sh --data

# Full cleanup including minikube
./scripts/cleanup-k8s.sh --all

# Quick cleanup for CI
./scripts/cleanup-k8s.sh --all --yes

# Debug cleanup process
./scripts/cleanup-k8s.sh --verbose
```

**When to use each option:**
| Scenario | Command |
|----------|---------|
| Redeploy (keep data) | `./scripts/cleanup-k8s.sh` |
| Fresh namespace | `./scripts/cleanup-k8s.sh --data` |
| Complete reset | `./scripts/cleanup-k8s.sh --all` |
| CI/CD cleanup | `./scripts/cleanup-k8s.sh --all --yes` |

---

## Prerequisites Scripts

### install-docker-prereqs.sh

Install Docker and Docker Compose prerequisites.

**Usage:**
```bash
./scripts/install-docker-prereqs.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |

**What it installs:**
- Docker Engine
- Docker Compose plugin
- Required system dependencies

**Supported platforms:**
- Ubuntu/Debian
- macOS (via Homebrew)
- Other Linux distributions (generic instructions)

**Examples:**
```bash
# Install prerequisites
./scripts/install-docker-prereqs.sh

# Install with verbose output
./scripts/install-docker-prereqs.sh --verbose
```

**Post-installation:**
- Log out and back in for group changes to take effect
- Verify with `docker --version` and `docker compose version`

---

### install-k8s-prereqs.sh

Install Kubernetes prerequisites including kubectl and minikube.

**Usage:**
```bash
./scripts/install-k8s-prereqs.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |

**What it installs:**
- kubectl (Kubernetes CLI)
- minikube (local Kubernetes)
- Required virtualization drivers

**Supported platforms:**
- Ubuntu/Debian
- macOS (via Homebrew)
- Other Linux distributions (generic instructions)

**Examples:**
```bash
# Install Kubernetes tools
./scripts/install-k8s-prereqs.sh

# Install with verbose output
./scripts/install-k8s-prereqs.sh --verbose
```

**Post-installation:**
- Verify with `kubectl version --client` and `minikube version`
- Start minikube with `minikube start`

---

## Testing & Benchmarking

### test.sh

Run API tests against a running Krakenly instance.

**Usage:**
```bash
./scripts/test.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |

**What it tests:**
- API health endpoints
- Document indexing
- Search functionality
- Embedding generation

**Prerequisites:**
- Krakenly must be running (Docker or Kubernetes)
- API must be accessible at configured endpoint

**Examples:**
```bash
# Run tests
./scripts/test.sh

# Run tests with verbose output
./scripts/test.sh --verbose
```

**Works with:**
- Docker Compose deployments
- Kubernetes deployments (uses port-forward or ingress)

---

### benchmark.sh

Run performance benchmarks against a running Krakenly instance.

**Usage:**
```bash
./scripts/benchmark.sh [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--verbose`, `-v` | Enable verbose output |

**What it benchmarks:**
- Indexing throughput
- Search latency
- Embedding generation speed
- Concurrent request handling

**Prerequisites:**
- Krakenly must be running
- Python 3.x with required packages

**Examples:**
```bash
# Run benchmarks
./scripts/benchmark.sh

# Run with verbose output
./scripts/benchmark.sh --verbose
```

**Output:**
- Results saved to `benchmark_results.json`
- Summary printed to console

---

## Common Workflows

### First-time Setup (Docker)

```bash
# 1. Install prerequisites
./scripts/install-docker-prereqs.sh

# 2. Start the application
./scripts/start-docker.sh

# 3. Verify it's working
./scripts/test.sh
```

### First-time Setup (Kubernetes)

```bash
# 1. Install prerequisites
./scripts/install-k8s-prereqs.sh

# 2. Deploy locally (includes tests)
./scripts/deploy-k8s-local.sh
```

### Development Cycle (Docker)

```bash
# Start development environment
./scripts/start-docker-dev.sh

# Make code changes...

# Restart to pick up changes
./scripts/cleanup-docker.sh
./scripts/start-docker-dev.sh

# Run tests
./scripts/test.sh
```

### Development Cycle (Kubernetes)

```bash
# Deploy to local minikube
./scripts/deploy-k8s-local.sh

# Make code changes...

# Redeploy
./scripts/cleanup-k8s.sh
./scripts/deploy-k8s-local.sh
```

### Complete Reset (Docker)

```bash
# Remove everything and start fresh
./scripts/cleanup-docker.sh --all --yes
./scripts/start-docker.sh
```

### Complete Reset (Kubernetes)

```bash
# Remove everything including minikube
./scripts/cleanup-k8s.sh --all --yes
./scripts/deploy-k8s-local.sh --yes
```

### CI/CD Pipeline

```bash
# Deploy without prompts
./scripts/deploy-k8s.sh --yes

# Run tests
./scripts/test.sh

# Run benchmarks
./scripts/benchmark.sh

# Cleanup
./scripts/cleanup-k8s.sh --all --yes
```

### Troubleshooting

```bash
# Use verbose mode to see what's happening
./scripts/start-docker.sh --verbose
./scripts/deploy-k8s-local.sh --verbose

# Check script help
./scripts/start-docker.sh --help
```

---

## See Also

- [README.md](../README.md) - Quick start guide
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration options
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [API.md](API.md) - API documentation
