import base64
import os
from datetime import datetime, timezone
from typing import Any

from app import logger, paths
from app.services.a1111_wrapper import RisaA1111Wrapper, Text2ImgSettings
from framework.services import scripts


class ScriptGenerateXYForLoraEpochs(scripts.Script):
    """
    This script generates a XY plot for a Lora Model.

    It used after training a Lora Model to generate a XY plot of the training epochs.

    It uses the following parameters:
    - Epochs: 9-30
    """

    def _validate_input(self, *args: Any, **kwargs: Any) -> bool:
        return True

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        logger.debug("Starting ScriptGenerateXYForLoraEpochs._run()")
        logger.debug(f"kwargs: {kwargs}")

        risa_a1111_wrapper = RisaA1111Wrapper()
        logger.debug(f"risa_a1111_wrapper: {risa_a1111_wrapper}")

        text2img_settings = Text2ImgSettings(**kwargs)
        logger.debug(f"text2img_settings: {text2img_settings}")

        sd_checkpoint_id = str(kwargs["sd_checkpoint_id"])
        logger.debug(f"sd_checkpoint_id: {sd_checkpoint_id}")

        lora_output_name = str(kwargs["lora_output_name"])
        logger.debug(f"lora_output_name: {lora_output_name}")

        start_epoch = int(kwargs.get("start_epoch", 9))
        logger.debug(f"start_epoch: {start_epoch}")

        end_epoch = int(kwargs.get("end_epoch", 30))
        logger.debug(f"end_epoch: {end_epoch}")

        max_epochs = int(kwargs.get("max_epochs", 30))
        logger.debug(f"max_epochs: {max_epochs}")

        seeds_per_epoch = int(kwargs.get("seeds_per_epoch", 1))
        logger.debug(f"seeds_per_epoch: {seeds_per_epoch}")

        character_id = kwargs.get("character_id")
        logger.debug(f"character_id: {character_id}")

        logger.info("Calling risa_a1111_wrapper.gen_xy_each_epoch_in_range()")

        response = risa_a1111_wrapper.gen_xy_each_epoch_in_range(
            sd_checkpoint_id=sd_checkpoint_id,
            lora_output_name=lora_output_name,
            text2img_settings=text2img_settings,
            start_epoch=start_epoch,
            end_epoch=end_epoch,
            max_epochs=max_epochs,
            seeds_per_epoch=seeds_per_epoch,
            character_id=character_id,
        )

        images_data = response["images"]

        image_paths = []

        output_folder = paths.OUTPUTS_PATH / "risa" / "scripts" / "generate_xy_for_lora_epochs"
        output_folder.mkdir(parents=True, exist_ok=True)

        for i, image_data in enumerate(images_data):
            # Convert base64 to png file
            timestamp = datetime.now(timezone.utc).strftime("%y%m%d-%H%M%S")
            image_filename = f"{timestamp}__{lora_output_name}__{start_epoch}-{end_epoch}.png"
            image_path = os.path.join(output_folder, image_filename)
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            image_paths.append(image_path)

        return scripts.ScriptOutput(
            success=True,
            message=f"Image saved to {image_path}",
            data={
                "image_path": image_path,
                "image_paths": image_paths,
            },
        )
