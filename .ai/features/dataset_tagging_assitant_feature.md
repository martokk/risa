
Okay, here is the complete feature documentation for the "Dataset Tagging Assistant," incorporating all the sections we've discussed. This should provide a solid foundation for an LLM to assist with code generation.

```markdown
# Feature Document: Dataset Tagging Assistant 🖼️🏷️

**Version:** 0.1
**Date:** October 26, 2023 (Updated)

### 1. Introduction & Goal

The **Dataset Tagging Assistant** is a web-based tool designed to streamline the process of applying comma-separated, Danbooru-style tags to a collection of images within a specified folder. The primary goal is to guide the user through a structured tagging workflow, ensuring comprehensive and consistent tagging, which is crucial for training high-quality LORA (Low-Rank Adaptation) models of specific characters.

This initial version focuses on simplicity and core functionality, providing a step-by-step walkthrough based on a predefined YAML configuration and leveraging HTMX for a responsive user experience with minimal client-side JavaScript.

### 2. Key Definitions

*   **`tagging_notes`**: Informational text displayed at the beginning of the tagging walkthrough. Its purpose is to educate the user on best practices for tagging images for the specific context (e.g., what defines a character vs. what doesn't).
*   **`dataset_tagger_walkthrough.yaml`**: A YAML file that defines the structure and sequence of the tagging process. It's divided into steps, and each step specifies types of tags to be processed.
*   **`manual_inputs`**: Within a walkthrough step, these are prompts for the user to enter specific tags (single or comma-separated). These tags are typically unique to the dataset or character. Once entered, each tag is then presented to the user, who will select the relevant images to apply it to.
*   **`automatic_tags`**: Common, predefined tags listed within a walkthrough step. The tool will present each of these tags to the user sequentially, who will then select all images to which the current tag applies.
*   **`character_tags`**: Tags associated with a pre-selected "Character" (managed in a database). When a walkthrough step references a `character_tag` type (e.g., `hair_color`), the tool will retrieve the specific tag value for the selected Character (e.g., "blonde hair") and present it to the user for image selection.

### 3. Core Workflow

The user interacts with the tool in the following sequence:

1.  **Initialization:**
    *   The user navigates to the setup page (`/tools/dataset-tagger/setup`).
    *   The user selects a **Character** from a list (populated from a database).
    *   The user provides/selects a **folder path** on the server that contains the images to be tagged.
    *   Upon submission, the server validates inputs. If valid, it prepares the initial workflow state and redirects/renders the main tagging page.

2.  **Tagging Session Start (Main Workflow Page):**
    *   The `tagging_notes` from `dataset_tagger_walkthrough.yaml` are displayed.
    *   All images from the specified folder are displayed in a thumbnail grid.
    *   The first tag/question from the `dataset_tagger_walkthrough.yaml` is presented in the "tag processing area."

3.  **Step-by-Step Tagging Walkthrough (HTMX Driven):**
    The tool iterates through each `step` defined in `dataset_tagger_walkthrough.yaml` sequentially. The "tag processing area" is updated via HTMX. For each step:
    *   The step's name/description is displayed alongside the current tag/question.
    *   Tags within the step are processed based on the `TaggingWorkflowState`:
        1.  **`manual_inputs` Questions:**
            *   A prompt (e.g., "What are the unique trigger tags for the character?") is shown with a text input field.
            *   User enters tag(s) and submits. This HTMX request updates `pending_tags_from_last_manual_input` in the server-side state. The server then presents the first of these entered tags.
        2.  **Processing User-Provided Manual Tags / `automatic_inputs` / `character_tags`:**
            *   The current tag (whether from user's manual input, an automatic list, or a character's predefined tag) is displayed.
            *   User clicks on images in the grid to select them (visual feedback via JS).
            *   User clicks "Add Tag": HTMX POST request is sent. Server appends tag to `.txt` files, determines the next tag/question, and returns an HTML partial to update the "tag processing area" with the new tag/question and updated state in hidden fields.
            *   User clicks "Skip Tag": HTMX POST request. Server determines next tag/question and returns updated partial.
            *   User clicks "Select All": JS selects all images; subsequent "Add Tag" includes all images.
    *   Visual notification confirms tag application (e.g., "X images tagged with 'Y tag'").

4.  **Tag Storage:**
    *   Tags are stored in `.txt` files (e.g., `image001.png` -> `image001.txt`).
    *   Files are created if they don't exist. Tags are appended, comma-separated.
    *   No de-duplication in this version.

5.  **Walkthrough Completion:**
    *   Once all steps/tags are processed, a completion message is displayed in the "tag processing area."

### 4. High-Level UI Elements

*   **Setup Page (`setup_form.html`):**
    *   Character selection dropdown.
    *   Folder path input field.
    *   "Start Tagging Session" button.
*   **Main Tagging Workflow Page (`tagging_workflow.html`):**
    *   **`tagging_notes` Display:** Shown at the start.
    *   **Image Grid:** Thumbnails. Selected images have a bold outline.
    *   **Tag Processing Area (`<div id="tag-processor">` updated by HTMX):**
        *   Displays current step name/description.
        *   Displays current tag or manual input prompt.
        *   Text input field for manual inputs.
        *   Action Buttons ("Add Tag", "Skip Tag", "Select All") with HTMX attributes.
        *   Hidden input fields for `TaggingWorkflowState`.
        *   Hidden input field (`#selectedImagesInput`) for selected image filenames.
    *   **Notifications Area:** For success/error messages (can be part of `#tag-processor` or separate).

### 5. Out of Scope for Initial Version (Future Enhancements)

*   Viewing all current tags for an image *during* the walkthrough.
*   Undo/remove tag functionality during walkthrough.
*   Tag de-duplication.
*   Non-sequential navigation.
*   Custom `dataset_tagger_walkthrough.yaml` upload.
*   Direct editing of `.txt` files via UI.
*   Advanced image filtering/sorting.

### 6. Technical Architecture

This section outlines the technical architecture for the Dataset Tagging Assistant.

#### 6.1. Technology Stack

*   **Backend Framework:** FastAPI (Python)
*   **Database ORM:** SQLModel (for Character tag retrieval)
*   **Templating Engine:** Jinja2
*   **Frontend Interactivity Library:** HTMX
*   **Client-Side Scripting:** Minimal Vanilla JavaScript
*   **Styling:** Existing Bootstrap CSS

#### 6.2. Component Breakdown

##### 6.2.1. Python / FastAPI Backend

*   **Page Handlers & HTMX Endpoints (`app/views/pages/tools/dataset_tagger.py`):**
    *   **`GET /tools/dataset-tagger/setup`**: Renders `setup_form.html`. Fetches Characters for dropdown.
    *   **`POST /tools/dataset-tagger/setup`**: Validates input. Redirects to `GET /tools/dataset-tagger/workflow` with initial state parameters (e.g., `character_id`, `folder_path` in query).
    *   **`GET /tools/dataset-tagger/workflow`**: Renders `tagging_workflow.html`. Parses query parameters to initialize `TaggingWorkflowState`. Loads `dataset_tagger_walkthrough.yaml`. Renders initial `tagging_notes`, image grid, and the first tag/question via `_tag_processing_area.html` partial, including initial hidden state fields.
    *   **`POST /tools/dataset-tagger/workflow/process-tag` (HTMX Target)**:
        *   Receives current `TaggingWorkflowState` (from hidden fields), selected image filenames, action (e.g., "add_tag", "skip_tag", "submit_manual_input"), and potentially manually entered tags.
        *   **Logic:** See Section 8 for detailed tag progression logic.
        *   **Response:** Returns HTML snippet from `_tag_processing_area.html` (and `_notification.html` if needed) containing the next tag/question, updated hidden state fields, and any confirmation.
*   **Utility Functions/Services (could be in `dataset_tagger.py` initially or `app/logic/dataset_tagger_logic.py`):**
    *   Parsing `dataset_tagger_walkthrough.yaml` into `WalkthroughConfig` Pydantic model.
    *   Fetching Character-specific tags (e.g., from `app.crud.character`).
    *   File system operations (listing images, reading/writing `.txt` tag files).

##### 6.2.2. Jinja2 Templates

*   **`app/views/templates/tools/dataset_tagger/setup_form.html`**: Form with Character dropdown, folder path input.
*   **`app/views/templates/tools/dataset_tagger/tagging_workflow.html`**: Main layout. Includes `tagging_notes`, image grid placeholder, and `<div id="tag-processor"></div>`. Links to `dataset_tagger.js`.
*   **`app/views/templates/tools/dataset_tagger/_tag_processing_area.html` (HTMX Partial)**:
    *   Displays current step info, current tag/manual input prompt.
    *   Form (for manual input) or display for current tag.
    *   Action buttons with HTMX attributes.
    *   Hidden input fields for all attributes of `TaggingWorkflowState`.
    *   Hidden input field `<input type="hidden" name="selected_images_input" id="selectedImagesInput">`.
*   **`app/views/templates/tools/dataset_tagger/_image_grid.html` (Partial)**: Loops through images, displaying thumbnails. Each image: `<img>` with `id="image-{{ filename_no_ext }}" data-filename="{{ filename }}"`.
*   **`app/views/templates/tools/dataset_tagger/_notification.html` (HTMX Partial)**: For displaying success/error messages.

##### 6.2.3. HTMX Interactions

*   **Buttons in `_tag_processing_area.html` ("Add Tag", "Skip Tag", Manual Input Form Submit):**
    *   `hx-post="/tools/dataset-tagger/workflow/process-tag"`
    *   `hx-target="#tag-processor"`
    *   `hx-swap="innerHTML"`
    *   `hx-include="form"` (if in a form) or specific input names (e.g., `[name='current_step_index']`, `#selectedImagesInput`).
    *   `hx-indicator` for loading state.

##### 6.2.4. Client-Side JavaScript (`app/views/static/js/tools/dataset_tagger.js`)

*   See Section 9.

#### 6.3. Data Flow Examples

1.  **Initial Setup & Start Workflow:**
    *   User -> `GET /setup` -> `setup_form.html`.
    *   User submits -> `POST /setup` (Character ID, Folder Path).
    *   Server validates -> Redirects to `GET /workflow?character_id=X&folder_path=Y`.
    *   `GET /workflow` -> Renders `tagging_workflow.html` with `tagging_notes`, image grid, and initial `_tag_processing_area.html` content (first tag/question, initial state in hidden fields).

2.  **User Clicks "Add Tag":**
    *   JS has updated `#selectedImagesInput`.
    *   HTMX -> `POST /workflow/process-tag` (with tag, selected images, current `TaggingWorkflowState` from hidden fields).
    *   Server processes, determines next state/tag, renders `_tag_processing_area.html` with new content.
    *   HTMX swaps HTML into `#tag-processor`.

#### 6.4. State Management within Workflow

*   Managed via hidden input fields within the HTMX-updated partial (`_tag_processing_area.html`), representing `TaggingWorkflowState`. The server is the source of truth.

#### 6.5. Error Handling

*   **Setup Form:** Standard FastAPI form validation, re-rendering `setup_form.html` with errors.
*   **HTMX:** `POST /workflow/process-tag` returns HTML snippet (e.g., via `_notification.html`) with error messages if issues occur. Critical errors might result in a full page error.

#### 6.6. File Structure Summary

*   **Python:**
    *   `app/views/pages/tools/dataset_tagger.py`
    *   (Models in `app/models/dataset_tagger_models.py` or within `dataset_tagger.py` for LLM initial pass)
    *   (Logic in `app/logic/dataset_tagger_logic.py` or within `dataset_tagger.py` for LLM initial pass)
*   **Templates:**
    *   `app/views/templates/tools/dataset_tagger/` (containing `setup_form.html`, `tagging_workflow.html`, `_tag_processing_area.html`, `_image_grid.html`, `_notification.html`)
*   **Static:** `app/views/static/js/tools/dataset_tagger.js`
*   **Configuration:** `app/data/dataset_tagger_walkthrough.yaml` (or a more central config location)

### 7. Detailed Data Structures & State

#### 7.1. `dataset_tagger_walkthrough.yaml` Pydantic Models
(To be defined in `app/models/dataset_tagger_models.py` or `dataset_tagger.py`)
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class WalkthroughStep(BaseModel):
    name: str
    description: str
    manual_inputs: Optional[List[Dict[str, str]]] = Field(default_factory=list) # e.g. [{"trigger": "Question?"}]
    automatic_inputs: Optional[List[str]] = Field(default_factory=list)
    character_tags: Optional[List[str]] = Field(default_factory=list) # e.g. ["race", "skin_color"]

class WalkthroughConfig(BaseModel):
    tagging_notes: str
    steps: List[WalkthroughStep]
```

#### 7.2. `TaggingWorkflowState` Pydantic Model

(Used by FastAPI endpoint to parse/manage state from hidden form fields. Define in `app/models/dataset_tagger_models.py` or `dataset_tagger.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class TaggingWorkflowState(BaseModel):
    character_id: str 
    folder_path: str
    
    current_step_index: int = 0
    current_input_type_index_in_step: int = 0 # 0:manual_inputs, 1:pending_manual_tags, 2:automatic_inputs, 3:character_tags
    current_item_index_within_input_type: int = 0 
    
    pending_tags_from_last_manual_input: List[str] = Field(default_factory=list)
    active_manual_input_key: Optional[str] = None 
```

#### 7.3. Character Data Assumption

* A CRUD function `app.crud.character.get_tags(db: Session, character_id: str) -> Dict[str, str]` is assumed to exist.
* It returns a dictionary of character-specific tags, e.g., `{"hair_color": "blonde hair", "race": "elf"}`.

### 8. Core Server-Side Logic for Tag Progression (`POST /tools/dataset-tagger/workflow/process-tag`)

**Inputs:**

* `current_state: TaggingWorkflowState` (parsed from hidden form fields).
* `selected_images: List[str]` (from `#selectedImagesInput` hidden field, comma-separated).
* `action: str` (e.g., "add_tag", "skip_tag", "submit_manual_input").
* `manual_tag_input: Optional[str]` (user's input for a manual question, comma-separated).

**Process:**

1. Load `WalkthroughConfig` from `dataset_tagger_walkthrough.yaml`.
2. If `action == "add_tag"` and `current_tag_to_display` is available:
    * For each `img_filename` in `selected_images`:
        * Append `current_tag_to_display` to `img_filename.txt` (create if not exists).
3. If `action == "submit_manual_input"` and `manual_tag_input` is provided:
    * `current_state.pending_tags_from_last_manual_input = [t.strip() for t in manual_tag_input.split(',') if t.strip()]`
    * `current_state.current_input_type_index_in_step = 1` (move to processing pending manual tags)
    * `current_state.current_item_index_within_input_type = 0`
4. **Advance State & Determine Next Display Item (`next_display_item`, `next_item_type`):**
    * Get `current_walkthrough_step = WalkthroughConfig.steps[current_state.current_step_index]`.
    * Loop/Switch based on `current_state.current_input_type_index_in_step`:
        * **Case 0 (manual_inputs questions):**
            * If `current_state.current_item_index_within_input_type < len(current_walkthrough_step.manual_inputs)`:
                * `question_dict = current_walkthrough_step.manual_inputs[current_state.current_item_index_within_input_type]`
                * `current_state.active_manual_input_key = list(question_dict.keys())[0]`
                * `next_display_item = question_dict[current_state.active_manual_input_key]` (the question text)
                * `next_item_type = "manual_question"`
                * (Server will expect `submit_manual_input` action next)
                * Increment `current_state.current_item_index_within_input_type`.
            * Else (no more manual questions in this step):
                * `current_state.current_input_type_index_in_step = 1` (move to pending tags)
                * `current_state.current_item_index_within_input_type = 0`
                * `current_state.active_manual_input_key = None`
                * (Recursively call or loop to process this new state type)
        * **Case 1 (pending_tags_from_last_manual_input):**
            * If `current_state.current_item_index_within_input_type < len(current_state.pending_tags_from_last_manual_input)`:
                * `next_display_item = current_state.pending_tags_from_last_manual_input[current_state.current_item_index_within_input_type]`
                * `next_item_type = "tag"` (this is the tag to apply)
                * `current_tag_to_display = next_display_item`
                * Increment `current_state.current_item_index_within_input_type`.
            * Else (no more pending manual tags):
                * `current_state.pending_tags_from_last_manual_input = []`
                * `current_state.current_input_type_index_in_step = 2` (move to automatic inputs)
                * `current_state.current_item_index_within_input_type = 0`
                * (Recursively call or loop)
        * **Case 2 (automatic_inputs):**
            * If `current_state.current_item_index_within_input_type < len(current_walkthrough_step.automatic_inputs)`:
                * `next_display_item = current_walkthrough_step.automatic_inputs[current_state.current_item_index_within_input_type]`
                * `next_item_type = "tag"`
                * `current_tag_to_display = next_display_item`
                * Increment `current_state.current_item_index_within_input_type`.
            * Else (no more automatic inputs):
                * `current_state.current_input_type_index_in_step = 3` (move to character tags)
                * `current_state.current_item_index_within_input_type = 0`
                * (Recursively call or loop)
        * **Case 3 (character_tags):**
            * If `current_state.current_item_index_within_input_type < len(current_walkthrough_step.character_tags)`:
                * `char_tag_category = current_walkthrough_step.character_tags[current_state.current_item_index_within_input_type]`
                * `character_specific_tags = crud.character.get_tags(db, character_id=current_state.character_id)`
                * `tag_value = character_specific_tags.get(char_tag_category)`
                * Increment `current_state.current_item_index_within_input_type`.
                * If `tag_value`:
                    * `next_display_item = tag_value`
                    * `next_item_type = "tag"`
                    * `current_tag_to_display = next_display_item`
                * Else (no tag for this category for this char, or no more char tags):
                    * (Recursively call or loop to effectively skip to next char_tag or next phase)
            * Else (no more character tags for this step):
                * Advance to next step:
                    * `current_state.current_step_index += 1`
                    * `current_state.current_input_type_index_in_step = 0`
                    * `current_state.current_item_index_within_input_type = 0`
                    * If `current_state.current_step_index >= len(WalkthroughConfig.steps)`:
                        * `next_item_type = "complete"`
                        * `next_display_item = "Tagging Complete!"`
                    * Else: (Recursively call or loop for new step)
5. **Prepare Response:**
    * Render `_tag_processing_area.html` template with context:
        * `next_display_item`, `next_item_type`.
        * The fully updated `current_state` (for hidden fields).
        * Step name/description if applicable.
        * Notification message.

**(Note: The "recursively call or loop" above means the logic should re-evaluate from step 4 with the updated state until a `next_display_item` is determined or completion is reached.)**

### 9. JavaScript for Image Selection (`app/views/static/js/tools/dataset_tagger.js`)

* On document ready/load:
    * Get the image grid container element.
    * Get the hidden input field `#selectedImagesInput`.
    * Attach a click event listener to the image grid container (event delegation).
* Inside the event listener:
    * If the clicked target is an `<img>` (or its wrapper if images are wrapped):
        * Toggle a 'selected-image-outline' CSS class on the image element.
        * Collect all image elements within the grid that have the 'selected-image-outline' class.
        * Extract the `data-filename` attribute from each selected image.
        * Join these filenames into a comma-separated string.
        * Set the `value` of `#selectedImagesInput` to this string.
* Implement "Select All" / "Deselect All" (if client-side for UX before HTMX submit):
    * Buttons that iterate all images, add/remove 'selected-image-outline', and update `#selectedImagesInput`.

---

That's a great way to approach a complex feature with LLM assistance! Breaking it down into manageable phases with clear goals and testing points is crucial. Here's a development plan tailored for LLM-driven coding, aiming for that barebones foundation first and then building incrementally:

**Guiding Principles for LLM Interaction:**

* **Focused Prompts:** For each task within a phase, provide the LLM with specific sections of the feature document and the current state of the relevant file(s).
* **Iterative Refinement:** Expect to guide the LLM. It might not get it perfect on the first try. Use Cursor's diffing and editing features to correct and steer it.
* **Consolidated Context (Initially):** As you noted, for initial generation of Python logic within a phase, you might ask the LLM to place Pydantic models, helper functions, and endpoint logic all within `app/views/pages/tools/dataset_tagger.py`. Refactor later. Same for Jinja partials within the main template.

---

### Development Plan: Dataset Tagging Assistant

**Phase 0: Project Setup & Basic File Structure (Manual / Minimal LLM)**

* **Goal:** Create the directory structure and empty files. Add router entry.
* **Tasks (Mostly Manual):**
    1. **Create Directories:**
        * `app/views/pages/tools/dataset_tagger/`
        * `app/views/templates/tools/dataset_tagger/`
        * `app/views/static/js/tools/`
        * `app/models/tool_specific/` (if you decide to separate models early)
    2. **Create Empty Python Files:**
        * `app/views/pages/tools/dataset_tagger.py`
        * `app/models/tool_specific/dataset_tagger_models.py` (or plan to keep models in `dataset_tagger.py` for LLM's first pass)
    3. **Create Empty Template Files:**
        * `app/views/templates/tools/dataset_tagger/setup_form.html`
        * `app/views/templates/tools/dataset_tagger/tagging_workflow.html`
        * `app/views/templates/tools/dataset_tagger/_tag_processing_area.html`
        * `app/views/templates/tools/dataset_tagger/_image_grid.html`
        * `app/views/templates/tools/dataset_tagger/_notification.html`
    4. **Create `dataset_tagger_walkthrough.yaml`:**
        * Place `app/data/dataset_tagger_walkthrough.yaml` with the example content from the user's attached file.
    5. **Add Router:**
        * In `app/routes/views.py` (or your project's equivalent), import the router from `app.views.pages.tools.dataset_tagger` and include it in the main view router.
    6. **Add Navigation Link (Placeholder):**
        * In `app/views/templates/base/navbar_logged_in.html` (or equivalent), add a link to `/tools/dataset-tagger/setup` so you can easily access it.
* **Testing:**
    * Start the FastAPI application.
    * Verify you can navigate to `/tools/dataset-tagger/setup` (it will be blank or error out if the endpoint isn't defined, which is the next step).
    * No major application startup errors.

**Phase 1: Setup Page - Rendering and Submission (LLM Focus)**

* **Goal:** Implement the setup page UI, character loading (mocked), form submission, and redirection.
* **LLM Tasks (Targeting `app/views/pages/tools/dataset_tagger.py` and `setup_form.html`):**
    1. **Pydantic Models:**
        * Generate `TaggingWorkflowState`, `WalkthroughConfig`, and `WalkthroughStep` Pydantic models (Section 7.1, 7.2).
    2. **Setup GET Endpoint (`/tools/dataset-tagger/setup`):**
        * Implement the FastAPI route.
        * **Mock Character Fetching:** For now, return a hardcoded list of dictionaries for characters (e.g., `[{"id": "char1_id", "name": "Character Alpha"}]`).
        * Render `setup_form.html` with the request and characters.
    3. **`setup_form.html` Template:**
        * Create the HTML form with a dropdown for `character_id` (populated from context) and a text input for `folder_path`.
    4. **Setup POST Endpoint (`/tools/dataset-tagger/setup`):**
        * Implement the FastAPI route to receive `character_id: str = Form(...)` and `folder_path: str = Form(...)`.
        * **Basic Validation:**
            * Check if `folder_path` is not empty.
            * (Optional: For now, skip `Path(folder_path).is_dir()` if it complicates the LLM too much, add in refinement phase).
        * Perform a `RedirectResponse` to `/tools/dataset-tagger/workflow?character_id=...&folder_path=...` (status code 303).
* **Testing:**
    * Navigate to `/tools/dataset-tagger/setup`. Does the page render with the (mocked) character dropdown?
    * Enter a folder path and select a character. Does submitting the form redirect you to the workflow URL with the correct query parameters? (The workflow page will likely 404 or error, which is fine for this phase).

**Phase 2: Workflow Page - Initial Static Display (LLM Focus)**

* **Goal:** Render the main workflow page, display `tagging_notes`, show images from the specified folder (via image proxy), and a static placeholder for the first tag/question.
* **LLM Tasks (Targeting `app/views/pages/tools/dataset_tagger.py`, `tagging_workflow.html`, `_image_grid.html`, `_tag_processing_area.html`):**
    1. **Image Proxy Endpoint (`/tools/dataset-tagger/image-proxy`):**
        * Implement this endpoint to serve images, including path traversal security checks (Section 6.2.1).
    2. **Workflow GET Endpoint (`/tools/dataset-tagger/workflow`):**
        * Implement the route, receiving `character_id` and `folder_path` from query params.
        * Load and parse `dataset_tagger_walkthrough.yaml` into `WalkthroughConfig`.
        * List image files (e.g., `.png`, `.jpg`) from `folder_path`.
        * **Simplified First Item Display:**
            * For this phase, don't implement the full tag progression logic.
            * Statically determine the *first* item to display: e.g., `tagging_notes` from `WalkthroughConfig`, the first step's name/description, and the text of the *first manual input question* OR the *first automatic tag* from the first step.
            * Pass this static first item information, `tagging_notes`, and image list to `tagging_workflow.html`.
    3. **`tagging_workflow.html` Template:**
        * Display `tagging_notes`.
        * Include `_image_grid.html` partial.
        * Include `_tag_processing_area.html` partial within a `<div id="tag-processor">`.
    4. **`_image_grid.html` Partial:**
        * Loop through image files and create `<img>` tags using the `image-proxy` endpoint for the `src`. Include `data-filename`.
    5. **`_tag_processing_area.html` Partial (Static Initial Version):**
        * Display the static first item (question/tag text) passed from the Python endpoint.
        * Include basic hidden fields for `TaggingWorkflowState` (e.g., `character_id`, `folder_path`, and initial indices like `current_step_index=0`).
* **Testing:**
    * After submitting the setup form, does the workflow page render?
    * Are `tagging_notes` visible?
    * Are images from the test folder correctly displayed? (Test with a folder containing a few images).
    * Is the static first tag/question text visible in the tag processing area?

**Phase 3: Core Tag Progression Logic & Basic "Skip Tag" HTMX (LLM Focus)**

* **Goal:** Implement the server-side logic for advancing through `dataset_tagger_walkthrough.yaml`. Make the "Skip Tag" button functional via HTMX to update the tag processing area.
* **LLM Tasks (Mainly `app/views/pages/tools/dataset_tagger.py` and `_tag_processing_area.html`):**
    1. **Tag Progression Logic (Section 8):**
        * Implement the detailed server-side logic to determine the next display item (`next_display_item`, `next_item_type`) and update `TaggingWorkflowState`. This is the most complex Python part. Start with the pseudocode from Section 8.
    2. **Workflow POST Endpoint (`/tools/dataset-tagger/workflow/process-tag`):**
        * Implement this route.
        * It should receive the `TaggingWorkflowState` attributes from hidden form fields.
        * It should receive `action: str = Form(...)`.
        * Call the tag progression logic (if `action == "skip_tag"` or any other action that advances state).
        * Render the `_tag_processing_area.html` partial with the context for the *next* item and the *updated* `TaggingWorkflowState`.
    3. **Update `_tag_processing_area.html`:**
        * Ensure all `TaggingWorkflowState` attributes are present as hidden input fields.
        * Add a "Skip Tag" button:
            `<button type="submit" name="action" value="skip_tag" hx-post="/tools/dataset-tagger/workflow/process-tag" hx-target="#tag-processor" hx-swap="innerHTML" hx-include="closest form">Skip Tag</button>`
            (Wrap this and other action elements in a `<form>` if not already, to make `hx-include="closest form"` work reliably, or explicitly list all hidden fields in `hx-include`).
* **Testing:**
    * On the workflow page, click "Skip Tag".
    * Does the content within `<div id="tag-processor">` update to show the *next* tag/question from `dataset_tagger_walkthrough.yaml`?
    * Inspect the HTML: Are the hidden `TaggingWorkflowState` input fields updated with the new state values after the HTMX swap?
    * Repeatedly click "Skip Tag". Does it cycle through all defined items in `dataset_tagger_walkthrough.yaml` and eventually show the "Tagging Complete!" message?

**Phase 4: Manual Input & "Add Tag" Functionality (HTMX) (LLM Focus)**

* **Goal:** Enable manual tag submission and the "Add Tag" functionality, including writing to `.txt` files.
* **LLM Tasks (Mainly `app/views/pages/tools/dataset_tagger.py` and `_tag_processing_area.html`):**
    1. **Update `_tag_processing_area.html`:**
        * When `next_item_type == "manual_question"`:
            * Render the text input field (`<input type="text" name="manual_tag_input" required>`).
            * Render a "Submit Tags" button (HTMX-enabled, `action="submit_manual_input"`).
        * When `next_item_type == "tag"`:
            * Add the "Add Tag" button (HTMX-enabled, `action="add_tag"`).
    2. **Update `POST /tools/dataset-tagger/workflow/process-tag` Logic:**
        * Handle `action == "submit_manual_input"`:
            * Populate `current_state.pending_tags_from_last_manual_input`.
            * Set `current_state.current_input_type_index_in_step = 1` and `current_state.current_item_index_within_input_type = 0`.
        * Handle `action == "add_tag"`:
            * **Determine `tag_being_processed`:** Based on the *incoming* state (before advancement), figure out which tag was displayed to the user.
            * Implement the file writing logic to append this tag to the `.txt` files for selected images (initially, `selected_images_input` will be empty as JS isn't integrated yet; the logic should handle an empty list gracefully or you can test by manually setting a value in the hidden field via browser dev tools).
            * Add notification messages.
* **Testing:**
    * When a manual input question appears, can you enter tags (comma-separated) and submit them?
    * Does the UI then correctly step through each of your submitted manual tags?
    * For any displayed tag, click "Add Tag".
        * Verify that `.txt` files are created/updated in your test image folder with the correct tag. (Initially, all images might get tagged if selection isn't working, or no images if `selected_images_input` is empty – focus on the file writing itself).
    * Do appropriate notification messages appear?

**Phase 5: Client-Side Image Selection JavaScript (LLM for JS, Manual Integration)**

* **Goal:** Implement and integrate the JavaScript for image selection.
* **LLM Tasks:**
    1. **Generate JavaScript (`dataset_tagger.js`):** Based on Section 9, generate the JS code for toggling selection class and updating `#selectedImagesInput`.
* **Manual/Cursor Tasks:**
    1. Create `app/views/static/js/tools/dataset_tagger.js` and paste the generated code.
    2. Link this JS file in `tagging_workflow.html`.
    3. Ensure the hidden input `<input type="hidden" name="selected_images_input" id="selectedImagesInput">` is correctly placed within the form in `_tag_processing_area.html` so it's included in HTMX requests.
    4. Define a basic CSS class for `selected-image-outline` (e.g., in a global CSS file or a new `dataset_tagger.css`).
* **Testing:**
    * On the workflow page, can you click images to select/deselect them? Does the visual outline appear/disappear?
    * Use browser developer tools to inspect the `#selectedImagesInput` hidden field. Does its value update correctly with comma-separated filenames of selected images?
    * Now, when you click "Add Tag", verify that only the selected images' `.txt` files are modified.

**Phase 6: Full Character Tag Integration, Refinements & Robust Error Handling (LLM & Manual)**

* **Goal:** Integrate real character tag fetching, polish the UI/UX, and make error handling comprehensive.
* **LLM/Manual Tasks:**
    1. **Character Tag Logic:**
        * In `POST /workflow/process-tag`, when processing `character_tags`, replace mock fetching with actual calls to `app.crud.character.get_tags_dict(db, character_id=current_state.character_id)`. Ensure `db: Session = Depends(get_db)` is correctly injected.
    2. **Error Handling:**
        * Review all file operations, YAML loading, image proxy for potential errors and add `try-except` blocks. Return appropriate error messages via the `_notification.html` partial or by re-rendering parts of the page with error states.
        * Handle cases like `dataset_tagger_walkthrough.yaml` not found, invalid folder, no images in folder more gracefully in `GET /workflow`.
    3. **UI/UX Refinements:**
        * Ensure `hx-indicator` is used effectively for loading states.
        * Make notifications clear and well-styled.
        * Test usability across different `dataset_tagger_walkthrough.yaml` configurations.
* **Testing:**
    * Test with real characters and their tags from the database. Do character-specific tags display and apply correctly?
    * Test various error conditions: non-existent folder, invalid character ID in URL, `dataset_tagger_walkthrough.yaml` missing or malformed, unwritable tag files (if permissions can be simulated).
    * Perform a full end-to-end test of the entire workflow with multiple images and varied tags.

---
