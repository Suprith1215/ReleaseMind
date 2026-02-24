"""
ReleaseMind — Real-Time Metrics Collector (Phase 5)
Pulls CPU + Memory using psutil, optionally queries kubectl pod metrics.
"""

import subprocess
import json
from typing import Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def get_system_metrics() -> dict:
    """
    Return current host CPU and memory usage percentages.
    Falls back gracefully when psutil is unavailable.
    """
    if not PSUTIL_AVAILABLE:
        return {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "source": "unavailable",
            "warning": "psutil not installed — install it: pip install psutil"
        }

    cpu = psutil.cpu_percent(interval=0.5)           # non-blocking 0.5s sample
    mem = psutil.virtual_memory().percent

    return {
        "cpu_percent":    round(cpu, 1),
        "memory_percent": round(mem, 1),
        "source":         "psutil"
    }


def get_k8s_pod_metrics(namespace: str = "default") -> Optional[dict]:
    """
    Optionally pull Kubernetes pod CPU/memory from kubectl top pods.
    Returns None if kubectl is not available.

    kubectl must be configured (KUBECONFIG set, cluster reachable).
    """
    try:
        result = subprocess.run(
            ["kubectl", "top", "pods", "-n", namespace, "--no-headers"],
            capture_output=True, text=True, timeout=8
        )
        if result.returncode != 0:
            return None

        pods = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                pods.append({
                    "name":   parts[0],
                    "cpu":    parts[1],   # e.g. "25m"
                    "memory": parts[2]    # e.g. "128Mi"
                })
        return {"pods": pods, "namespace": namespace}

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    except Exception:
        return None


def compute_metric_risk(
    cpu_percent: float,
    memory_percent: float,
    cpu_threshold: float = 75.0,
    memory_threshold: float = 80.0,
    cpu_risk_per_percent: float = 0.10,
    memory_risk_per_percent: float = 0.08
) -> dict:
    """
    Calculate the additional risk score from current system metrics.
    """
    cpu_risk = 0.0
    mem_risk = 0.0

    if cpu_percent > cpu_threshold:
        cpu_risk = round((cpu_percent - cpu_threshold) * cpu_risk_per_percent, 2)

    if memory_percent > memory_threshold:
        mem_risk = round((memory_percent - memory_threshold) * memory_risk_per_percent, 2)

    return {
        "cpu_risk":    cpu_risk,
        "memory_risk": mem_risk,
        "total_metric_risk": round(cpu_risk + mem_risk, 2),
        "cpu_alert":   cpu_percent > cpu_threshold,
        "memory_alert": memory_percent > memory_threshold
    }
