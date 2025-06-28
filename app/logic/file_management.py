import glob
from pathlib import Path

from pydantic import BaseModel

from app.paths import OUTPUTS_KOHYA_SS_PATH


class TrainedLoraSafetensors(BaseModel):
    """A class to represent a trained lora safetensors files in the OUTPUTS_KOHYA_SS_PATH folder."""

    lora_output_name: str
    min_epoch: int
    max_epoch: int


def get_trained_lora_safetensors() -> list[TrainedLoraSafetensors]:
    """Get all files from the OUTPUTS_KOHYA_SS_PATH folder that do NOT end with .safetensors.
    For each unique lora_output_name, find the min and max epoch (max+1) among its files.
    """

    files = glob.glob(str(OUTPUTS_KOHYA_SS_PATH / "*.safetensors"))

    lora_epochs: dict[str, list[int]] = {}

    for file in files:
        file_stem = str(Path(file).stem)

        parts = file_stem.split("-")
        lora_output_name = parts[0]
        epoch_part = parts[-1] if len(parts) > 1 else None

        if epoch_part and epoch_part.isdigit() and len(epoch_part) == 6:
            epoch = int(epoch_part)
        else:
            epoch = None

        if epoch:
            lora_epochs.setdefault(lora_output_name, []).append(epoch)
        else:
            lora_epochs.setdefault(lora_output_name, [])

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
