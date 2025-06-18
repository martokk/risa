from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.logic.hub import fix_civitai_download_filenames


router = APIRouter()


class FixCivitaiRequest(BaseModel):
    hub_path: str


@router.post("/tools/fix-civitai-download-filenames", response_class=JSONResponse)
async def fix_civitai_download_filenames_api(request: FixCivitaiRequest) -> JSONResponse:
    """API endpoint to fix Civitai download filenames in a given hub directory.

    Args:
        request: Request body containing the hub_path (string)

    Returns:
        JSON response with the result of the operation
    """
    try:
        path = Path(request.hub_path)
        if not path.exists() or not path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided hub_path does not exist or is not a directory.",
            )
        result = fix_civitai_download_filenames(path=path)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fixing filenames: {str(e)}",
        )
