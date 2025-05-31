# noqa: E501
# Pydantic models (as per feature document Sections 7.1, 7.2)


import os
from pathlib import Path
from typing import Annotated, Any

import yaml
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from PIL import Image
from pydantic import BaseModel, Field
from sqlmodel import Session
from starlette.templating import _TemplateResponse

from app import crud, logger
from app.core.db import get_db
from app.paths import DATASET_TAGGER_WALKTHROUGH_PATH
from app.views.templates import templates
from app.views.templates.context import get_template_context


# Define thumbnail constants
THUMBNAIL_DIR_NAME = ".thumb"
THUMBNAIL_WIDTH = 300  # pixels
THUMBNAIL_JPEG_QUALITY = 85


class WalkthroughStep(BaseModel):
    name: str
    description: str
    manual_inputs: list[dict[str, str]] = Field(default_factory=list)
    automatic_inputs: list[str] = Field(default_factory=list)
    character_tags: list[str] = Field(default_factory=list)


class WalkthroughConfig(BaseModel):
    tagging_notes: str
    steps: list[WalkthroughStep]


class TaggingWorkflowState(BaseModel):
    character_id: str
    folder_path: str
    current_step_index: int = 0
    current_input_type_index_in_step: int = 0
    current_item_index_within_input_type: int = 0
    pending_tags_from_last_manual_input: list[str] = Field(default_factory=lambda: [])
    active_manual_input_key: str | None = None


# Pydantic Models for Page Context and Image Data
class ImageData(BaseModel):
    original_filename: str
    thumbnail_filename: str
    thumbnail_exists: bool
    tags: list[str] = Field(default_factory=list)
    # thumbnail_url: Optional[str] = None # Can be generated in template or here


class DatasetTaggerPageContext(BaseModel):  # This will be our 'initial_state'
    folder_path: str
    images_data: list[ImageData] = Field(default_factory=list)
    character_id: str | None = None  # Add other fields if initial_state uses them
    current_image_filename: str | None = None  # Example
    tag_counts_json_str: str | None = None  # Example
    # Add any other fields that initial_state is expected to have by the template


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
        context["characters"] = await crud.character.get_all(db)
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
            context["characters"] = await crud.character.get_all(db)
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
            context["characters"] = await crud.character.get_all(db)
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
        context["characters"] = await crud.character.get_all(db)
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
        context["characters"] = await crud.character.get_all(db)
        context["error_message"] = (
            f"A system error occurred while checking the folder path '{folder_path}'. Details: {e}"
        )
        context["selected_character_id"] = character_id
        context["folder_path_value"] = folder_path
    # return templates.TemplateResponse(
    #         "tools/dataset_tagger/setup_form.html",
    #     context,
    #         status_code=500,
    #     )
    except Exception as e:
        logger.error(f"Setup POST: Unexpected error validating folder path '{folder_path}': {e}")
        context["characters"] = await crud.character.get_all(db)
        context["error_message"] = (
            f"An unexpected error occurred while validating the folder path '{folder_path}'."
        )
        context["selected_character_id"] = character_id
        context["folder_path_value"] = folder_path
    # return templates.TemplateResponse(
    #     "tools/dataset_tagger/setup_form.html",
    #     context,
    #     status_code=500,
    # )

    redirect_url = (
        f"/tools/dataset-tagger/workflow?character_id={character_id}&folder_path={folder_path}"
    )
    return RedirectResponse(url=redirect_url, status_code=303)


def _ensure_thumb_dir_exists(base_folder_path: str) -> Path:
    """Ensures the thumbnail directory exists within the base folder and returns its path."""
    thumb_dir = Path(base_folder_path) / THUMBNAIL_DIR_NAME
    try:
        thumb_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating thumbnail directory {thumb_dir}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not create thumbnail directory: {e}")
    return thumb_dir


def _generate_thumbnail(
    original_image_path: Path, thumbnail_save_path: Path, original_filename: str
) -> str | None:
    """
    Generates a thumbnail for the given image, saves it in the thumb_dir_path.
    Returns the thumbnail filename if successful, None otherwise.
    """
    thumbnail_filename = f"{original_filename}"
    thumbnail_path = thumbnail_save_path
    try:
        if not original_image_path.exists():
            logger.error(
                f"Original image not found for thumbnail generation: {original_image_path}"
            )
            return None

        img: Image.Image = Image.open(original_image_path)

        # Calculate new height to maintain aspect ratio
        original_width, original_height = img.size
        if original_width == 0:  # Avoid division by zero for corrupted images
            logger.warning(f"Original image {original_filename} has zero width.")
            return None
        aspect_ratio = original_height / original_width
        new_height = int(THUMBNAIL_WIDTH * aspect_ratio)
        if new_height == 0:
            new_height = THUMBNAIL_WIDTH  # Handle cases where aspect_ratio is very small

        img.thumbnail((THUMBNAIL_WIDTH, new_height), Image.Resampling.LANCZOS)

        if img.mode != "RGB":
            img = img.convert("RGB")

        img.save(thumbnail_path, "JPEG", quality=THUMBNAIL_JPEG_QUALITY, optimize=True)
        logger.info(f"Generated thumbnail: {thumbnail_path}")
        return thumbnail_filename
    except Exception as e:
        logger.error(f"Error generating thumbnail for {original_filename}: {e}")
        return None


@router.get("/image-proxy", response_class=FileResponse)
async def get_image_proxy(
    request: Request,
    folder: str = Query(...),
    filename: str = Query(...),
    source_dir_type: str = Query(default="original"),  # "original" or "thumbnail"
) -> FileResponse:
    """Serves an image, either original or thumbnail."""
    try:
        base_folder_path = Path(folder).resolve()

        if source_dir_type == "thumbnail":
            # Ensure .thumb directory exists if we are trying to serve from it,
            # though generation should have created it.
            # For proxy, it's more about constructing the correct path.
            image_source_folder = _ensure_thumb_dir_exists(str(base_folder_path))
            # Thumbnails might have same name as original, or could be modified if needed
            # For now, assume thumbnail filename is same as original for simplicity in proxy
        elif source_dir_type == "original":
            image_source_folder = base_folder_path
        else:
            logger.warning(f"Image proxy: Invalid source_dir_type: {source_dir_type}")
            raise HTTPException(status_code=400, detail="Invalid image source type specified.")

        requested_path = (image_source_folder / filename).resolve()

        if not image_source_folder.is_dir():  # Check the specific source folder
            logger.warning(
                f"Image proxy: Source folder path is not a directory or doesn't exist: {image_source_folder}"
            )
            raise HTTPException(
                status_code=400, detail="Invalid image source folder path provided."
            )

        if not requested_path.is_file():
            # If a thumbnail is requested and not found, we do NOT try to generate it here.
            # Generation happens during the workflow page load.
            # Here, if it's not found, it's a 404 for the thumbnail.
            logger.warning(
                f"Image proxy: Requested image not found or is not a file: {requested_path} (source type: {source_dir_type})"
            )
            raise HTTPException(
                status_code=404, detail=f"Image not found: {filename} (source: {source_dir_type})"
            )

        if os.path.commonprefix([str(requested_path), str(image_source_folder.resolve())]) != str(
            image_source_folder.resolve()
        ):
            logger.error(
                f"Image proxy: Path traversal attempt detected. Base: {image_source_folder}, Requested: {requested_path}"
            )
            raise HTTPException(
                status_code=403, detail="Forbidden: Path traversal attempt detected."
            )

        allowed_extensions = [".png", ".jpg", ".jpeg", ".webp"]
        if requested_path.suffix.lower() not in allowed_extensions:
            logger.warning(
                f"Image proxy: Invalid image type requested: {requested_path.suffix.lower()}"
            )
            raise HTTPException(status_code=400, detail="Invalid image type.")

        return FileResponse(str(requested_path))

    except FileNotFoundError:
        logger.error(
            f"Image proxy: FileNotFoundError for {filename} in {folder} (source: {source_dir_type}). This might happen if file is deleted after initial checks."
        )
        raise HTTPException(
            status_code=404,
            detail=f"Image file {filename} (source: {source_dir_type}) disappeared before it could be served.",
        )
    except PermissionError:
        logger.error(
            f"Image proxy: PermissionError serving {filename} from {folder} (source: {source_dir_type})."
        )
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied while trying to serve the image {filename} (source: {source_dir_type}).",
        )
    except Exception as e:
        logger.error(
            f"Image proxy: Unexpected error serving image {filename} from {folder} (source: {source_dir_type}): {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An unexpected server error occurred while serving the image."
        )


@router.get("/workflow", response_class=HTMLResponse)
async def get_dataset_tagger_workflow_page(
    request: Request,
    character_id: str = Query(...),
    folder_path: str = Query(...),
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
) -> _TemplateResponse:
    # ... (existing setup like loading walkthrough_config, security checks) ...

    base_path = Path(folder_path)
    if not base_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")

    try:
        walkthrough_config_path = DATASET_TAGGER_WALKTHROUGH_PATH
        with open(walkthrough_config_path) as f:
            yaml_data = yaml.safe_load(f)
        walkthrough_config = WalkthroughConfig(**yaml_data)
    except FileNotFoundError:
        logger.error(f"Walkthrough configuration file not found at: {walkthrough_config_path}")
        raise HTTPException(status_code=500, detail="Tagging walkthrough configuration not found.")
    except Exception as e:
        logger.error(f"Error loading walkthrough configuration: {e}")
        raise HTTPException(
            status_code=500, detail="Could not load tagging walkthrough configuration."
        )

    image_files_data: list[ImageData] = []
    original_image_filenames = sorted(
        [
            f.name
            for f in base_path.iterdir()
            if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]
        ]
    )

    if not original_image_filenames:
        logger.warning(f"No image files found in folder: {folder_path}")
        # Still proceed to render the page, JS will show "no images" or grid will be empty.

    thumb_dir_path = _ensure_thumb_dir_exists(folder_path)  # Ensures .thumb exists

    for img_filename in original_image_filenames:
        thumbnail_name = f"{img_filename}"
        thumbnail_file_path = thumb_dir_path / thumbnail_name
        thumbnail_exists = thumbnail_file_path.exists()

        # Load tags for the image
        base_img_filename, _ = os.path.splitext(img_filename)
        tag_file_path = base_path / f"{base_img_filename}.txt"
        image_tags = _read_tags_from_file(tag_file_path)

        image_files_data.append(
            ImageData(
                original_filename=img_filename,
                thumbnail_filename=thumbnail_name,
                thumbnail_exists=thumbnail_exists,
                tags=image_tags,
            )
        )

    # Create the initial_state object that the template expects
    # Assuming TaggingWorkflowState is for the dynamic HTMX part,
    # but initial_state for the page might be simpler or a superset.
    # The template uses initial_state.folder_path and initial_state.images_data.

    page_initial_state = DatasetTaggerPageContext(
        folder_path=folder_path,
        images_data=image_files_data,
        character_id=character_id,
        # Populate other fields if your 'initial_state' in the template uses more
        # e.g., current_image_filename might be the first image or None
        current_image_filename=original_image_filenames[0] if original_image_filenames else None,
        tag_counts_json_str="{}",  # Placeholder, adapt if needed
    )

    # Prepare context for the main workflow page
    # This `page_initial_state` will be accessible as `initial_state` in the template
    context.update(
        {
            "request": request,
            "initial_state": page_initial_state,
            "walkthrough_config": walkthrough_config,
            "notification_message": None,
            "notification_type": "info",
            "selected_images": [],
        }
    )

    # Determine the actual first item to display for the partial
    first_step = walkthrough_config.steps[0] if walkthrough_config.steps else None
    initial_display_item_for_partial = "Tagging Complete!"  # Default if no steps
    initial_item_type_for_partial = "complete"  # Default if no steps
    initial_step_name_for_partial = None
    initial_step_description_for_partial = None
    active_manual_input_key_for_partial = None

    if first_step:
        initial_step_name_for_partial = first_step.name
        initial_step_description_for_partial = first_step.description
        if first_step.manual_inputs:
            question_dict = first_step.manual_inputs[0]
            active_manual_input_key_for_partial = list(question_dict.keys())[0]
            initial_display_item_for_partial = question_dict[active_manual_input_key_for_partial]
            initial_item_type_for_partial = "manual_question"
        elif first_step.automatic_inputs:
            initial_display_item_for_partial = first_step.automatic_inputs[0]
            initial_item_type_for_partial = "tag"
        elif first_step.character_tags:
            try:
                char_tags = await crud.character.get_dataset_tagger_tags(
                    db=db, character_id=character_id
                )
                tag_category = first_step.character_tags[0]
                actual_tag = char_tags.get(tag_category)
                if actual_tag:
                    initial_display_item_for_partial = actual_tag
                    initial_item_type_for_partial = "tag"
                else:
                    initial_display_item_for_partial = (
                        f"Character tag for '{tag_category}' not found."
                    )
                    initial_item_type_for_partial = "info"
            except Exception as e:
                logger.error(f"Failed to fetch character tags for initial display: {e}")
                initial_display_item_for_partial = (
                    f"Error fetching tag: {first_step.character_tags[0]}"
                )
                initial_item_type_for_partial = "info"  # Or 'error' if template handles it
        elif first_step.name:  # Fallback to step name if no inputs/tags in the first step
            initial_display_item_for_partial = first_step.name
            initial_item_type_for_partial = (
                "step_description"  # This type will need handling in partial
            )
        else:  # If step has no inputs, tags, or even a name
            initial_display_item_for_partial = "Step information unavailable"
            initial_item_type_for_partial = "info"

    # Add context specifically for the _tag_processing_area.html partial initial include
    context["initial_display_item"] = initial_display_item_for_partial
    context["initial_item_type"] = initial_item_type_for_partial
    context["initial_step_name"] = initial_step_name_for_partial
    context["initial_step_description"] = initial_step_description_for_partial

    # This is the TaggingWorkflowState for the hidden fields in the partial
    context["TaggingWorkflowState"] = TaggingWorkflowState(
        character_id=character_id,
        folder_path=folder_path,
        current_step_index=0,
        current_input_type_index_in_step=0,
        current_item_index_within_input_type=0,
        active_manual_input_key=active_manual_input_key_for_partial,  # Set based on first item logic
        pending_tags_from_last_manual_input=[],  # Empty for initial load
    )

    logger.debug(
        f"Context for tagging_workflow.html: initial_state.images_data count = {len(page_initial_state.images_data)}"
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


def _write_tag_to_file(folder_path: str, filename: str, tag: str) -> list[str] | None:
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

        # Ensure tag is not duplicated before appending
        if tag not in current_tags:
            current_tags.append(tag)

        # Write the potentially updated list of tags back to the file
        with open(txt_filepath, "w", encoding="utf-8") as f:
            f.write(", ".join(current_tags))
        logger.info(f"Successfully wrote/updated tags in {txt_filepath}")
        return current_tags  # Return the final list of tags for this file
    except OSError as e:  # More specific exceptions for file I/O
        logger.error(
            f"I/O or OS error writing tag '{tag}' to file for {filename} in {folder_path}: {e}"
        )
        return None


def _remove_tag_from_file(folder_path: str, filename: str, tag_to_remove: str) -> list[str] | None:
    """Removes a specific tag from a .txt file for the given image filename."""
    try:
        base_filename, _ = os.path.splitext(filename)
        txt_filepath = Path(folder_path) / f"{base_filename}.txt"

        current_tags = []
        if txt_filepath.exists():
            try:
                with open(txt_filepath, encoding="utf-8") as f:
                    current_tags = [t.strip() for t in f.read().split(",") if t.strip()]
            except OSError as e:
                logger.error(f"Error reading existing tag file {txt_filepath} for removal: {e}")
                return None  # Cannot proceed if file can't be read
            except Exception as e:
                logger.error(f"Unexpected error reading tag file {txt_filepath} for removal: {e}")
                return None

        if tag_to_remove in current_tags:
            current_tags.remove(tag_to_remove)
            try:
                with open(txt_filepath, "w", encoding="utf-8") as f:
                    f.write(", ".join(current_tags))
                logger.info(f"Successfully removed tag '{tag_to_remove}' from {txt_filepath}")
                return current_tags  # Return the updated list of tags
            except OSError as e:
                logger.error(f"I/O error writing updated tags to {txt_filepath} after removal: {e}")
                return None
            except Exception as e:
                logger.error(
                    f"Unexpected error writing updated tags to {txt_filepath} after removal: {e}"
                )
                return None
        else:
            # If the tag to remove is not in the list, it's already effectively removed.
            # This can be considered a success for the operation's intent.
            logger.info(f"Tag '{tag_to_remove}' not found in {txt_filepath}, no changes made.")
            return current_tags  # Return the existing tags as they are effectively the new state

    except Exception as e:
        logger.error(
            f"Unexpected error in _remove_tag_from_file for {filename} in {folder_path}: {e}"
        )
        return None


def _read_tags_from_file(txt_filepath: Path) -> list[str]:
    """Reads tags from a .txt file, expecting comma-separated values."""
    if not txt_filepath.exists() or not txt_filepath.is_file():
        return []
    try:
        with open(txt_filepath, encoding="utf-8") as f:
            tags_content = f.read()
        # Split by comma, strip whitespace from each tag, and filter out empty strings
        tags = [tag.strip() for tag in tags_content.split(",") if tag.strip()]
        return tags
    except Exception as e:
        logger.error(f"Error reading or parsing tag file {txt_filepath}: {e}")
        return []


async def _get_next_display_item_and_update_state(
    current_state: TaggingWorkflowState,
    walkthrough_config: WalkthroughConfig,
    selected_images: list[str],
    action: str,
    manual_tag_input: str | None,
    db: Session,
) -> tuple[
    str,
    str,
    str | None,
    str | None,
    TaggingWorkflowState,
    str | None,
    str | None,
    list[dict[str, Any]],
]:
    state = current_state.model_copy(deep=True)
    original_action = action
    notification_message: str | None = None
    notification_type: str | None = None  # e.g., "success", "error", "info"
    updated_image_tag_data: list[dict[str, Any]] = []  # For HX-Trigger

    # Handle file writing for "add_tag" before advancing state for display
    if original_action == "add_tag":
        # Determine the tag that was just displayed and is being added.
        # We need to use the state *before* any index increments for the current display item.
        tag_to_action = await _get_current_tag_for_action(current_state, walkthrough_config, db)

        if tag_to_action and selected_images:
            num_successful_writes = 0
            for img_filename in selected_images:
                new_tags = _write_tag_to_file(state.folder_path, img_filename, tag_to_action)
                if new_tags is not None:
                    num_successful_writes += 1
                    updated_image_tag_data.append({"filename": img_filename, "tags": new_tags})
            if num_successful_writes > 0:
                notification_message = (
                    f"Tag '{tag_to_action}' added to {num_successful_writes} image(s)."
                )
                notification_type = "success"
            else:
                notification_message = (
                    f"Failed to add tag '{tag_to_action}' to any selected images."
                )
                notification_type = "warning"
        elif not selected_images and tag_to_action:
            notification_message = f"No images selected to add tag '{tag_to_action}'."
            notification_type = "info"
        elif not tag_to_action:
            notification_message = "Could not determine tag to add."
            notification_type = "error"

    # Handle file writing for "remove_tag" before advancing state for display
    elif original_action == "remove_tag":
        tag_to_action = await _get_current_tag_for_action(current_state, walkthrough_config, db)
        if tag_to_action and selected_images:
            num_successful_removals = 0
            for img_filename in selected_images:
                new_tags = _remove_tag_from_file(state.folder_path, img_filename, tag_to_action)
                if new_tags is not None:
                    num_successful_removals += 1
                    updated_image_tag_data.append({"filename": img_filename, "tags": new_tags})
            if num_successful_removals > 0:
                notification_message = (
                    f"Tag '{tag_to_action}' removed from {num_successful_removals} image(s)."
                )
                notification_type = "success"
            else:
                # This case might mean the tag wasn't present or file I/O failed
                notification_message = f"Tag '{tag_to_action}' not found on selected image(s) or failed to update files."
                notification_type = "warning"  # Or "info" if not finding it is not an error
        elif not selected_images and tag_to_action:
            notification_message = f"No images selected to remove tag '{tag_to_action}'."
            notification_type = "info"
        elif not tag_to_action:
            notification_message = "Could not determine tag to remove."
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
                updated_image_tag_data,
            )

        current_walkthrough_step = walkthrough_config.steps[state.current_step_index]
        step_name = current_walkthrough_step.name
        step_description = current_walkthrough_step.description

        # Actions that consume the current item and advance the index for that type
        advancing_actions = ["skip_tag"]
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
                    updated_image_tag_data,
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
                    updated_image_tag_data,
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
                    updated_image_tag_data,
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
                        updated_image_tag_data,
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
            updated_image_tag_data,  # Pass empty list on error
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
            updated_image_tag_data_list,
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
        logger.info(f"Updated image tag data for HX-Trigger: {updated_image_tag_data_list}")

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

        response_headers = {}
        if updated_image_tag_data_list:
            # Serialize the list of dicts to a JSON string for the header
            import json

            response_headers["HX-Trigger"] = json.dumps(
                {"tagsUpdated": updated_image_tag_data_list}
            )

        return templates.TemplateResponse(
            "tools/dataset_tagger/_tag_processing_area.html",
            {**context, **partial_context},
            headers=response_headers,
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


@router.post("/generate-thumbnail", status_code=200)
async def post_generate_single_thumbnail(
    request: Request,  # Added request for potential future use (e.g. auth)
    folder_path: Annotated[str, Form()],
    original_filename: Annotated[str, Form()],
    # db: Session = Depends(get_db) # Not needed for simple thumbnail generation
) -> dict[str, Any]:
    """Generates a thumbnail for a single specified image.

    Args:
        request: The FastAPI request object.
        folder_path: The base directory where the original image resides.
        original_filename: The filename of the original image.

    Returns:
        JSON response indicating success or failure and thumbnail path.
    """
    p_folder_path = Path(folder_path)
    original_image_path = p_folder_path / original_filename

    if not original_image_path.is_file():
        logger.error(f"Generate-thumbnail API: Original image not found: {original_image_path}")
        raise HTTPException(
            status_code=404, detail=f"Original image '{original_filename}' not found in folder."
        )

    try:
        thumb_dir = _ensure_thumb_dir_exists(str(p_folder_path))
        # Thumbnail keeps the same filename, stored in .thumb subdir
        thumbnail_save_path = thumb_dir / original_filename
    except Exception as e:  # Catch errors from _ensure_thumb_dir_exists
        logger.error(
            f"Generate-thumbnail API: Failed to ensure/create thumbnail directory for {p_folder_path}: {e}"
        )
        raise HTTPException(status_code=500, detail="Failed to prepare thumbnail directory.")

    if thumbnail_save_path.is_file():
        logger.info(
            f"Generate-thumbnail API: Thumbnail already exists for {original_filename} at {thumbnail_save_path}"
        )
        return {
            "success": True,
            "message": "Thumbnail already existed.",
            "thumbnail_filename": original_filename,  # Keep consistent with how images_data is structured
            "thumbnail_url": f"/tools/dataset-tagger/image-proxy?folder={folder_path}&filename={original_filename}&source_dir_type=thumbnail",
        }

    success = _generate_thumbnail(
        original_image_path=original_image_path,
        thumbnail_save_path=thumbnail_save_path,
        original_filename=original_filename,
    )

    if success:
        return {
            "success": True,
            "message": "Thumbnail generated successfully.",
            "thumbnail_filename": original_filename,
            "thumbnail_url": f"/tools/dataset-tagger/image-proxy?folder={folder_path}&filename={original_filename}&source_dir_type=thumbnail",
        }
    else:
        # _generate_thumbnail logs its own errors, so just return a generic failure here for the API response
        # We could raise HTTPException, but a JSON response might be easier for client-side loop processing.
        return {
            "success": False,
            "message": f"Failed to generate thumbnail for {original_filename}. Check server logs.",
            "thumbnail_filename": original_filename,
            "thumbnail_url": None,  # No URL if generation failed
        }


# Future endpoints for workflow will be added here
# The new POST endpoint will go below this line
