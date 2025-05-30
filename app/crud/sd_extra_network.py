import json
from pathlib import Path

from sqlmodel import Session

from app import models
from app.paths import HUB_MODELS_PATH

from .base import BaseCRUD


class SDExtraNetworkCRUD(
    BaseCRUD[
        models.SDExtraNetwork,
        models.SDExtraNetworkCreate,
        models.SDExtraNetworkUpdate,
    ]
):
    """CRUD operations for SDExtraNetwork."""

    async def get_by_lora_sha256(self, db: Session, sha256: str) -> models.SDExtraNetwork | None:
        return await self.get_or_none(db, lora_sha256=sha256)

    async def attempt_to_get_sha256(self, db: Session, id: str) -> str | None:
        sd_extra_network = await self.get(db, id=id)

        if sd_extra_network.lora_sha256:
            return sd_extra_network.lora_sha256

        if sd_extra_network.safetensors_name:
            # Search for all files in HUB_MODELS_PATH that match the safetensors_name
            list_of_files_with_safetensors_name = list(
                HUB_MODELS_PATH.rglob(f"**/{sd_extra_network.safetensors_name}.safetensors")
            )

            # If there is only one file, try to find the sha256 in the json file
            if len(list_of_files_with_safetensors_name) == 1:
                safetensors_json_path = Path(
                    str(list_of_files_with_safetensors_name[0]).replace(".safetensors", ".json")
                )
                if safetensors_json_path.exists():
                    with open(safetensors_json_path) as f:
                        json_data = json.load(f)

                        # Update the sha256
                        lora_sha256 = json_data.get("sha256")

                        # Save the changes
                        if lora_sha256:
                            return str(lora_sha256)
                return None

            # If there are multiple files, raise an error
            if len(list_of_files_with_safetensors_name) > 1:
                raise ValueError(
                    f"Found multiple files with the name {sd_extra_network.safetensors_name}"
                )

        raise ValueError(f"No file found with the name {sd_extra_network.safetensors_name}")


sd_extra_network = SDExtraNetworkCRUD(model=models.SDExtraNetwork)
