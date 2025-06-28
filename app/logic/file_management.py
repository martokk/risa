import glob
import os


def get_trained_lora_output_names() -> list[str]:
    """Get all files from the /workspace/__OUTPUTS__/kohya_ss/ folder that end with .safetensors."""
    files = glob.glob("/workspace/__OUTPUTS__/kohya_ss/*.safetensors")

    # Drop the dash and numbers and return the remaining string. There sill likely be duplicates, so we return a list of unique strings.
    lora_output_names = [os.path.basename(file).split("-")[0] for file in files]

    # Get unique lora output names.
    unique_lora_output_names = list(set(lora_output_names))

    # Return the list of unique strings.
    return unique_lora_output_names
