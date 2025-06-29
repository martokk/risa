from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, Field

from app import crud, logger
from app.models.sd_checkpoint import SDCheckpoint
from framework.core.db import get_db_context


class Text2ImgSettings(BaseModel):
    prompt: str = Field(default="")
    negative_prompt: str = Field(default="")
    styles: list[str] = Field(default_factory=list)
    sampler_name: str = Field(default="Euler a")
    seed: int = Field(default=-1)
    steps: int = Field(default=20)
    cfg_scale: float = Field(default=7.0)
    width: int = Field(default=768)
    height: int = Field(default=768)
    batch_size: int = Field(default=1)
    n_iter: int = Field(default=1)
    restore_faces: bool = Field(default=False)
    tiling: bool = Field(default=False)
    enable_hr: bool = Field(default=False)
    override_settings: dict[str, Any] = Field(default_factory=dict)
    script_name: str = Field(default="")
    script_args: list[Any] = Field(default_factory=list)


class XYPlotSettings(BaseModel):
    """
    def run(self, p, x_type, x_values, x_values_dropdown, y_type, y_values, y_values_dropdown, z_type, z_values, z_values_dropdown, draw_legend, include_lone_images, include_sub_grids, no_fixed_seeds, vary_seeds_x, vary_seeds_y, vary_seeds_z, margin_size, csv_mode):

    """

    x_type: int = Field(default=1)  # 1=Seed
    x_values: str = Field(default="-1,-1")
    x_values_dropdown: list[str] = Field(default_factory=list)

    y_type: int = Field(default=7)  # 7=Prompt S/R
    y_values: str = Field(default=",")
    y_values_dropdown: list[str] = Field(default_factory=list)

    z_type: int = Field(default=0)
    z_values: str = Field(default="")
    z_values_dropdown: list[str] = Field(default_factory=list)

    draw_legend: bool = Field(default=True)
    include_lone_images: bool = Field(default=False)
    include_sub_grids: bool = Field(default=False)
    no_fixed_seeds: bool = Field(default=False)
    vary_seeds_x: bool = Field(default=False)
    vary_seeds_y: bool = Field(default=False)
    vary_seeds_z: bool = Field(default=False)
    margin_size: int = Field(default=0)
    csv_mode: bool = Field(default=False)


class A1111Wrapper:
    """
    A wrapper for the A1111 API.
    """

    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url
        self.session = requests.Session()
        logger.debug(f"A1111Wrapper initialized with base_url: {self.base_url}")

    def post(self, endpoint: str, payload: dict) -> Any:
        url = f"{self.base_url}/{endpoint}"

        try:
            resp = self.session.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error posting to {url}: {e}")
            raise e

    def get(self, endpoint: str) -> Any:
        url = f"{self.base_url}/{endpoint}"

        try:
            resp = self.session.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error getting from {url}: {e}")
            raise e

    def generate_txt2img(self, text2img_settings: Text2ImgSettings) -> Any:
        payload = text2img_settings.dict()
        logger.info(f"Generating txt2img with payload: {payload}")
        return self.post("sdapi/v1/txt2img", payload)

    def generate_xy_plot(
        self,
        checkpoint_path: str,
        text2img_settings: Text2ImgSettings,
        xy_plot_settings: XYPlotSettings | None = None,
    ) -> Any:
        self.set_checkpoint(checkpoint_path=checkpoint_path)

        xy_plot_settings = xy_plot_settings or XYPlotSettings()

        payload = text2img_settings.model_dump()
        payload["script_name"] = "x/y/z plot"
        payload["script_args"] = xy_plot_settings.model_dump()
        logger.info(f"Generating xy plot with payload: {payload}")

        try:
            return self.post("sdapi/v1/txt2img", payload)
        except Exception as e:
            logger.error(f"Error generating xy plot: {e}")
            raise e

    def list_checkpoints(self) -> Any:
        try:
            return self.get("sdapi/v1/sd-models")
        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}")
            raise e

    def set_checkpoint(self, checkpoint_path: str) -> Any:
        """
        Example:
        "pony/cyberrealisticPony_v110"
        """
        logger.info(f"Attempting to set checkpoint to: {checkpoint_path}")
        try:
            self.post("sdapi/v1/options", {"sd_model_checkpoint": checkpoint_path})
        except Exception as e:
            logger.error(f"Error setting checkpoint: {e}")
            raise e

        # Validate
        active_checkpoint = self.get_current_checkpoint()
        if active_checkpoint != checkpoint_path:
            logger.error(
                f"Failed to set checkpoint. Active checkpoint is {active_checkpoint} but expected {checkpoint_path}"
            )
            raise ValueError(
                f"Failed to set checkpoint. Active checkpoint is {active_checkpoint} but expected {checkpoint_path}"
            )

        logger.info(f"Successfully set checkpoint to: {checkpoint_path}")

    def get_current_checkpoint(self) -> str:
        try:
            options = self.get("sdapi/v1/options")
        except Exception as e:
            logger.error(f"Error getting current checkpoint: {e}")
            raise e

        return str(options.get("sd_model_checkpoint", ""))


class RisaA1111Wrapper(A1111Wrapper):
    """
    A wrapper for the A1111 API.
    """

    def _convert_range_to_comma_separated_string(
        self, start_epoch: int, end_epoch: int, max_epochs: int
    ) -> str:
        prompt_sr_list = [f"-{i:06d}" for i in range(start_epoch, end_epoch)]

        if end_epoch == max_epochs:
            prompt_sr_list.pop(-1)

        prompt_sr_str = ",".join(prompt_sr_list)

        if end_epoch == max_epochs:
            prompt_sr_str += ","

        return prompt_sr_str

    def _convert_seeds_per_epoch_to_comma_separated_string(self, seeds_per_epoch: int) -> str:
        return ",".join(["-1" for i in range(seeds_per_epoch)])

    def _convert_sd_checkpoint_to_checkpoint_path(self, sd_checkpoint: SDCheckpoint) -> str:
        if not sd_checkpoint.local_file_path:
            raise ValueError(
                "SDCheckpoint.local_file_path is required to convert to checkpoint path. There is room for improvement here."
            )

        sdcp_local_file_path = Path(sd_checkpoint.local_file_path)
        return f"{sdcp_local_file_path.parent}/{sdcp_local_file_path.name}"

    def _convert_sd_checkpoint_id_to_checkpoint_path(self, sd_checkpoint_id: str) -> str:
        with get_db_context() as db:
            sd_checkpoint = crud.sd_checkpoint.sync.get(db, id=sd_checkpoint_id)
        return self._convert_sd_checkpoint_to_checkpoint_path(sd_checkpoint=sd_checkpoint)

    def gen_xy_each_epoch_in_range(
        self,
        sd_checkpoint_id: str,
        lora_output_name: str,
        text2img_settings: Text2ImgSettings,
        start_epoch: int,
        end_epoch: int,
        max_epochs: int,
        seeds_per_epoch: int,
        character_id: str | None,
    ) -> Any:
        """Will generate a XY plot for each epoch of the Lora Model in the range."""

        logger.debug("Starting RisaA1111Wrapper.gen_xy_each_epoch_in_range()")

        checkpoint_path = self._convert_sd_checkpoint_id_to_checkpoint_path(
            sd_checkpoint_id=sd_checkpoint_id
        )

        logger.debug(f"checkpoint_path: {checkpoint_path}")

        xy_plot_settings = XYPlotSettings(
            x_type=1,  # 1=Seed
            x_values=self._convert_seeds_per_epoch_to_comma_separated_string(seeds_per_epoch),
            y_type=7,  # 7=Prompt S/R
            y_values=self._convert_range_to_comma_separated_string(
                start_epoch, end_epoch, max_epochs
            ),
        )

        logger.debug(f"xy_plot_settings: {xy_plot_settings}")

        logger.debug(f"text2img_settings: {text2img_settings}")

        return self.generate_xy_plot(
            checkpoint_path=checkpoint_path,
            text2img_settings=text2img_settings,
            xy_plot_settings=xy_plot_settings,
        )
