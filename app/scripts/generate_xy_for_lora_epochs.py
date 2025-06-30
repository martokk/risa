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

    def _parse_selected_epochs(self, selected_epochs_str: str) -> list[int]:
        selected_epochs_str_list = selected_epochs_str.split(",")

        selected_epochs: list[int] = []
        if selected_epochs_str_list:
            selected_epochs = [int(epoch) for epoch in selected_epochs_str_list]

        return selected_epochs

    def _add_lora_and_trigger_to_prompt(
        self, prompt: str, start_epoch: int, lora_output_name: str, trigger: str, lora_weight: float
    ) -> str:
        return f"<lora:{lora_output_name}-{start_epoch:06d}:{lora_weight}> {trigger}, {prompt}"

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        logger.debug("Starting ScriptGenerateXYForLoraEpochs._run()")
        logger.debug(f"kwargs: {kwargs}")

        risa_a1111_wrapper = RisaA1111Wrapper()
        logger.debug(f"risa_a1111_wrapper: {risa_a1111_wrapper}")

        text2img_settings = Text2ImgSettings(**kwargs)
        logger.debug(f"text2img_settings: {text2img_settings}")

        lora_output_name = str(kwargs["lora_output_name"])
        logger.debug(f"lora_output_name: {lora_output_name}")

        character_id = kwargs.get("character_id")
        logger.debug(f"character_id: {character_id}")

        sd_checkpoint_id = str(kwargs["sd_checkpoint_id"])
        logger.debug(f"sd_checkpoint_id: {sd_checkpoint_id}")

        trigger = str(kwargs["trigger"])
        logger.debug(f"trigger: {trigger}")

        lora_weight = float(kwargs.get("lora_weight", 1.0))
        logger.debug(f"lora_weight: {lora_weight}")

        start_epoch = int(kwargs.get("start_epoch", 9))
        logger.debug(f"start_epoch: {start_epoch}")

        max_epochs = int(kwargs.get("max_epochs", 30))
        logger.debug(f"max_epochs: {max_epochs}")

        epoch_selection = str(kwargs.get("epoch_selection", "off"))
        logger.debug(f"epoch_selection: {epoch_selection}")

        end_epoch = int(kwargs.get("end_epoch", 30))
        logger.debug(f"end_epoch: {end_epoch}")

        selected_epochs_str = kwargs.get("selected_epochs", "")
        selected_epochs = self._parse_selected_epochs(selected_epochs_str=selected_epochs_str)
        logger.debug(f"selected_epochs: {selected_epochs}")

        seeds_per_epoch = int(kwargs.get("seeds_per_epoch", 1))
        logger.debug(f"seeds_per_epoch: {seeds_per_epoch}")

        prompt = str(kwargs.get("prompt", ""))
        prompt = self._add_lora_and_trigger_to_prompt(
            prompt=prompt,
            start_epoch=start_epoch,
            lora_output_name=lora_output_name,
            trigger=trigger,
            lora_weight=lora_weight,
        )
        logger.debug(f"prompt: {prompt}")

        logger.info("Calling risa_a1111_wrapper.generate_xy_for_lora_epochs()")

        response = risa_a1111_wrapper.generate_xy_for_lora_epochs(
            character_id=character_id,
            sd_checkpoint_id=sd_checkpoint_id,
            start_epoch=start_epoch,
            max_epochs=max_epochs,
            epoch_selection=epoch_selection,
            end_epoch=end_epoch,
            selected_epochs=selected_epochs,
            seeds_per_epoch=seeds_per_epoch,
            prompt=prompt,
            text2img_settings=text2img_settings,
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
