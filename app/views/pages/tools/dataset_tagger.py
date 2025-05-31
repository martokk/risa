# noqa: E501
# Pydantic models (as per feature document Sections 7.1, 7.2)


import os
from pathlib import Path
from typing import Annotated, Any

import yaml
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel, Field
from sqlmodel import Session
from starlette.templating import _TemplateResponse

from app import crud
from app.core.db import get_db
from app.paths import DATASET_TAGGER_WALKTHROUGH_PATH
from app.views.templates import templates
from app.views.templates.context import get_template_context


class WalkthroughStep(BaseModel):
    name: str
    description: str
    manual_inputs: list[dict[str, str]] | None = Field(default_factory=lambda: [])
    automatic_inputs: list[str] | None = Field(default_factory=lambda: [])
    character_tags: list[str] | None = Field(default_factory=lambda: [])


class WalkthroughConfig(BaseModel):
    tagging_notes: str
    steps: list[WalkthroughStep]


class TaggingWorkflowState(BaseModel):
    character_id: str
    folder_path: str
    current_step_index: int = 0
    current_input_type_index_in_step: int = (
        0  # 0:manual_inputs, 1:pending_manual_tags, 2:automatic_inputs, 3:character_tags
    )
    current_item_index_within_input_type: int = 0
    pending_tags_from_last_manual_input: list[str] = Field(default_factory=lambda: [])
    active_manual_input_key: str | None = None


# Main router for the Dataset Tagging Assistant tool.
router = APIRouter(
    prefix="/tools/dataset-tagger",
    tags=["tools_dataset_tagger"],
)


@router.get("/setup", response_class=HTMLResponse)
async def get_dataset_tagger_setup_page(
    request: Request,
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
    selected_character_id: str | None = Query(default=None),
) -> HTMLResponse:
    characters = await crud.character.get_all(db)
    context["characters"] = characters
    context["selected_character_id"] = selected_character_id
    return templates.TemplateResponse("tools/dataset_tagger/setup_form.html", context)


@router.post("/setup")
async def post_dataset_tagger_setup(
    request: Request,
    character_id: Annotated[str, Form()],
    folder_path: Annotated[str, Form()],
    context: dict[str, Any] = Depends(get_template_context),
    db: Session = Depends(get_db),
) -> Response:
    # Basic Validation
    if (
        not folder_path
        or not folder_path.strip()
        or folder_path
        == "/media/martokk/FILES/AI/datasets/CHARACTER_FOLDER/training_images/x_woman"
    ):
        context["characters"] = await crud.character.get_all(db)
        context["error_message"] = "Folder path cannot be empty or the default path."
        context["selected_character_id"] = character_id

        # Re-render the form with an error message
        return templates.TemplateResponse(
            "tools/dataset_tagger/setup_form.html",
            context,
            status_code=400,
        )

    # Path validation (as per feature doc: optional to skip for LLM first pass, but good to include)
    path_obj = Path(folder_path)
    if not path_obj.is_dir():
        context["characters"] = await crud.character.get_all(db)
        context["error_message"] = f"Folder not found or is not a directory: {folder_path}"
        context["selected_character_id"] = character_id
        return templates.TemplateResponse(
            "tools/dataset_tagger/setup_form.html",
            context,
            status_code=400,
        )

    redirect_url = (
        f"/tools/dataset-tagger/workflow?character_id={character_id}&folder_path={folder_path}"
    )
    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/image-proxy", response_class=FileResponse)
async def get_image_proxy(
    request: Request, folder: str = Query(...), filename: str = Query(...)
) -> FileResponse:
    # Security: Prevent path traversal attacks
    # Ensure the requested folder is absolute and a directory.
    # The base_path should be the user-provided folder_path from the workflow state.
    # For this proxy, we directly use the 'folder' query parameter which should be the validated folder_path.

    base_dir = Path(folder).resolve()
    requested_path = (base_dir / filename).resolve()

    # Check if the resolved path is within the resolved base_dir
    if not base_dir.is_dir():
        raise HTTPException(status_code=400, detail="Invalid base folder path provided.")

    if not requested_path.is_file():
        raise HTTPException(
            status_code=404, detail=f"Image not found: {filename}"
        )  # Changed from 400 to 404

    # Ensure the requested path is actually within the base_dir to prevent traversal
    if (
        base_dir not in requested_path.parents and requested_path != base_dir
    ):  # Check if base_dir is a parent of requested_path
        # This secondary check might be too strict if filename itself contains '..' but resolves within.
        # A better check is to see if requested_path starts with base_dir string representation after resolving both.
        pass  # Primary check is below with commonprefix

    # A more robust check for path traversal:
    # After resolving both, the requested_path must start with the base_dir path string.
    if os.path.commonprefix([str(requested_path), str(base_dir)]) != str(base_dir):
        raise HTTPException(status_code=403, detail="Forbidden: Path traversal attempt detected.")

    # Check for allowed image types if necessary (optional, for added security)
    allowed_extensions = [".png", ".jpg", ".jpeg", ".webp"]
    if requested_path.suffix.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid image type.")

    return FileResponse(str(requested_path))


@router.get("/workflow", response_class=HTMLResponse)
async def get_dataset_tagger_workflow_page(
    request: Request,
    character_id: str = Query(...),
    folder_path: str = Query(...),
    # db: Session = Depends(get_db) # Will be needed later for character tags
    context: dict[str, Any] = Depends(get_template_context),
) -> _TemplateResponse:
    # 1. Initialize TaggingWorkflowState (using data from query params)
    initial_state = TaggingWorkflowState(
        character_id=character_id,
        folder_path=folder_path,
        # Other fields will use Pydantic defaults (0, [], None)
    )

    # 2. Load walkthrough.yaml
    walkthrough_config_path = DATASET_TAGGER_WALKTHROUGH_PATH
    walkthrough_config: WalkthroughConfig | None = None
    if walkthrough_config_path.is_file():
        with open(walkthrough_config_path) as f:
            try:
                yaml_data = yaml.safe_load(f)
                walkthrough_config = WalkthroughConfig(**yaml_data)
            except yaml.YAMLError as e:
                # Handle YAML parsing error - render page with error
                # For now, raise HTTPException, but ideally render error in template
                raise HTTPException(
                    status_code=500, detail=f"Error parsing walkthrough.yaml: {e}"
                ) from e
            except Exception as e:  # Catches Pydantic validation errors too
                raise HTTPException(
                    status_code=500, detail=f"Error loading walkthrough config: {e}"
                ) from e
    else:
        raise HTTPException(status_code=500, detail="walkthrough.yaml not found.")

    if not walkthrough_config:  # Should be caught above, but as a safeguard
        raise HTTPException(status_code=500, detail="Failed to load walkthrough configuration.")

    # 3. List image files
    image_files: list[str] = []
    allowed_extensions = (".png", ".jpg", ".jpeg", ".webp")
    try:
        p_folder_path = Path(folder_path)
        if p_folder_path.is_dir():
            image_files = sorted(
                [
                    f.name
                    for f in p_folder_path.iterdir()
                    if f.is_file() and f.suffix.lower() in allowed_extensions
                ]
            )
        else:
            # Handle case where folder_path is not a dir (should be caught in setup, but good practice)
            # Render page with error or raise
            raise HTTPException(
                status_code=400, detail=f"Provided path is not a directory: {folder_path}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing image files: {e}") from e

    # If no images found, still proceed but image grid will be empty
    # A message could be added to context if image_files is empty.

    # 4. Simplified First Item Display Logic for Phase 2
    initial_display_item: str = "Walkthrough loaded. Ready to start (full logic pending)."
    initial_item_type: str = "info"  # Placeholder type
    initial_step_name: str | None = None
    initial_step_description: str | None = None

    if walkthrough_config.steps:
        first_step = walkthrough_config.steps[0]
        initial_step_name = first_step.name
        initial_step_description = first_step.description

        if first_step.manual_inputs and first_step.manual_inputs[0]:
            # Get the question from the first manual_input dictionary
            initial_display_item = list(first_step.manual_inputs[0].values())[0]
            initial_item_type = "manual_question"
        elif first_step.automatic_inputs and first_step.automatic_inputs[0]:
            initial_display_item = first_step.automatic_inputs[0]
            initial_item_type = "tag"
        elif first_step.character_tags and first_step.character_tags[0]:
            # For Phase 2, we just show the category name, not the resolved tag yet
            initial_display_item = f"Character Tag Category: {first_step.character_tags[0]}"
            initial_item_type = "tag"  # Treat as a tag for display purposes for now
        elif len(walkthrough_config.steps) == 1:  # Only one step, might be empty
            initial_display_item = "First step is defined but has no processable items."
            initial_item_type = "info"
    else:
        initial_display_item = "Walkthrough has no steps defined."
        initial_item_type = "complete"  # Or "error", or "info"

    context.update(
        {
            "request": request,
            "initial_state": initial_state,
            "walkthrough_config": walkthrough_config,  # For tagging_notes
            "image_files": image_files,
            "initial_display_item": initial_display_item,
            "initial_item_type": initial_item_type,
            "initial_step_name": initial_step_name,
            "initial_step_description": initial_step_description,
            # Add other necessary context variables here based on what tagging_workflow.html needs
        }
    )
    return templates.TemplateResponse("tools/dataset_tagger/tagging_workflow.html", context)


# Future endpoints for workflow will be added here
