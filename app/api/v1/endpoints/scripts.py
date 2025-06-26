"""
API endpoints for managing the job queue.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from framework.routes.restrict_to_env import restrict_to
from framework.services.scripts import ScriptGenerateXYForLoraEpochs


router = APIRouter()


@router.post("/scripts/generate-xy-for-lora-epochs")
@restrict_to("playground")
async def generate_xy_for_lora_epochs() -> JSONResponse:
    script_output = ScriptGenerateXYForLoraEpochs().run(
        start_epoch=9,
        end_epoch=30,
        images_per_epoch=8,
        lora_model_name="ashley_pasco_cyberrealisticPony_v110_1",
        character_id="ashley_pasco",
        sd_checkpoint="cyberrealisticPony_v110",
    )

    status = 200 if script_output.success else 400
    return JSONResponse(content=script_output.model_dump(), status_code=status)
