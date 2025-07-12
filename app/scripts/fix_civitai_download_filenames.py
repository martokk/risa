import re
from pathlib import Path
from typing import Any

from app import logger
from vcore.backend.services import scripts


class ScriptFixCivitaiDownloadFilenames(scripts.Script):
    """
    This script fixes the filenames of models downloaded by the Civitai Extension for A1111.

    It removes the 6 or 7 digit model id from the end of the filename.
    """

    def _validate_input(self, *args: Any, **kwargs: Any) -> bool:
        return True

    def _fix_civitai_download_filenames(self, path: Path | str) -> list[str]:
        """Recursively search through all files in the hub path and remove filename suffixes that end with an underscore followed by 6 or 7 digits, before any extension(s).

        Args:
            path: The root directory to search (as a pathlib.Path object).
        """
        path = Path(path)
        # Matches an underscore followed by 6 or 7 digits before a dot or end of string
        pattern = re.compile(r"_(\d{6,7})(?=\.|$)")
        total_renamed = 0
        messages = []
        for file in path.glob("**/*"):
            if file.is_file():
                # Split name into base and all suffixes
                base, *suffixes = file.name.split(".")
                match = pattern.search(base)
                if match:
                    new_base = pattern.sub("", base)
                    # Reconstruct the filename with all suffixes
                    new_name = new_base + ("." + ".".join(suffixes) if suffixes else "")
                    new_path = file.with_name(new_name)

                    message = f"Renamed {file.name} --> {new_name}"
                    logger.debug(message)
                    messages.append(message)
                    file.rename(new_path)
                    total_renamed += 1
        return messages

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

        hub_path = kwargs["hub_path"]
        logger.debug(f"hub_path: {hub_path}")

        messages = self._fix_civitai_download_filenames(path=hub_path)

        return scripts.ScriptOutput(
            success=True,
            message="Fix Civitai Download Filenames",
            data=messages,
        )
