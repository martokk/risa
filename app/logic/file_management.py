import glob
import os

from pydantic import BaseModel

from app.models import settings


class TrainedLoraSafetensors(BaseModel):
    """A class to represent a trained lora safetensors files in the /workspace/__OUTPUTS__/kohya_ss/ folder."""

    lora_output_name: str
    min_epoch: int
    max_epoch: int


def get_trained_lora_safetensors() -> list[TrainedLoraSafetensors]:
    """Get all files from the /workspace/__OUTPUTS__/kohya_ss/ folder that end with .safetensors.
    For each unique lora_output_name, find the min and max epoch (max+1) among its files.
    """

    if settings.ENV_NAME == "dev":
        files = glob.glob("/media/martokk/FILES/__INBOX__/__TEMP/temp/*.safetensors")
    else:
        files = glob.glob("/workspace/__OUTPUTS__/kohya_ss/*.safetensors")

    # Dictionary to collect epochs for each lora_output_name
    lora_epochs: dict[str, list[int]] = {}

    for file in files:
        base = os.path.basename(file)
        # Split on dash, first part is lora_output_name
        parts = base.split("-")
        lora_output_name = parts[0]
        # Try to extract epoch from the last 6 digits before .safetensors
        epoch = None
        if len(parts) > 1:
            # Find the part before the extension
            epoch_part = parts[-1].replace(".safetensors", "")
            if epoch_part.isdigit() and len(epoch_part) == 6:
                epoch = int(epoch_part)
        if epoch is not None:
            lora_epochs.setdefault(lora_output_name, []).append(epoch)
        else:
            # If no epoch found, treat as epoch 0
            lora_epochs.setdefault(lora_output_name, []).append(0)

    result: list[TrainedLoraSafetensors] = []
    for lora_output_name, epochs in lora_epochs.items():
        min_epoch = min(epochs)
        max_epoch = max(epochs) + 1  # As requested, max+1
        result.append(
            TrainedLoraSafetensors(
                lora_output_name=lora_output_name,
                min_epoch=min_epoch,
                max_epoch=max_epoch,
            )
        )
    return result
