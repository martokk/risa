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
    """
    Gets all 'trained_lora_safetensors' files in the OUTPUTS_KOHYA_SS_PATH folder.

    This will returns the lora_output_name, min_epoch, and max_epoch for each trained lora.
    """

    files = glob.glob(str(OUTPUTS_KOHYA_SS_PATH / "*.safetensors"))

    lora_epochs: dict[str, list[int]] = {}
    lora_has_non_epoch: dict[str, bool] = {}

    for file in files:
        file_stem = str(Path(file).stem)

        parts = file_stem.split("-")
        lora_output_name = parts[0]
        epoch_part = parts[-1] if len(parts) > 1 else None

        # Check for 6-digit epoch at the end
        if epoch_part and epoch_part.isdigit() and len(epoch_part) == 6:
            epoch = int(epoch_part)
            lora_epochs.setdefault(lora_output_name, []).append(epoch)
        else:
            # This is the non-epoch file (latest)
            lora_has_non_epoch[lora_output_name] = True
            lora_epochs.setdefault(lora_output_name, [])

    result: list[TrainedLoraSafetensors] = []
    for lora_output_name, epochs in lora_epochs.items():
        has_non_epoch = lora_has_non_epoch.get(lora_output_name, False)
        if epochs:
            min_epoch = min(epochs)
            max_epoch = max(epochs) + 1 if has_non_epoch else max(epochs)
        else:
            # Only the non-epoch file exists
            min_epoch = 1
            max_epoch = 1
        result.append(
            TrainedLoraSafetensors(
                lora_output_name=lora_output_name,
                min_epoch=min_epoch,
                max_epoch=max_epoch,
            )
        )
    return result
