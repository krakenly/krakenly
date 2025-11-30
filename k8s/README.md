# Kubernetes Deployment

Deploy Krakenly to a Kubernetes cluster.

## Quick Start

```bash
# Deploy all components
kubectl apply -k k8s/

# Check status
kubectl -n krakenly get pods

# Wait for pods to be ready
kubectl -n krakenly wait --for=condition=ready pod -l app.kubernetes.io/part-of=krakenly --timeout=300s
```

## Components

| Component | Description | Resources |
|-----------|-------------|-----------|
| Ollama | LLM inference | 4-8GB RAM, 1-4 CPU |
| ChromaDB | Vector database | 512MB-2GB RAM |
| Krakenly | API + Web UI | 1-4GB RAM |

## Access the Services

### Option 1: Port Forward (Development)

```bash
# Web UI
kubectl -n krakenly port-forward svc/krakenly 8080:80

# API
kubectl -n krakenly port-forward svc/krakenly 5000:5000
```

Open http://localhost:8080 in your browser.

### Option 2: Ingress (Production)

1. Edit `k8s/ingress.yaml` and set your domain
2. Uncomment the ingress in `k8s/kustomization.yaml`
3. Apply: `kubectl apply -k k8s/`

### Option 3: LoadBalancer

```bash
kubectl -n krakenly patch svc krakenly -p '{"spec": {"type": "LoadBalancer"}}'
```

## Storage

The deployment uses PersistentVolumeClaims:

| PVC | Size | Purpose |
|-----|------|---------|
| ollama-data | 10Gi | LLM models |
| chromadb-data | 5Gi | Vector embeddings |
| krakenly-data | 1Gi | Index metadata |

Adjust sizes in `k8s/pvc.yaml` as needed.

## GPU Support (Optional)

For GPU-accelerated inference, add to `k8s/ollama.yaml`:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

And ensure the NVIDIA device plugin is installed in your cluster.

## Uninstall

```bash
kubectl delete -k k8s/
```

## Troubleshooting

```bash
# Check pod status
kubectl -n krakenly get pods

# View logs
kubectl -n krakenly logs -l app.kubernetes.io/name=krakenly -f
kubectl -n krakenly logs -l app.kubernetes.io/name=ollama -f
kubectl -n krakenly logs -l app.kubernetes.io/name=chromadb -f

# Describe pod for events
kubectl -n krakenly describe pod -l app.kubernetes.io/name=krakenly
```
