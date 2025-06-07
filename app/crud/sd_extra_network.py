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

    async def get_by_sha256(self, db: Session, sha256: str) -> models.SDExtraNetwork | None:
        """Get an SD Extra Network by its SHA256 hash."""
        return await self.get_or_none(db, sha256=sha256)

    async def attempt_to_get_sha256(self, db: Session, id: str) -> str | None:
        """Attempt to get the SHA256 hash for an SD Extra Network, first from the DB, then from the filesystem."""
        sd_extra_network = await self.get(db, id=id)

        if sd_extra_network.sha256:
            return sd_extra_network.sha256

        if sd_extra_network.safetensors:
            safetensors_name = sd_extra_network.safetensors.name
            if not safetensors_name:
                raise ValueError(f"Safetensor for {id} has no name.")

            # Search for all files in HUB_MODELS_PATH that match the safetensors_name
            list_of_files_with_safetensors_name = list(
                HUB_MODELS_PATH.rglob(f"**/{safetensors_name}.safetensors")
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
                        sha256_from_json = json_data.get("sha256")

                        # Save the changes
                        if sha256_from_json:
                            return str(sha256_from_json)
                return None

            # If there are multiple files, raise an error
            if len(list_of_files_with_safetensors_name) > 1:
                raise ValueError(f"Found multiple files with the name {safetensors_name}")

            raise ValueError(f"No file found with the name {safetensors_name}")

        raise ValueError(f"SDExtraNetwork {id} has no safetensors file associated.")


sd_extra_network = SDExtraNetworkCRUD(model=models.SDExtraNetwork)
