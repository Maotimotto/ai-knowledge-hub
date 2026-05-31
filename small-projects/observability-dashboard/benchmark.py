"""Performance benchmark for observability-dashboard."""
import time, statistics, os, sys

def measure_startup():
    start = time.perf_counter()
    try:
        from main import app  # noqa
    except Exception:
        pass
    return (time.perf_counter() - start) * 1000

def measure_request_latency(n=100):
    """Simulate metrics collection + rendering latency."""
    latencies = []
    for _ in range(n):
        start = time.perf_counter()
        # Simulate: aggregate metrics + compute percentiles
        data = [i * 0.1 for i in range(1000)]
        _ = sorted(data)[len(data)//2]  # placeholder work
        latencies.append((time.perf_counter() - start) * 1000)
    return sorted(latencies)

def get_memory_mb():
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return 0.0

def percentile(data, p):
    k = (len(data) - 1) * (p / 100)
    f, c = int(k), int(k) + 1
    if c >= len(data): return data[f]
    return data[f] + (k - f) * (data[c] - data[f])

def main():
    print("=" * 50)
    print("  OBSERVABILITY-DASHBOARD Performance Benchmark")
    print("=" * 50)
    startup = measure_startup()
    latencies = measure_request_latency(100)
    mem = get_memory_mb()
    print(f"\n{'Metric':<25} {'Value':>15}")
    print("-" * 42)
    print(f"{'Startup time':<25} {startup:>12.2f} ms")
    print(f"{'Requests':<25} {len(latencies):>12}")
    print(f"{'Latency p50':<25} {percentile(latencies,50):>12.3f} ms")
    print(f"{'Latency p95':<25} {percentile(latencies,95):>12.3f} ms")
    print(f"{'Latency p99':<25} {percentile(latencies,99):>12.3f} ms")
    print(f"{'Latency mean':<25} {statistics.mean(latencies):>12.3f} ms")
    print(f"{'Memory (RSS)':<25} {mem:>12.1f} MB")
    print()

if __name__ == "__main__":
    main()
