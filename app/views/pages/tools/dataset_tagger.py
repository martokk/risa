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
        logger.warning(
            f"Setup POST: Folder path was empty or default. User provided: '{folder_path}'"
        )
        context["characters"] = await crud.character.get_all(db=db)
        context["error_message"] = "Folder path cannot be empty or the default path."
        context["selected_character_id"] = character_id
        context["folder_path_value"] = folder_path

        # Re-render the form with an error message
        return templates.TemplateResponse(
            "tools/dataset_tagger/setup_form.html",
            context,
            status_code=400,
        )

    try:
        path_obj = Path(folder_path)
        if not path_obj.exists():
            logger.warning(f"Setup POST: Provided folder path does not exist: {folder_path}")
            context["characters"] = await crud.character.get_all(db=db)
            context["error_message"] = f"Folder not found: '{folder_path}'. Please verify the path."
            context["selected_character_id"] = character_id
            context["folder_path_value"] = folder_path
            return templates.TemplateResponse(
                "tools/dataset_tagger/setup_form.html",
                context,
                status_code=400,
            )
        if not path_obj.is_dir():
            logger.warning(f"Setup POST: Provided folder path is not a directory: {folder_path}")
            context["characters"] = await crud.character.get_all(db=db)
            context["error_message"] = (
                f"The path '{folder_path}' is not a directory. Please select a valid folder."
            )
            context["selected_character_id"] = character_id
            context["folder_path_value"] = folder_path
            return templates.TemplateResponse(
                "tools/dataset_tagger/setup_form.html",
                context,
                status_code=400,
            )
    except PermissionError as e:
        logger.error(f"Setup POST: Permission error accessing folder path '{folder_path}': {e}")
        context["characters"] = await crud.character.get_all(db=db)
        context["error_message"] = (
            f"Permission denied when trying to access folder '{folder_path}'. Check server permissions."
        )
        context["selected_character_id"] = character_id
        context["folder_path_value"] = folder_path
        return templates.TemplateResponse(
            "tools/dataset_tagger/setup_form.html",
            context,
            status_code=403,
        )
    except OSError as e:
        logger.error(f"Setup POST: OS error checking folder path '{folder_path}': {e}")
        context["characters"] = await crud.character.get_all(db=db)
        context["error_message"] = (
            f"A system error occurred while checking the folder path '{folder_path}'. Details: {e}"
        )
        context["selected_character_id"] = character_id
        context["folder_path_value"] = folder_path
        return templates.TemplateResponse(
            "tools/dataset_tagger/setup_form.html",
            context,
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Setup POST: Unexpected error validating folder path '{folder_path}': {e}")
        context["characters"] = await crud.character.get_all(db=db)
        context["error_message"] = (
            f"An unexpected error occurred while validating the folder path '{folder_path}'."
        )
        context["selected_character_id"] = character_id
        context["folder_path_value"] = folder_path
        return templates.TemplateResponse(
            "tools/dataset_tagger/setup_form.html",
            context,
            status_code=500,
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
    try:
        base_dir = Path(folder).resolve()
        requested_path = (base_dir / filename).resolve()

        # Check if the resolved path is within the resolved base_dir
        if not base_dir.is_dir():
            logger.warning(
                f"Image proxy: Base folder path is not a directory or doesn't exist: {base_dir}"
            )
            raise HTTPException(status_code=400, detail="Invalid base folder path provided.")

        if not requested_path.is_file():
            logger.warning(
                f"Image proxy: Requested image not found or is not a file: {requested_path}"
            )
            raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

        # Ensure the requested path is actually within the base_dir to prevent traversal
        # A more robust check for path traversal:
        # After resolving both, the requested_path must start with the base_dir path string.
        if os.path.commonprefix([str(requested_path), str(base_dir)]) != str(base_dir):
            logger.error(
                f"Image proxy: Path traversal attempt detected. Base: {base_dir}, Requested: {requested_path}"
            )
            raise HTTPException(
                status_code=403, detail="Forbidden: Path traversal attempt detected."
            )

        # Check for allowed image types if necessary (optional, for added security)
        allowed_extensions = [".png", ".jpg", ".jpeg", ".webp"]
        if requested_path.suffix.lower() not in allowed_extensions:
            logger.warning(
                f"Image proxy: Invalid image type requested: {requested_path.suffix.lower()}"
            )
            raise HTTPException(status_code=400, detail="Invalid image type.")

        return FileResponse(str(requested_path))

    except FileNotFoundError:
        logger.error(
            f"Image proxy: FileNotFoundError for {filename} in {folder}. This might happen if file is deleted after initial checks."
        )
        raise HTTPException(
            status_code=404, detail=f"Image file {filename} disappeared before it could be served."
        )
    except PermissionError:
        logger.error(f"Image proxy: PermissionError serving {filename} from {folder}.")
        raise HTTPException(
            status_code=403, detail=f"Permission denied while trying to serve the image {filename}."
        )
    except Exception as e:
        logger.error(f"Image proxy: Unexpected error serving image {filename} from {folder}: {e}")
        raise HTTPException(
            status_code=500, detail="An unexpected server error occurred while serving the image."
        )


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

    if not walkthrough_config_path.is_file():
        logger.error(f"Walkthrough configuration file not found at: {walkthrough_config_path}")
        raise HTTPException(
            status_code=500,
            detail=f"Critical Error: Dataset tagger walkthrough configuration file not found at {walkthrough_config_path}. Please check server setup.",
        )

    try:
        with open(walkthrough_config_path, encoding="utf-8") as f:  # Added encoding
            yaml_data = yaml.safe_load(f)
            if not yaml_data:
                logger.error(
                    f"Walkthrough configuration file is empty or invalid: {walkthrough_config_path}"
                )
                raise HTTPException(
                    status_code=500,
                    detail="Critical Error: Walkthrough configuration file is empty or invalid.",
                )
            walkthrough_config = WalkthroughConfig(**yaml_data)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML from {walkthrough_config_path}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error parsing walkthrough.yaml: {e}. Check for syntax errors."
        ) from e
    except Exception as e:  # Catches Pydantic validation errors too
        logger.error(f"Error loading walkthrough configuration from {walkthrough_config_path}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading walkthrough configuration: {e}. Ensure the structure matches the Pydantic models.",
        ) from e

    image_files: list[str] = []
    allowed_extensions = (".png", ".jpg", ".jpeg", ".webp")
    try:
        p_folder_path = Path(folder_path)
        if not p_folder_path.exists():
            logger.warning(f"Image folder does not exist: {folder_path}")
            raise HTTPException(
                status_code=400,
                detail=f"Image folder not found: {folder_path}. Please check the path provided in setup.",
            )
        if not p_folder_path.is_dir():
            logger.warning(f"Provided path is not a directory: {folder_path}")
            raise HTTPException(
                status_code=400,
                detail=f"The path '{folder_path}' is not a directory. Please select a valid folder.",
            )

        image_files = sorted(
            [
                f.name
                for f in p_folder_path.iterdir()
                if f.is_file() and f.suffix.lower() in allowed_extensions
            ]
        )
        if not image_files:
            logger.info(f"No images with allowed extensions found in folder: {folder_path}")
            # This is not necessarily an error, could be an empty dataset.
            # The UI should handle displaying "no images found".
            # We can pass a notification if desired.
            pass  # Let it proceed with an empty list

    except PermissionError as e:
        logger.error(f"Permission error accessing image folder {folder_path}: {e}")
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied when trying to access the folder: {folder_path}. Check server permissions.",
        ) from e
    except OSError as e:  # Catch other OS-level errors like too many open files, etc.
        logger.error(f"OS error accessing image folder {folder_path}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"A system error occurred while accessing the folder: {folder_path}. Details: {e}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error listing image files in {folder_path}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Unexpected error listing image files: {e}"
        ) from e

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


async def _get_current_tag_for_action(
    current_state: TaggingWorkflowState,
    walkthrough_config: WalkthroughConfig,
    db: Session | None = None,
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
            if db:
                character_specific_tags = await crud.character.get_dataset_tagger_tags(
                    db=db, character_id=current_state.character_id
                )
                tag_value = character_specific_tags.get(char_tag_category)
                return tag_value
            logger.warning(
                "Database session not available in _get_current_tag_for_action for character_tags"
            )
            return f"Error: DB not available for {char_tag_category}"
    return None


def _write_tag_to_file(folder_path: str, filename: str, tag: str) -> bool:
    """Appends a tag to a .txt file for the given image filename."""
    try:
        base_filename, _ = os.path.splitext(filename)
        txt_filepath = Path(folder_path) / f"{base_filename}.txt"

        current_tags = []
        if txt_filepath.exists():
            # Ensure reading with encoding and handle potential errors during read
            try:
                with open(txt_filepath, encoding="utf-8") as f:  # Specify 'r' for reading
                    current_tags = [t.strip() for t in f.read().split(",") if t.strip()]
            except OSError as e:
                logger.error(f"Error reading existing tag file {txt_filepath}: {e}")
                # Depending on desired behavior, could return False or raise an error
                # For now, we'll attempt to overwrite if reading fails, which might not be ideal.
                # Consider if failing to read should prevent writing.
                pass  # Or return False if read failure should halt operation
            except Exception as e:  # Catch any other unexpected error during read
                logger.error(f"Unexpected error reading tag file {txt_filepath}: {e}")
                pass  # Or return False

        if tag not in current_tags:  # Basic de-duplication for this single add
            current_tags.append(tag)

        with open(txt_filepath, "w", encoding="utf-8") as f:
            f.write(", ".join(current_tags))
        logger.info(f"Successfully wrote tag '{tag}' to {txt_filepath}")
        return True
    except OSError as e:  # More specific exceptions for file I/O
        logger.error(
            f"I/O or OS error writing tag '{tag}' to file for {filename} in {folder_path}: {e}"
        )
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error writing tag '{tag}' to file for {filename} in {folder_path}: {e}"
        )
        return False


async def _get_next_display_item_and_update_state(
    current_state: TaggingWorkflowState,
    walkthrough_config: WalkthroughConfig,
    selected_images: list[str],
    action: str,
    manual_tag_input: str | None,
    db: Session,
) -> tuple[str, str, str | None, str | None, TaggingWorkflowState, str | None, str | None]:
    state = current_state.model_copy(deep=True)
    original_action = action
    notification_message: str | None = None
    notification_type: str | None = None  # e.g., "success", "error", "info"

    # Handle file writing for "add_tag" before advancing state for display
    if original_action == "add_tag":
        # Determine the tag that was just displayed and is being added.
        # We need to use the state *before* any index increments for the current display item.
        tag_to_add = await _get_current_tag_for_action(current_state, walkthrough_config, db)

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
                character_specific_tags = await crud.character.get_dataset_tagger_tags(
                    db=db, character_id=state.character_id
                )
                tag_value = character_specific_tags.get(char_tag_category)

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
    try:
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
        if not walkthrough_config_path.is_file():
            logger.error(
                f"Process-tag POST: Walkthrough configuration file not found: {walkthrough_config_path}"
            )
            raise HTTPException(
                status_code=500, detail="Critical Error: Walkthrough configuration file not found."
            )

        try:
            with open(walkthrough_config_path, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
                if not yaml_data:
                    logger.error(
                        f"Process-tag POST: Walkthrough configuration file is empty or invalid: {walkthrough_config_path}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail="Critical Error: Walkthrough configuration file is empty or invalid.",
                    )
                walkthrough_config = WalkthroughConfig(**yaml_data)
        except yaml.YAMLError as e:
            logger.error(
                f"Process-tag POST: Error parsing YAML from {walkthrough_config_path}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Error parsing walkthrough.yaml: {e}. Check for syntax errors.",
            ) from e
        except Exception as e:  # Catches Pydantic validation errors too
            logger.error(
                f"Process-tag POST: Error loading walkthrough configuration from {walkthrough_config_path}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Error loading walkthrough configuration: {e}. Ensure the structure matches models.",
            ) from e

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
            "selected_images": selected_images,
        }
        return templates.TemplateResponse(
            "tools/dataset_tagger/_tag_processing_area.html", {**context, **partial_context}
        )

    except HTTPException:  # Re-raise HTTPExceptions so FastAPI handles them
        raise
    except Exception as e:
        logger.error(f"Critical error in post_dataset_tagger_process_tag: {e}", exc_info=True)
        # Attempt to return an error message within the HTMX partial
        error_partial_context = {
            "request": request,
            "initial_state": current_state
            if "current_state" in locals()
            else None,  # Pass last known state if available
            "initial_display_item": "An unexpected server error occurred.",
            "initial_item_type": "error",  # Custom type for template to display error style
            "initial_step_name": "Error",
            "initial_step_description": "Please try again or contact support if the issue persists.",
            "notification_message": "Server Error: Could not process your request.",
            "notification_type": "danger",
            "selected_images": selected_images_input.split(",") if selected_images_input else [],
        }
        # Merge with a minimal base context if necessary, or ensure _tag_processing_area.html can handle this state.
        return templates.TemplateResponse(
            "tools/dataset_tagger/_tag_processing_area.html",
            {**context, **error_partial_context},
            status_code=500,
        )


# Future endpoints for workflow will be added here
# The new POST endpoint will go below this line
