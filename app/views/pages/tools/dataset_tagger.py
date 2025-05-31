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

from app import crud, logger
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
    db: Session = Depends(get_db),
    action: str = Query(default="initial_load"),
    context: dict[str, Any] = Depends(get_template_context),
) -> _TemplateResponse:
    initial_state = TaggingWorkflowState(
        character_id=character_id,
        folder_path=folder_path,
    )

    walkthrough_config_path = DATASET_TAGGER_WALKTHROUGH_PATH
    walkthrough_config: WalkthroughConfig | None = None
    if walkthrough_config_path.is_file():
        with open(walkthrough_config_path) as f:
            try:
                yaml_data = yaml.safe_load(f)
                walkthrough_config = WalkthroughConfig(**yaml_data)
            except yaml.YAMLError as e:
                raise HTTPException(
                    status_code=500, detail=f"Error parsing walkthrough.yaml: {e}"
                ) from e
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error loading walkthrough config: {e}"
                ) from e
    else:
        raise HTTPException(status_code=500, detail="walkthrough.yaml not found.")

    if not walkthrough_config:
        raise HTTPException(status_code=500, detail="Failed to load walkthrough configuration.")

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
            raise HTTPException(
                status_code=400, detail=f"Provided path is not a directory: {folder_path}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing image files: {e}") from e

    (
        next_display_item,
        next_item_type,
        next_step_name,
        next_step_description,
        updated_state,
        notification_message,
        notification_type,
    ) = await _get_next_display_item_and_update_state(
        current_state=initial_state,
        walkthrough_config=walkthrough_config,
        action=action,
        selected_images=[],
        manual_tag_input=None,
        db=db,
    )

    context.update(
        {
            "request": request,
            "initial_state": updated_state,
            "walkthrough_config": walkthrough_config,
            "image_files": image_files,
            "initial_display_item": next_display_item,
            "initial_item_type": next_item_type,
            "initial_step_name": next_step_name,
            "initial_step_description": next_step_description,
            "notification_message": notification_message,
            "notification_type": notification_type,
        }
    )
    return templates.TemplateResponse("tools/dataset_tagger/tagging_workflow.html", context)


def _get_current_tag_for_action(
    current_state: TaggingWorkflowState,
    walkthrough_config: WalkthroughConfig,
    db: Session | None = None,  # For character tags in future
) -> str | None:
    """Determines the tag that was displayed when an action (like add_tag) was taken."""
    # This function uses the state *as it was when the action was performed*,
    # i.e., before current_item_index_within_input_type was incremented by skip/add logic.

    if not walkthrough_config.steps or current_state.current_step_index >= len(
        walkthrough_config.steps
    ):
        return None

    current_walkthrough_step = walkthrough_config.steps[current_state.current_step_index]

    # Check based on input type index at the moment of action
    input_type = current_state.current_input_type_index_in_step
    item_index = current_state.current_item_index_within_input_type

    if input_type == 1:  # pending_tags_from_last_manual_input
        if item_index < len(current_state.pending_tags_from_last_manual_input):
            return current_state.pending_tags_from_last_manual_input[item_index]
    elif input_type == 2:  # automatic_inputs
        if current_walkthrough_step.automatic_inputs and item_index < len(
            current_walkthrough_step.automatic_inputs
        ):
            return current_walkthrough_step.automatic_inputs[item_index]
    elif input_type == 3:  # character_tags
        if current_walkthrough_step.character_tags and item_index < len(
            current_walkthrough_step.character_tags
        ):
            char_tag_category = current_walkthrough_step.character_tags[item_index]
            if db:  # In Phase 6, this will fetch from DB
                # character_specific_tags = await crud.character.get_tags_dict(db, character_id=current_state.character_id)
                # return character_specific_tags.get(char_tag_category)
                return f"Mocked_DB: {char_tag_category} for {current_state.character_id}"  # Placeholder
            return f"Mocked: {char_tag_category} for {current_state.character_id}"  # Placeholder
    return None


def _write_tag_to_file(folder_path: str, filename: str, tag: str) -> bool:
    """Appends a tag to a .txt file for the given image filename."""
    try:
        base_filename, _ = os.path.splitext(filename)
        txt_filepath = Path(folder_path) / f"{base_filename}.txt"

        current_tags = []
        if txt_filepath.exists():
            with open(txt_filepath, encoding="utf-8") as f:
                current_tags = [t.strip() for t in f.read().split(",") if t.strip()]

        if tag not in current_tags:  # Basic de-duplication for this single add
            current_tags.append(tag)

        with open(txt_filepath, "w", encoding="utf-8") as f:
            f.write(", ".join(current_tags))
        logger.info(f"Successfully wrote tag '{tag}' to {txt_filepath}")
        return True
    except Exception as e:
        logger.error(f"Error writing tag '{tag}' to file for {filename}: {e}")
        return False


async def _get_next_display_item_and_update_state(
    current_state: TaggingWorkflowState,
    walkthrough_config: WalkthroughConfig,
    selected_images: list[str],
    action: str,
    manual_tag_input: str | None,
    db: Session,  # Now required due to _get_current_tag_for_action possibly needing it
) -> tuple[
    str, str, str | None, str | None, TaggingWorkflowState, str | None, str | None
]:  # Added notification msg & type
    state = current_state.model_copy(deep=True)
    original_action = action
    notification_message: str | None = None
    notification_type: str | None = None  # e.g., "success", "error", "info"

    # Handle file writing for "add_tag" before advancing state for display
    if original_action == "add_tag":
        # Determine the tag that was just displayed and is being added.
        # We need to use the state *before* any index increments for the current display item.
        tag_to_add = _get_current_tag_for_action(current_state, walkthrough_config, db)

        if tag_to_add and selected_images:
            num_successful_writes = 0
            for img_filename in selected_images:
                if _write_tag_to_file(state.folder_path, img_filename, tag_to_add):
                    num_successful_writes += 1
            if num_successful_writes > 0:
                notification_message = (
                    f"Tag '{tag_to_add}' added to {num_successful_writes} image(s)."
                )
                notification_type = "success"
            else:
                notification_message = f"Failed to add tag '{tag_to_add}' to any selected images."
                notification_type = "warning"
        elif not selected_images and tag_to_add:
            notification_message = f"No images selected to add tag '{tag_to_add}'."
            notification_type = "info"
        elif not tag_to_add:
            notification_message = "Could not determine tag to add."
            notification_type = "error"

    if original_action == "submit_manual_input" and manual_tag_input:
        state.pending_tags_from_last_manual_input = [
            t.strip() for t in manual_tag_input.split(",") if t.strip()
        ]
        state.current_input_type_index_in_step = 1
        state.current_item_index_within_input_type = 0
        state.active_manual_input_key = None
        # If tags were submitted, let the loop find the first one.
        # No specific notification for just submitting, success is showing the first tag.

    while True:
        if not walkthrough_config.steps or state.current_step_index >= len(
            walkthrough_config.steps
        ):
            return (
                "Tagging Complete!",
                "complete",
                None,
                None,
                state,
                notification_message,
                notification_type,
            )

        current_walkthrough_step = walkthrough_config.steps[state.current_step_index]
        step_name = current_walkthrough_step.name
        step_description = current_walkthrough_step.description

        # Actions that consume the current item and advance the index for that type
        advancing_actions = ["skip_tag", "add_tag"]
        if original_action == "submit_manual_input" and state.current_input_type_index_in_step == 0:
            # If we submitted manual input for a question, we are done with *that question*
            advancing_actions.append("submit_manual_input")

        # Case 0: manual_inputs questions
        if state.current_input_type_index_in_step == 0:
            if original_action in advancing_actions:
                state.current_item_index_within_input_type += 1

            if (
                current_walkthrough_step.manual_inputs
                and state.current_item_index_within_input_type
                < len(current_walkthrough_step.manual_inputs)
            ):
                question_dict = current_walkthrough_step.manual_inputs[
                    state.current_item_index_within_input_type
                ]
                state.active_manual_input_key = list(question_dict.keys())[0]
                next_display_item = question_dict[state.active_manual_input_key]
                return (
                    next_display_item,
                    "manual_question",
                    step_name,
                    step_description,
                    state,
                    notification_message,
                    notification_type,
                )
            else:
                state.current_input_type_index_in_step = 1
                state.current_item_index_within_input_type = 0
                state.active_manual_input_key = None
                # If we just submitted manual input, pending_tags might now have items. Restart loop.
                if original_action == "submit_manual_input":
                    original_action = (
                        "initial_load"  # Reset action to avoid re-processing submission logic
                    )
                continue

        # Case 1: pending_tags_from_last_manual_input
        elif state.current_input_type_index_in_step == 1:
            if original_action in advancing_actions:
                state.current_item_index_within_input_type += 1

            if state.current_item_index_within_input_type < len(
                state.pending_tags_from_last_manual_input
            ):
                next_display_item = state.pending_tags_from_last_manual_input[
                    state.current_item_index_within_input_type
                ]
                return (
                    next_display_item,
                    "tag",
                    step_name,
                    step_description,
                    state,
                    notification_message,
                    notification_type,
                )
            else:
                state.pending_tags_from_last_manual_input = []
                state.current_input_type_index_in_step = 2
                state.current_item_index_within_input_type = 0
                continue

        # Case 2: automatic_inputs
        elif state.current_input_type_index_in_step == 2:
            if original_action in advancing_actions:
                state.current_item_index_within_input_type += 1

            if (
                current_walkthrough_step.automatic_inputs
                and state.current_item_index_within_input_type
                < len(current_walkthrough_step.automatic_inputs)
            ):
                next_display_item = current_walkthrough_step.automatic_inputs[
                    state.current_item_index_within_input_type
                ]
                return (
                    next_display_item,
                    "tag",
                    step_name,
                    step_description,
                    state,
                    notification_message,
                    notification_type,
                )
            else:
                state.current_input_type_index_in_step = 3
                state.current_item_index_within_input_type = 0
                continue

        # Case 3: character_tags
        elif state.current_input_type_index_in_step == 3:
            if original_action in advancing_actions:
                state.current_item_index_within_input_type += 1

            if (
                current_walkthrough_step.character_tags
                and state.current_item_index_within_input_type
                < len(current_walkthrough_step.character_tags)
            ):
                char_tag_category = current_walkthrough_step.character_tags[
                    state.current_item_index_within_input_type
                ]
                # In Phase 6, this will fetch from DB
                # For now, mock it. Ensure db is passed if you uncomment DB logic.
                if db:  # Phase 6 example
                    # character_specific_tags = await crud.character.get_tags_dict(db, character_id=state.character_id)
                    # tag_value = character_specific_tags.get(char_tag_category)
                    tag_value = f"Mocked_DB: {char_tag_category} for {state.character_id}"
                else:
                    tag_value = f"Mocked: {char_tag_category} for {state.character_id}"

                if tag_value:
                    return (
                        tag_value,
                        "tag",
                        step_name,
                        step_description,
                        state,
                        notification_message,
                        notification_type,
                    )
                else:
                    # Auto-skip if char_tag_category resolves to no value
                    # No need to increment item_index_within_input_type again here, as the loop will continue,
                    # and if original_action was skip/add, it was already incremented.
                    continue
            else:
                state.current_step_index += 1
                state.current_input_type_index_in_step = 0
                state.current_item_index_within_input_type = 0
                state.active_manual_input_key = None
                state.pending_tags_from_last_manual_input = []
                continue

        return (
            "Error: Could not determine next step.",
            "info",
            None,
            None,
            state,
            "An unexpected error occurred.",
            "error",
        )


@router.post("/workflow/process-tag", response_class=HTMLResponse)
async def post_dataset_tagger_process_tag(
    request: Request,
    # --- TaggingWorkflowState fields --- #
    character_id: Annotated[str, Form()],
    folder_path: Annotated[str, Form()],
    current_step_index: Annotated[int, Form()],
    current_input_type_index_in_step: Annotated[int, Form()],
    current_item_index_within_input_type: Annotated[int, Form()],
    # --- Action (required) --- #
    action: Annotated[str, Form()],
    # --- Optional form inputs --- #
    pending_tags_from_last_manual_input_str: Annotated[
        str, Form(alias="pending_tags_from_last_manual_input")
    ] = "",
    active_manual_input_key: Annotated[str | None, Form()] = None,
    selected_images_input: Annotated[str, Form()] = "",
    manual_tag_input: Annotated[str | None, Form()] = None,
    # --- Dependencies --- #
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
) -> _TemplateResponse:
    current_state = TaggingWorkflowState(
        character_id=character_id,
        folder_path=folder_path,
        current_step_index=current_step_index,
        current_input_type_index_in_step=current_input_type_index_in_step,
        current_item_index_within_input_type=current_item_index_within_input_type,
        pending_tags_from_last_manual_input=(
            [t.strip() for t in pending_tags_from_last_manual_input_str.split(",") if t.strip()]
            if pending_tags_from_last_manual_input_str
            else []
        ),
        active_manual_input_key=active_manual_input_key,
    )
    logger.info(
        f"Phase 4 DEBUG: State BEFORE calling helper: {current_state.model_dump_json(indent=2)}"
    )
    logger.info(f"Phase 4 DEBUG: Action received: {action}, Manual Input: {manual_tag_input}")

    selected_images = [img.strip() for img in selected_images_input.split(",") if img.strip()]

    walkthrough_config_path = DATASET_TAGGER_WALKTHROUGH_PATH
    walkthrough_config: WalkthroughConfig | None = None
    if walkthrough_config_path.is_file():
        with open(walkthrough_config_path) as f:
            try:
                yaml_data = yaml.safe_load(f)
                walkthrough_config = WalkthroughConfig(**yaml_data)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error loading walkthrough config: {e}"
                )
    else:
        raise HTTPException(status_code=500, detail="walkthrough.yaml not found.")

    if not walkthrough_config:
        raise HTTPException(
            status_code=500, detail="Failed to load walkthrough configuration for POST."
        )

    (
        next_display_item,
        next_item_type,
        next_step_name,
        next_step_description,
        updated_state,
        notification_message,
        notification_type,
    ) = await _get_next_display_item_and_update_state(
        current_state=current_state,
        walkthrough_config=walkthrough_config,
        action=action,
        selected_images=selected_images,
        manual_tag_input=manual_tag_input,
        db=db,
    )
    logger.info(
        f"Phase 4 DEBUG: State AFTER calling helper (updated_state): {updated_state.model_dump_json(indent=2)}"
    )
    logger.info(
        f"Phase 4 DEBUG: Next display item: {next_display_item}, Type: {next_item_type}, Notification: {notification_message}"
    )

    partial_context = {
        "request": request,
        "initial_state": updated_state,
        "initial_display_item": next_display_item,
        "initial_item_type": next_item_type,
        "initial_step_name": next_step_name,
        "initial_step_description": next_step_description,
        "notification_message": notification_message,
        "notification_type": notification_type,
    }
    context.update(partial_context)

    return templates.TemplateResponse("tools/dataset_tagger/_tag_processing_area.html", context)


# Future endpoints for workflow will be added here
# The new POST endpoint will go below this line
