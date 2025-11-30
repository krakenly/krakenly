#!/usr/bin/env python3
"""
Krakenly Benchmark Script
https://github.com/krakenly/krakenly

This script benchmarks Krakenly's RAG performance by:
1. Uploading sample data
2. Running queries of varying complexity
3. Collecting timing and throughput metrics
4. Generating a comprehensive performance report

Usage:
    python scripts/benchmark.py [--api-url URL] [--sample-file PATH]

Requirements:
    - requests library (pip install requests)
    - Krakenly services running (./scripts/start.sh)
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library required. Install with: pip install requests")
    sys.exit(1)


# ============== Configuration ==============

DEFAULT_API_URL = "http://localhost:5000"
DEFAULT_SAMPLE_FILE = "tests/sample_data.md"

# Query definitions by complexity
BENCHMARK_QUERIES = {
    "trivial": [
        {"query": "hi"},
        {"query": "hello"},
        {"query": "hey"},
        {"query": "thanks"},
        {"query": "ok"},
        {"query": "test"},
        {"query": "help"},
        {"query": "bye"},
        {"query": "yes"},
        {"query": "no"},
    ],
    "simple": [
        {"query": "what is this", "top_k": 2, "max_tokens": 64},
        {"query": "what port does the API use", "top_k": 2, "max_tokens": 64},
        {"query": "what LLM model is used", "top_k": 2, "max_tokens": 64},
        {"query": "what is ChromaDB", "top_k": 2, "max_tokens": 64},
        {"query": "what is Ollama", "top_k": 2, "max_tokens": 64},
        {"query": "what is the embedding model", "top_k": 2, "max_tokens": 64},
        {"query": "how much RAM is needed", "top_k": 2, "max_tokens": 64},
        {"query": "what is the web manager port", "top_k": 2, "max_tokens": 64},
        {"query": "is this local or cloud", "top_k": 2, "max_tokens": 64},
        {"query": "what framework is the API", "top_k": 2, "max_tokens": 64},
    ],
    "medium": [
        {"query": "list all the API endpoints", "top_k": 3, "max_tokens": 128},
        {"query": "explain the architecture", "top_k": 3, "max_tokens": 128},
        {"query": "what are the hardware requirements", "top_k": 3, "max_tokens": 128},
        {"query": "describe the key features", "top_k": 3, "max_tokens": 128},
        {"query": "explain RAG-based chat", "top_k": 3, "max_tokens": 128},
        {"query": "what are the performance benchmarks", "top_k": 3, "max_tokens": 128},
        {"query": "describe data indexing", "top_k": 3, "max_tokens": 128},
        {"query": "explain the privacy features", "top_k": 3, "max_tokens": 128},
        {"query": "list the common commands", "top_k": 3, "max_tokens": 128},
        {"query": "describe the design philosophy", "top_k": 3, "max_tokens": 128},
    ],
    "complex": [
        {"query": "explain the complete system architecture with all services and their roles", "top_k": 5, "max_tokens": 200},
        {"query": "compare all the different services and their purposes", "top_k": 5, "max_tokens": 200},
        {"query": "describe all API endpoints with their methods and descriptions", "top_k": 5, "max_tokens": 200},
        {"query": "explain the performance characteristics and what affects response time", "top_k": 5, "max_tokens": 200},
        {"query": "summarize all the content including features, architecture, and requirements", "top_k": 5, "max_tokens": 200},
        {"query": "what makes this different from other AI assistants and why", "top_k": 5, "max_tokens": 200},
        {"query": "describe the complete indexing and search workflow", "top_k": 5, "max_tokens": 200},
        {"query": "explain all the hardware requirements and performance expectations", "top_k": 5, "max_tokens": 200},
        {"query": "list and explain all the key features with examples", "top_k": 5, "max_tokens": 200},
        {"query": "describe the security and privacy model in detail", "top_k": 5, "max_tokens": 200},
    ],
}


# ============== System Information ==============

def get_system_info():
    """Collect system hardware and software information."""
    info = {
        "timestamp": datetime.now().isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python_version": platform.python_version(),
    }
    
    # CPU info (Linux)
    if platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
            
            # Extract model name
            for line in cpuinfo.split("\n"):
                if "model name" in line:
                    info["cpu_model"] = line.split(":")[1].strip()
                    break
            
            # Count cores
            info["cpu_cores"] = cpuinfo.count("processor")
            
        except Exception:
            pass
        
        # Memory info
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            for line in meminfo.split("\n"):
                if "MemTotal" in line:
                    mem_kb = int(line.split()[1])
                    info["memory_gb"] = round(mem_kb / 1024 / 1024, 1)
                    break
        except Exception:
            pass
    
    # macOS
    elif platform.system() == "Darwin":
        try:
            info["cpu_model"] = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], 
                text=True
            ).strip()
            info["cpu_cores"] = int(subprocess.check_output(
                ["sysctl", "-n", "hw.ncpu"], 
                text=True
            ).strip())
            mem_bytes = int(subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"], 
                text=True
            ).strip())
            info["memory_gb"] = round(mem_bytes / 1024 / 1024 / 1024, 1)
        except Exception:
            pass
    
    return info


def get_docker_info(api_url):
    """Get Docker container and model information."""
    info = {}
    
    try:
        # Get health info
        resp = requests.get(f"{api_url}/health", timeout=10)
        if resp.status_code == 200:
            health = resp.json()
            info["ollama"] = health.get("ollama", {})
            info["chromadb"] = health.get("chromadb", {})
            info["embeddings"] = health.get("embeddings", {})
            info["documents_count"] = health.get("documents_count", 0)
        
        # Get model details
        resp = requests.get(f"{api_url}/models", timeout=10)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            if models:
                model = models[0]  # Primary model
                info["model_details"] = {
                    "name": model.get("name"),
                    "size_gb": round(model.get("size", 0) / 1024 / 1024 / 1024, 2),
                    "parameter_size": model.get("details", {}).get("parameter_size"),
                    "quantization": model.get("details", {}).get("quantization_level"),
                }
    except Exception as e:
        info["error"] = str(e)
    
    return info


# ============== Benchmark Functions ==============

def upload_sample_file(api_url, file_path):
    """Upload the sample file to Krakenly."""
    print(f"\n📄 Uploading sample file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"   ERROR: File not found: {file_path}")
        return False
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            resp = requests.post(f"{api_url}/index/upload", files=files, timeout=120)
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"   ✅ Indexed {result.get('chunks_indexed', 0)} chunks")
            print(f"   📊 File size: {result.get('size_bytes', 0)} bytes")
            return True
        else:
            print(f"   ❌ Upload failed: {resp.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def run_query(api_url, query_params):
    """Run a single query and return timing metrics."""
    try:
        start = time.time()
        resp = requests.post(
            f"{api_url}/search/rag",
            json=query_params,
            timeout=180
        )
        wall_time = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            timings = data.get("timings", {})
            return {
                "success": True,
                "wall_time_ms": round(wall_time * 1000, 2),
                "total_ms": timings.get("total_ms", 0),
                "ollama_ms": timings.get("ollama_ms", 0),
                "embedding_ms": timings.get("embedding_ms", 0),
                "chromadb_ms": timings.get("chromadb_ms", 0),
                "tokens_generated": timings.get("tokens_generated", 0),
                "tokens_per_sec": timings.get("tokens_per_sec", 0),
                "context_chars": timings.get("context_chars", 0),
                "context_chunks": data.get("context_chunks_used", 0),
            }
        else:
            return {"success": False, "error": resp.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def percentile(data, p):
    """Calculate the p-th percentile of a list of numbers."""
    if not data:
        return 0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def run_benchmark(api_url, queries, complexity):
    """Run all queries for a complexity level and collect metrics."""
    print(f"\n🔄 Running {complexity.upper()} queries ({len(queries)} total)...")
    
    results = []
    for i, q in enumerate(queries):
        query_text = q["query"][:40] + "..." if len(q["query"]) > 40 else q["query"]
        print(f"   [{i+1}/{len(queries)}] {query_text}", end=" ", flush=True)
        
        result = run_query(api_url, q)
        results.append(result)
        
        if result["success"]:
            print(f"→ {result['total_ms']/1000:.1f}s, {result['tokens_per_sec']:.1f} tok/s")
        else:
            print(f"→ ERROR: {result.get('error', 'Unknown')[:50]}")
    
    return results


def calculate_stats(results):
    """Calculate aggregate statistics from benchmark results."""
    successful = [r for r in results if r.get("success")]
    
    if not successful:
        return {"error": "No successful queries"}
    
    # Extract metrics
    times = [r["total_ms"] for r in successful]
    speeds = [r["tokens_per_sec"] for r in successful]
    tokens = [r["tokens_generated"] for r in successful]
    contexts = [r["context_chars"] for r in successful]
    ollama_times = [r["ollama_ms"] for r in successful]
    
    return {
        "total_queries": len(results),
        "successful_queries": len(successful),
        "failed_queries": len(results) - len(successful),
        "response_time_ms": {
            "avg": round(sum(times) / len(times), 1),
            "min": round(min(times), 1),
            "max": round(max(times), 1),
            "p50": round(percentile(times, 50), 1),
            "p90": round(percentile(times, 90), 1),
            "p95": round(percentile(times, 95), 1),
        },
        "tokens_per_sec": {
            "avg": round(sum(speeds) / len(speeds), 1),
            "min": round(min(speeds), 1),
            "max": round(max(speeds), 1),
            "p50": round(percentile(speeds, 50), 1),
            "p90": round(percentile(speeds, 90), 1),
            "p95": round(percentile(speeds, 95), 1),
        },
        "tokens_generated": {
            "avg": round(sum(tokens) / len(tokens), 1),
            "total": sum(tokens),
        },
        "context_chars": {
            "avg": round(sum(contexts) / len(contexts), 1),
        },
        "ollama_time_pct": round(sum(ollama_times) / sum(times) * 100, 1) if sum(times) > 0 else 0,
    }


# ============== Report Generation ==============

def print_header(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f" {title}")
    print('='*70)


def print_system_info(system_info, docker_info):
    """Print system information section."""
    print_header("SYSTEM INFORMATION")
    
    print(f"\n📅 Benchmark Date: {system_info.get('timestamp', 'N/A')}")
    
    print(f"\n🖥️  Hardware:")
    print(f"   CPU: {system_info.get('cpu_model', 'Unknown')}")
    print(f"   Cores: {system_info.get('cpu_cores', 'Unknown')}")
    print(f"   Memory: {system_info.get('memory_gb', 'Unknown')} GB")
    
    print(f"\n💻 Software:")
    print(f"   OS: {system_info.get('platform', {}).get('system', 'Unknown')} {system_info.get('platform', {}).get('release', '')}")
    print(f"   Python: {system_info.get('python_version', 'Unknown')}")
    
    if docker_info:
        print(f"\n🦑 Krakenly:")
        model = docker_info.get("model_details", {})
        print(f"   Model: {model.get('name', 'Unknown')}")
        print(f"   Parameters: {model.get('parameter_size', 'Unknown')}")
        print(f"   Quantization: {model.get('quantization', 'Unknown')}")
        print(f"   Size: {model.get('size_gb', 'Unknown')} GB")
        print(f"   Embedding: {docker_info.get('embeddings', {}).get('model', 'Unknown')}")


def print_results_table(all_stats):
    """Print the benchmark results table."""
    print_header("BENCHMARK RESULTS")
    
    # Response Time Table
    print("\n📊 Response Time (milliseconds):")
    print(f"   {'Complexity':<12} {'Avg':>10} {'P50':>10} {'P90':>10} {'P95':>10} {'Min':>10} {'Max':>10}")
    print(f"   {'-'*72}")
    
    for complexity in ["trivial", "simple", "medium", "complex"]:
        if complexity in all_stats:
            s = all_stats[complexity]["response_time_ms"]
            print(f"   {complexity:<12} {s['avg']:>10.0f} {s['p50']:>10.0f} {s['p90']:>10.0f} {s['p95']:>10.0f} {s['min']:>10.0f} {s['max']:>10.0f}")
    
    # Tokens/sec Table
    print("\n⚡ Throughput (tokens/second):")
    print(f"   {'Complexity':<12} {'Avg':>10} {'P50':>10} {'P90':>10} {'P95':>10} {'Min':>10} {'Max':>10}")
    print(f"   {'-'*72}")
    
    for complexity in ["trivial", "simple", "medium", "complex"]:
        if complexity in all_stats:
            s = all_stats[complexity]["tokens_per_sec"]
            print(f"   {complexity:<12} {s['avg']:>10.1f} {s['p50']:>10.1f} {s['p90']:>10.1f} {s['p95']:>10.1f} {s['min']:>10.1f} {s['max']:>10.1f}")
    
    # Summary
    print("\n📈 Summary:")
    total_queries = sum(s.get("total_queries", 0) for s in all_stats.values())
    successful = sum(s.get("successful_queries", 0) for s in all_stats.values())
    failed = sum(s.get("failed_queries", 0) for s in all_stats.values())
    
    print(f"   Total Queries: {total_queries}")
    print(f"   Successful: {successful} ({successful/total_queries*100:.1f}%)" if total_queries > 0 else "   Successful: 0")
    print(f"   Failed: {failed}")
    
    # LLM is the bottleneck
    avg_ollama_pct = sum(s.get("ollama_time_pct", 0) for s in all_stats.values()) / len(all_stats)
    print(f"   LLM Time: {avg_ollama_pct:.1f}% of total (bottleneck)")


def print_recommendations(all_stats):
    """Print performance recommendations."""
    print_header("RECOMMENDATIONS")
    
    # Check average speed
    if "simple" in all_stats:
        avg_speed = all_stats["simple"]["tokens_per_sec"]["avg"]
        
        if avg_speed < 5:
            print("\n⚠️  Low throughput detected. Consider:")
            print("   • Reduce MAX_CONTEXT_CHARS in config")
            print("   • Use a smaller model (qwen2.5:1.5b or qwen2.5:0.5b)")
            print("   • Add GPU for 10-20x speedup")
        elif avg_speed < 10:
            print("\n💡 Moderate throughput. To improve:")
            print("   • Reduce top_k for faster context retrieval")
            print("   • Consider qwen2.5:1.5b for 2x speed")
        else:
            print("\n✅ Good throughput for CPU inference.")
    
    # Check complex query times
    if "complex" in all_stats:
        p95_time = all_stats["complex"]["response_time_ms"]["p95"]
        if p95_time > 60000:
            print("\n⚠️  Complex queries are slow (P95 > 60s). Consider:")
            print("   • Reduce max_tokens for complex queries")
            print("   • Limit top_k to 3")


def save_json_report(system_info, docker_info, all_stats, output_path):
    """Save detailed JSON report."""
    report = {
        "benchmark_version": "1.0",
        "system": system_info,
        "docker": docker_info,
        "results": all_stats,
    }
    
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📁 Detailed JSON report saved to: {output_path}")


# ============== Main ==============

def main():
    parser = argparse.ArgumentParser(description="Krakenly Benchmark")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API base URL")
    parser.add_argument("--sample-file", default=DEFAULT_SAMPLE_FILE, help="Sample data file")
    parser.add_argument("--output", default="benchmark_results.json", help="Output JSON file")
    parser.add_argument("--skip-upload", action="store_true", help="Skip file upload")
    args = parser.parse_args()
    
    print_header("KRAKENLY BENCHMARK")
    print(f"\n🚀 Starting benchmark...")
    print(f"   API URL: {args.api_url}")
    print(f"   Sample File: {args.sample_file}")
    
    # Check API health
    print(f"\n🔍 Checking API health...")
    try:
        resp = requests.get(f"{args.api_url}/health", timeout=10)
        if resp.status_code != 200:
            print(f"   ❌ API not healthy: {resp.status_code}")
            sys.exit(1)
        print(f"   ✅ API is healthy")
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        sys.exit(1)
    
    # Collect system info
    system_info = get_system_info()
    docker_info = get_docker_info(args.api_url)
    
    # Print system info
    print_system_info(system_info, docker_info)
    
    # Upload sample file
    if not args.skip_upload:
        if not upload_sample_file(args.api_url, args.sample_file):
            print("   ⚠️  Continuing with existing data...")
    
    # Warm up the model
    print(f"\n🔥 Warming up model...")
    run_query(args.api_url, {"query": "warmup"})
    print(f"   ✅ Model ready")
    
    # Run benchmarks
    all_stats = {}
    all_results = {}
    
    for complexity, queries in BENCHMARK_QUERIES.items():
        results = run_benchmark(args.api_url, queries, complexity)
        all_results[complexity] = results
        all_stats[complexity] = calculate_stats(results)
    
    # Print results
    print_results_table(all_stats)
    print_recommendations(all_stats)
    
    # Save JSON report
    save_json_report(system_info, docker_info, all_stats, args.output)
    
    print_header("BENCHMARK COMPLETE")
    print(f"\n✅ Benchmark finished successfully!")
    print(f"   Run 'cat {args.output}' for detailed metrics.\n")


if __name__ == "__main__":
    main()
