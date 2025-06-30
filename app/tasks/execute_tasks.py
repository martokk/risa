from app.scripts.choose_best_epoch import ScriptChooseBestEpoch
from app.scripts.generate_xy_for_lora_epochs import ScriptGenerateXYForLoraEpochs
from framework.services.scripts import Script


def hook_get_script_class_from_class_name(script_class_name: str) -> type[Script]:
    if script_class_name == "ScriptGenerateXYForLoraEpochs":
        return ScriptGenerateXYForLoraEpochs
    if script_class_name == "ScriptChooseBestEpoch":
        return ScriptChooseBestEpoch
    raise ValueError(f"Unknown script class name: {script_class_name}")
