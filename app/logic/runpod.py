import os


def convert_local_checkpoint_path_to_runpod_path(local_path: str) -> str:
    """
    Converts a Hub File Path to the corresponding RunPod path.

    Args:
        local_path: The Hub File Path to convert

    Returns:
        str: The converted RunPod path

    Example:
        >>> convert_local_checkpoint_path_to_runpod_path('/media/martokk/FILES/AI/hub/models/SDXL/checkpoints/illustrious/model.safetensors')
        '/workspace/stable-diffusion-webui/models/Stable-diffusion/illustrious/model.safetensors'
    """
    # Split the path into parts
    parts = local_path.split("/")

    # Find the model name directory (last directory before the filename)
    base_model_name = parts[-2]
    checkpoint_name = parts[-1]

    # Construct the RunPod path
    runpod_path = f"/workspace/stable-diffusion-webui/models/Stable-diffusion/{base_model_name}/{checkpoint_name}"

    return runpod_path


def get_runpod_pod_id() -> str | None:
    return os.environ.get("RUNPOD_POD_ID")


def get_runpod_gpu_name() -> str | None:
    raw_gpu_name = os.environ.get("RUNPOD_GPU_NAME")
    if raw_gpu_name:
        return raw_gpu_name.replace("NVIDIA ", "").replace("+", " ")
    return None


def get_runpod_public_ip() -> str | None:
    return os.environ.get("RUNPOD_PUBLIC_IP")


def get_runpod_tcp_port_22() -> int | None:
    return int(os.environ.get("RUNPOD_TCP_PORT_22", "22"))
