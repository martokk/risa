from typing import Any

from app import logger
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

        logger.debug(f"response: {response}")

        # payload = {
        #     "prompt": "woman",
        #     "negative_prompt": "",
        #     "steps": 25,
        #     "cfg_scale": 7,
        #     "width": 512,
        #     "height": 512,
        #     "seed": -1,
        #     "script_name": "x/y/z plot",
        #     "script_args": [
        #         1,  # x_type (Seed)
        #         "-1,-1,-1,-1,-1,-1",
        #         [],  # x_values_dropdown
        #         7,  # y_type (Prompt S/R)
        #         "-000009,-000010,-000011,-000012,-000013,-000014,-000015,-000016,-000017,-000018,-000019,-000020,-000021,-000022,-000023,-000024,-000025,-000026,-000027,-000028,-000029,",
        #         [],  # y_values_dropdown
        #         0,  # z_type (Nothing)
        #         "",
        #         [],  # z_values_dropdown
        #         True,  # draw_legend
        #         False,  # include_lone_images
        #         False,  # include_sub_grids
        #         False,  # no_fixed_seeds
        #         False,  # vary_seeds_x
        #         False,  # vary_seeds_y
        #         False,  # vary_seeds_z
        #         0,  # margin_size
        #         False,  # csv_mode
        #     ],
        # }

        # response = requests.post(
        #     "http://127.0.0.1:3001/sdapi/v1/txt2img", json=a1111_payload.model_dump_json()
        # )
        # response.raise_for_status()

        images_data = response.json()["images"]

        image_paths = []

        for i, image_data in enumerate(images_data):
            image_path = f"/workspace/__OUTPUTS__/xy_output_{i}.png"
            with open(image_path, "wb") as f:
                f.write(image_data.encode("latin1"))
            image_paths.append(image_path)

        return scripts.ScriptOutput(
            success=True,
            message=f"Image saved to {image_path}",
            data={
                "image_path": image_path,
                "image_paths": image_paths,
            },
        )
