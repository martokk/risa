from app.scripts.choose_best_epoch import ScriptChooseBestEpoch
from app.scripts.fix_civitai_download_filenames import ScriptFixCivitaiDownloadFilenames
from app.scripts.generate_xy_for_lora_epochs import ScriptGenerateXYForLoraEpochs
from app.scripts.rsync_files import ScriptRsyncFiles
from vcore.backend.services.scripts import Script


def hook_get_script_class_from_class_name(script_class_name: str) -> type[Script]:
    if script_class_name == "ScriptGenerateXYForLoraEpochs":
        return ScriptGenerateXYForLoraEpochs
    if script_class_name == "ScriptChooseBestEpoch":
        return ScriptChooseBestEpoch
    if script_class_name == "ScriptFixCivitaiDownloadFilenames":
        return ScriptFixCivitaiDownloadFilenames
    if script_class_name == "ScriptRsyncFiles":
        return ScriptRsyncFiles
    raise ValueError(
        f"Unknown script class name: {script_class_name}. Hint: if you just added a new script, you need to add it to the hook_get_script_class_from_class_name function."
    )
