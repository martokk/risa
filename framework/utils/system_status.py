import shutil
import subprocess
from pathlib import Path
from typing import Any

import psutil
from pydantic import BaseModel


class SystemStatus(BaseModel):
    cpu_usage: float
    gpu_usage: float
    gpu_memory_used: float
    total_disk_space: float
    used_disk_space: float
    free_disk_space: float


def get_gpu_stats() -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used",
                "--format=csv,nounits,noheader",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
            timeout=5,
        )
        usage, mem_used = result.stdout.strip().split(", ")
        status = {
            "gpu_usage": float(usage),
            "gpu_memory_used": float(mem_used),
        }
        return status
    except Exception:
        return {
            "gpu_usage": None,
            "gpu_memory_used": None,
        }


def get_cpu_stats() -> dict[str, float]:
    cpu = psutil.cpu_percent(interval=0.5)
    return {
        "cpu_usage": cpu,
    }


def get_disk_stats(path: str | Path = "/") -> dict[str, Any]:
    """Get disk usage statistics in GB.

    Args:
        path: Path to check disk usage for, defaults to root directory.

    Returns:
        Dictionary containing disk space values in GB and usage percentage.
    """
    try:
        total, used, free = shutil.disk_usage(Path(path))
        used_percent = used / total * 100
        # Convert bytes to GB (1 GB = 1024^3 bytes)
        bytes_to_gb = 1024**3
        return {
            "total_disk_space": int(total / bytes_to_gb),
            "used_disk_space": int(used / bytes_to_gb),
            "free_disk_space": int(free / bytes_to_gb),
            "disk_usage": used_percent,
        }
    except Exception:
        return {}


def get_system_status() -> SystemStatus:
    statuses = get_cpu_stats()
    statuses.update(get_gpu_stats())
    statuses.update(get_disk_stats())
    return SystemStatus(**statuses)


def get_system_status_as_dict() -> dict[str, Any]:
    return get_system_status().model_dump()
