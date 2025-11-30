# Performance Benchmarks

This document provides detailed performance benchmarks for Krakenly.

## Test Environment

| Component | Specification |
|-----------|---------------|
| **CPU** | `AMD EPYC 9V74` (8 vCPUs) |
| **RAM** | 31 GB |
| **GPU** | None (CPU-only inference) |
| **OS** | Linux |
| **Model** | `qwen2.5:3b` (Q4_K_M quantization, 1.9GB) |
| **Embedding** | `BAAI/bge-small-en-v1.5` |

---

## Query Complexity Levels

Benchmarks use 4 complexity levels based on expected response length:

| Level | Max Tokens | Expected Response |
|-------|------------|-------------------|
| **Trivial** | 32 | Single fact or number |
| **Simple** | 64 | One-sentence answer |
| **Medium** | 128 | Short paragraph |
| **Complex** | 256 | Detailed explanation |

---

## Response Time Results

### Summary (milliseconds)

| Complexity | Avg | P50 | P90 | P95 | Min | Max |
|------------|-----|-----|-----|-----|-----|-----|
| **Trivial** | 1,678 | 1,788 | 1,906 | 1,908 | 923 | 1,910 |
| **Simple** | 5,732 | 5,875 | 7,167 | 7,178 | 2,911 | 7,188 |
| **Medium** | 9,968 | 10,192 | 12,278 | 12,428 | 6,700 | 12,579 |
| **Complex** | 18,737 | 17,620 | 24,588 | 25,922 | 12,996 | 27,254 |

### Interpretation

- **Trivial queries** (1-2s): Quick lookups, ideal for simple facts
- **Simple queries** (5-6s): Short answers, acceptable for interactive use
- **Medium queries** (10s): Paragraph responses, good for explanations
- **Complex queries** (18-19s): Detailed responses, best for comprehensive answers

---

## Throughput Results

### Summary (tokens/second)

| Complexity | Avg | P50 | P90 | P95 | Min | Max |
|------------|-----|-----|-----|-----|-----|-----|
| **Trivial** | 16.4 | 16.7 | 16.8 | 16.9 | 15.2 | 16.9 |
| **Simple** | 10.4 | 10.8 | 11.7 | 12.4 | 8.6 | 13.1 |
| **Medium** | 13.0 | 12.6 | 15.4 | 15.7 | 10.2 | 16.1 |
| **Complex** | 11.2 | 11.4 | 14.5 | 15.0 | 7.3 | 15.4 |

### Interpretation

- **Consistent throughput**: 10-17 tokens/second across all complexity levels
- **CPU-bound**: Throughput limited by CPU inference speed
- **Context impact**: Larger context slightly reduces throughput

---

## Time Breakdown

Where does the time go?

| Component | Time | Percentage |
|-----------|------|------------|
| **LLM Inference** | 1,660-18,700ms | 99.9% |
| **Embedding** | 5-10ms | <0.1% |
| **Vector Search** | 5-10ms | <0.1% |
| **Network/API** | 1-2ms | <0.1% |

### Key Finding

**LLM inference is the bottleneck.** The embedding and vector search components are extremely fast (<20ms combined). Any performance improvements should focus on:

1. Using a smaller model (e.g., `qwen2.5:0.5b`)
2. Adding GPU acceleration
3. Reducing max tokens for faster responses

---

## Cold Start vs Warm Performance

### First Request (Cold Start)

When the model isn't loaded in memory:

| Metric | Time |
|--------|------|
| Model loading | 10-30 seconds |
| First inference | Additional 2-5 seconds |
| **Total** | 12-35 seconds |

### Subsequent Requests (Warm)

After the model is loaded:

| Metric | Time |
|--------|------|
| Inference only | 1-19 seconds (depends on complexity) |

### Recommendations

- Keep the Ollama container running to avoid cold starts
- First request after restart will be slow
- Model stays in memory until container stops or memory pressure

---

## Success Rate

| Metric | Result |
|--------|--------|
| **Queries tested** | 40 (10 per complexity level) |
| **Success rate** | 100% |
| **Errors** | 0 |
| **Timeouts** | 0 |

---

## Model Comparison (Estimated)

Based on model sizes and parameter counts, expected performance differences:

| Model | Size | Response Time (vs qwen2.5:3b) | Quality |
|-------|------|-------------------------------|---------|
| `qwen2.5:0.5b` | 400MB | 3-4x faster | Lower |
| `qwen2.5:3b` | 1.9GB | Baseline | Good |
| `phi3:mini` | 2.3GB | Similar | Similar |
| `qwen2.5:7b` | 4.4GB | 2-3x slower | Higher |
| `mistral:7b` | 4.1GB | 2-3x slower | Higher |

---

## Hardware Recommendations

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| RAM | 8GB |
| CPU | 2 cores |
| Disk | 10GB |

**Expected performance:** 2-3x slower than benchmark results

### Recommended Requirements

| Component | Requirement |
|-----------|-------------|
| RAM | 12GB+ |
| CPU | 4+ cores |
| Disk | 20GB |

**Expected performance:** Similar to benchmark results

### Optimal Setup

| Component | Requirement |
|-----------|-------------|
| RAM | 16GB+ |
| CPU | 8+ cores |
| GPU | NVIDIA with 6GB+ VRAM |
| Disk | 50GB+ SSD |

**Expected performance:** 5-10x faster than CPU-only benchmarks

---

## Running Your Own Benchmark

### Basic Usage

```bash
python scripts/benchmark.py
```

### Options

```bash
python scripts/benchmark.py \
  --api-url http://localhost:5000 \
  --sample-file tests/sample_data.md \
  --output-dir benchmark_results
```

### Output

The benchmark generates:
1. Console summary with key metrics
2. JSON report with full statistics
3. Per-query timing details

### Sample Output

```
╔══════════════════════════════════════════════════════╗
║              BENCHMARK RESULTS                       ║
╠══════════════════════════════════════════════════════╣
║  Complexity  │  Avg (ms)  │  P95 (ms)  │  Tok/s     ║
╠══════════════════════════════════════════════════════╣
║  Trivial     │   1,678    │   1,908    │   16.4     ║
║  Simple      │   5,732    │   7,178    │   10.4     ║
║  Medium      │   9,968    │  12,428    │   13.0     ║
║  Complex     │  18,737    │  25,922    │   11.2     ║
╚══════════════════════════════════════════════════════╝
```

---

## Improving Performance

### Quick Wins

1. **Use smaller model**: `qwen2.5:0.5b` for 3-4x speed improvement
2. **Reduce max tokens**: Set `max_tokens` to minimum needed
3. **Keep container running**: Avoid cold starts

### Advanced Optimizations

1. **Add GPU**: NVIDIA GPU provides 5-10x speedup
2. **Increase threads**: Set `OLLAMA_NUM_THREADS` to CPU core count
3. **Use SSD**: Faster model loading from disk

### Query Optimization

1. **Be specific**: Shorter, focused queries = faster responses
2. **Use appropriate complexity**: Don't use 256 tokens for yes/no questions
3. **Batch queries**: Multiple simple queries can be faster than one complex query
