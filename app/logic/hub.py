import re
from pathlib import Path


def fix_civitai_download_filenames(path: Path) -> dict[str, int]:
    """Recursively search through all files in the hub path and remove filename suffixes that end with an underscore followed by 6 or 7 digits, before any extension(s).

    Args:
        path: The root directory to search (as a pathlib.Path object).
    """
    # Matches an underscore followed by 6 or 7 digits before a dot or end of string
    pattern = re.compile(r"_(\d{6,7})(?=\.|$)")
    total_renamed = 0
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
                file.rename(new_path)
                total_renamed += 1
    return {
        "success": True,
        "total_renamed": total_renamed,
    }
