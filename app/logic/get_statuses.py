import shutil
import subprocess

import psutil


def get_gpu_stats():
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
        )
        usage, mem_used = result.stdout.strip().split(", ")
        status = {
            "gpu_usage": float(usage),
            "gpu_memory_used": float(mem_used),
        }
        return status
    except Exception:
        return None  # No GPU or error


def get_cpu_stats():
    cpu = psutil.cpu_percent(interval=0.5)
    return {
        "cpu_usage": cpu,
    }


def get_disk_stats():
    total, used, free = shutil.disk_usage("/")
    used_percent = used / total * 100
    return {
        "total_disk_space": total,
        "used_disk_space": used,
        "free_disk_space": free,
        "disk_usage": used_percent,
    }


def get_all_statuses():
    statuses = get_cpu_stats()
    statuses.update(get_gpu_stats())
    statuses.update(get_disk_stats())
    return statuses
