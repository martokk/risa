import glob
import os
import shutil
from pathlib import Path
from typing import Any

from app import crud, logger, paths
from app.paths import OUTPUTS_KOHYA_SS_PATH
from framework.core.db import get_db_context
from framework.services import scripts


class ScriptChooseBestEpoch(scripts.Script):
    """
    This script generates a XY plot for a Lora Model.

    It used after training a Lora Model to generate a XY plot of the training epochs.

    It uses the following parameters:
    - Epochs: 9-30
    """

    def _validate_input(self, *args: Any, **kwargs: Any) -> bool:
        return True

    def _get_best_epoch_file_path(
        self, lora_output_name: str, best_epoch_str: str, safetensor_files: list[str]
    ) -> str:
        """Get the path to the best epoch file for a Lora model.

        Args:
            lora_output_name: The name of the Lora model.
            best_epoch: The best epoch number.
        """
        # Find the best epoch file
        best_epoch_file_name = f"{lora_output_name}-{best_epoch_str}.safetensors"
        best_epoch_file_path = None

        for file_path_str in safetensor_files:
            if best_epoch_file_name in file_path_str:
                best_epoch_file_path = file_path_str
                break

        logger.debug(f"best_epoch_file_path: {best_epoch_file_path}")
        if not best_epoch_file_path:
            error_message = (
                f"No best epoch found for {lora_output_name} with epoch {best_epoch_str}"
            )
            logger.error(error_message)
            raise ValueError(error_message)

        return best_epoch_file_path

    def _move_best_epoch_to_hub(
        self,
        best_epoch_file_path: str,
        base_checkpoint_name: str,
        checkpoint_name: str,
        is_known: bool = False,
    ) -> str:
        """Move the best epoch to the hub.

        Args:
            best_epoch_file_path: The path to the best epoch file.
        """
        # Move the best epoch to the hub
        logger.error(f"PLACEHOLDER: Would move best epoch file to hub: {best_epoch_file_path}")

        # hub location
        base_model_name = "SDXL"
        hub_location = (
            paths.HUB_MODELS_PATH
            / base_model_name
            / "loras"
            / base_checkpoint_name
            / checkpoint_name
            / "characters"
        )
        hub_location = hub_location / "known" if is_known else hub_location

        hub_location.mkdir(parents=True, exist_ok=True)

        # Move the best epoch to the hub
        dst = hub_location / Path(best_epoch_file_path).name
        logger.info(f"Attempting to move best epoch file to hub: {best_epoch_file_path} -> {dst}")

        shutil.move(src=best_epoch_file_path, dst=dst)

        logger.info(f"Completed move of best epoch file to hub: {best_epoch_file_path} -> {dst}")

        if not dst.exists() or Path(best_epoch_file_path).exists():
            logger.error(f"Failed to move best epoch file to hub: {dst}")
            raise ValueError(f"Failed to move best epoch file to hub: {dst}")

        logger.info(f"Moved best epoch file to hub: {dst}")

        return str(dst)

    def _delete_old_epochs(
        self, lora_output_name: str, best_epoch_file_path: str, safetensor_files: list[str]
    ) -> list[str]:
        """Delete all other epochs for a Lora model.

        Args:
            lora_output_name: The name of the Lora model.
            best_epoch_file_path: The path to the best epoch file.
            safetensor_files: The list of all safetensor files.
        """
        # Delete all other epochs for this lora_output_name
        deleted_paths = []
        for file_path in safetensor_files:
            if (
                lora_output_name in os.path.basename(file_path)
                and file_path != best_epoch_file_path
            ):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted old epoch file: {file_path}")
                    deleted_paths.append(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")

        return deleted_paths

    def _create_local_job_to_dl_epoch_from_hub(self, best_epoch_file_path: str) -> str:
        """Create a local job to download the epoch from the cloud hub to local hub.

        Args:
            best_epoch_file_path: The path to the best epoch file.
        """
        # Create a local job to download the epoch from the cloud hub to local hub
        logger.error(
            f"PLACEHOLDER: Would create job to download {best_epoch_file_path} from cloud hub to local hub"
        )
        # TODO: Implement actual job creation if needed
        return "123456789"

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the script to select and process the best epoch for a Lora model.

        Args:
            *args: Positional arguments (unused)
            **kwargs: Keyword arguments, must include 'lora_output_name' and 'best_epoch'.

        Returns:
            scripts.ScriptOutput: Output object with success status, message, and data.

        Raises:
            ValueError: If the best epoch file is not found.
        """
        logger.debug(f"Starting {self.__class__.__name__}._run()")

        # Import kwargs
        logger.debug(f"args: {args}")
        logger.debug(f"kwargs: {kwargs}")

        lora_output_name = kwargs["select_lora_output_name"]
        logger.debug(f"lora_output_name: {lora_output_name}")

        best_epoch = int(kwargs["select_best_epoch"])
        best_epoch_str = f"{best_epoch:06d}"
        logger.debug(f"best_epoch: {best_epoch} / '{best_epoch_str}'")

        with get_db_context() as db:
            character_id = kwargs["select_character_id"]
            logger.debug(f"character_id: {character_id}")

            character = crud.character.sync.get(db=db, id=character_id)
            logger.debug(f"character: {character.id} / {character.name}")

            sd_checkpoint_id = kwargs["select_sd_checkpoint_id"]
            logger.debug(f"sd_checkpoint_id: {sd_checkpoint_id}")

            sd_checkpoint = crud.sd_checkpoint.sync.get(db=db, id=sd_checkpoint_id)
            logger.debug(f"sd_checkpoint: {sd_checkpoint.id} / {sd_checkpoint.name}")
            base_checkpoint_name = sd_checkpoint.sd_base_model.name.lower()

        # Glob all .safetensors files in the output directory
        safetensor_files = glob.glob(str(Path(OUTPUTS_KOHYA_SS_PATH) / "*.safetensors"))
        logger.debug(f"Found {len(safetensor_files)} .safetensors files in {OUTPUTS_KOHYA_SS_PATH}")

        # Find the best epoch file
        best_epoch_file_path = self._get_best_epoch_file_path(
            lora_output_name=lora_output_name,
            best_epoch_str=best_epoch_str,
            safetensor_files=safetensor_files,
        )

        # Move the best epoch to the hub (placeholder)
        best_epoch_file_path = self._move_best_epoch_to_hub(
            best_epoch_file_path=best_epoch_file_path,
            checkpoint_name=sd_checkpoint.name,
            base_checkpoint_name=base_checkpoint_name,
            is_known=character.is_known,
        )

        # Delete all other epochs for this lora_output_name
        deleted_paths = self._delete_old_epochs(
            lora_output_name=lora_output_name,
            best_epoch_file_path=best_epoch_file_path,
            safetensor_files=safetensor_files,
        )

        # Create a Job in LOCAL to download the epoch from the cloud hub to local hub (placeholder)
        job_id = self._create_local_job_to_dl_epoch_from_hub(best_epoch_file_path)

        return scripts.ScriptOutput(
            success=True,
            message="Best epoch file was moved to hub and all other epochs were deleted.",
            data={
                "best_epoch_file_path": best_epoch_file_path,
                "deleted_paths": deleted_paths,
            },
        )
