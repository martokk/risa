from abc import abstractmethod
from typing import Any

from pydantic import BaseModel


class ScriptOutput(BaseModel):
    success: bool | None = None
    message: str | None = None
    data: Any | None = None


class Script(BaseModel):
    # Input (Any or None)

    # Output
    output: ScriptOutput | None = None

    # Run
    @abstractmethod
    def _validate_input(self, *args: Any, **kwargs: Any) -> bool:
        pass

    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> ScriptOutput:
        pass

    def run(self, *args: Any, **kwargs: Any) -> ScriptOutput:
        if not self._validate_input(*args, **kwargs):
            raise ValueError("Script input validation failed.")

        self.output = self._run(*args, **kwargs)
        return self.output


class ExampleScript(Script):
    """
    This example inputs a number and doubles it.

    """

    def _validate_input(self, num: Any) -> bool:
        if not num:
            raise ValueError("Script Validation Error: A input value is required for `num`.")

        if not isinstance(num, int):
            raise ValueError("Script Validation Error: `num` must be an integer.")

        if num < 0:
            raise ValueError("Script Validation Error: `num` must be greater than 0.")

        return True

    def _run(self, num: int) -> ScriptOutput:
        return ScriptOutput(
            success=True,
            message=f"The number {num} doubled is {num * 2}.",
            data={"doubled_num": num * 2},
        )


class ScriptGenerateXYForLoraEpochs(Script):
    """
    This script generates a XY plot for a Lora Model.

    It used after training a Lora Model to generate a XY plot of the training epochs.

    It uses the following parameters:
    - Epochs: 9-30
    """

    def _validate_input(self, *args: Any, **kwargs: Any) -> bool:
        return True

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        import requests

        payload = {
            "prompt": "<lora:ashley_pasco_cyberrealisticPony_v110_1-000009:1> ashleyp, smile, 1girl",
            "negative_prompt": "",
            "styles": ["general"],
            "steps": 20,
            "cfg_scale": 7,
            "width": 512,
            "height": 512,
            "seed": -1,
            "script_name": "x/y/z plot",
            "script_args": [
                1,  # x_type (Seed)
                "-1,-1,-1,-1,-1,-1",
                [],  # x_values_dropdown
                7,  # y_type (Prompt S/R)
                "-000009,-000010",
                [],  # y_values_dropdown
                0,  # z_type (Nothing)
                "",
                [],  # z_values_dropdown
                True,  # draw_legend
                False,  # include_lone_images
                False,  # include_sub_grids
                False,  # no_fixed_seeds
                False,  # vary_seeds_x
                False,  # vary_seeds_y
                False,  # vary_seeds_z
                0,  # margin_size
                False,  # csv_mode
            ],
        }

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

        response = requests.post("http://127.0.0.1:3001/sdapi/v1/txt2img", json=payload)
        response.raise_for_status()

        image_data = response.json()["images"][0]

        # Save the result
        image_path = "/workspace/__OUTPUTS__/xy_output_test.png"
        with open(image_path, "wb") as f:
            f.write(image_data.encode("latin1"))

        return ScriptOutput(
            success=True,
            message=f"Image saved to {image_path}",
            data={
                "image_path": image_path,
            },
        )
