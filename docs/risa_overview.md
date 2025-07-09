---
llm_doc: true
audience: LLM
maintainer: LLM
last_updated: 2025-07-08
project: risa
purpose: High-level, living documentation for LLM understanding and maintenance
---

# Risa Project Documentation

## LLM Maintenance Notes

- After each commit, review code changes and update only the relevant sections.
- When adding new features, create a new section or subsection as appropriate.
- When removing features, mark the section as deprecated before deleting.
- Always update the Changelog with a summary of changes.
- Use explicit section boundaries (<!-- SECTION: ... -->) for each major section.
- Reference main codebase files for each feature or API.

## Changelog

- 2024-06-09: Revamped to LLM-optimized format, added metadata, maintenance notes, changelog, explicit section boundaries, and codebase references.
- 2024-06-08: Added Dataset Tagger tool section.
- 2024-07-08: Added Technology Stack section.

## Table of Contents

1. Overview
2. Technology Stack
3. Configuration
4. Features & Usage
5. API Reference
6. Project Architecture
7. Glossary

<!-- SECTION: 1. Overview -->
## 1. Overview

Risa is a comprehensive system for managing, viewing, and generating AI media, particularly for Stable Diffusion models. It operates as a distributed network of applications, each tailored for a specific environment (local development, a remote host, and a GPU-powered "playground"). This allows for a streamlined workflow from data management and training on a powerful remote machine to organizing and viewing assets from a local machine or a central server.

The system is built on a modern Python stack, featuring a FastAPI backend for both REST API and web UI, SQLModel for database interaction, and a sophisticated job queue system for handling background tasks.

### Key Concepts

- **Risa Network**: The core architectural concept is a network of interconnected instances, each with a specific role:
    - **r|HOST**: The central, always-on server (e.g., on a cloud provider) that holds the master database.
    - **r|PLAYGROUND**: An on-demand, GPU-enabled environment (e.g., RunPod) for running AI tasks like model training and image generation. It hosts applications like AUTOMATIC1111's Web UI and Kohya\_ss.
    - **r|LOCAL**: The instance running on a user's local machine for tasks like dataset preparation and file management.
    - **r|DEV**: A local development instance with access to all components.
- **State Management**: The system maintains and synchronizes the state (e.g., IP address, system status, running apps) of each instance in the network, visible through a central dashboard.
- **Job Queue**: A powerful background task system powered by Huey. It allows for queueing various jobs, such as running scripts, executing commands, or making API calls. The queue supports prioritization and can be managed across different environments.
- **App Manager**: A feature available in the `r|PLAYGROUND` environment that allows users to start, stop, and restart external AI applications (like A1111 WebUI) directly from the Risa dashboard.
- **The Hub**: A centralized directory structure for storing and organizing AI models, including checkpoints and LoRAs (`SDExtraNetwork`), which Risa can discover and import into its database.
<!-- ENDSECTION -->

<!-- SECTION: 2. Technology Stack -->
## 2. Technology Stack

Risa is built on a modern, scalable technology stack designed for distributed AI workflows and real-time operations.

### Backend

- **FastAPI**: High-performance Python web framework providing both REST API and web UI
- **SQLModel**: SQLAlchemy-based ORM for database operations with Pydantic integration
- **SQLite**: Lightweight database for local storage and development
- **Alembic**: Database migration management and version control

### Authentication & Security

- **JWT**: JSON Web Tokens for stateless authentication
- **OAuth2**: Password flow implementation for secure API access
- **bcrypt**: Password hashing and verification
- **CORS**: Cross-origin resource sharing configuration

### Job/Task Processing

- **Huey**: Lightweight task queue for background job processing
- **Redis**: Optional message broker for distributed job queues
- **Priority Queues**: Job prioritization system (highest to lowest)

### Frontend & UI

- **Jinja2**: Server-side templating engine for dynamic HTML generation
- **Bootstrap 5**: CSS framework for responsive, modern UI components
- **JavaScript**: Client-side interactivity and real-time updates
- **WebSockets**: Real-time communication for job status and app manager updates

### Development & Deployment

- **Poetry**: Dependency management and packaging
- **Docker**: Containerization support for consistent deployments
- **Uvicorn**: ASGI server for running FastAPI applications
- **Loguru**: Advanced logging with structured output

### External Integrations

- **rsync**: File synchronization between environments

<!-- ENDSECTION -->

<!-- SECTION: 3. Configuration -->
## 3. Configuration

Application behavior is controlled by environment variables defined in `app/models/settings.py`. These can be set in an `.env` file.

**Key Environment Variables:**

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `ENV_NAME` | The name of the current environment. **Required**. | `dev`, `local`, `host`, `playground` |
| `DB_URL` | The SQLAlchemy database connection string. | `sqlite:///./app/data/database.sqlite3` |
| `PROJECT_NAME` | The name of the project. | `risa` |
| `FIRST_SUPERUSER_USERNAME` | Username for the initial superuser account. | `admin` |
| `FIRST_SUPERUSER_PASSWORD` | Password for the initial superuser account. | `changeme` |
| `FIRST_SUPERUSER_EMAIL` | Email for the initial superuser account. | `admin@example.com` |
| `JWT_ACCESS_SECRET_KEY` | Secret key for JWT access tokens. **Required**. | A long, random string. |
| `JWT_REFRESH_SECRET_KEY`| Secret key for JWT refresh tokens. **Required**. | A long, random string. |
| `RISA_HOST_BASE_URL` | The base URL for the `rHost` instance. | `http://localhost:5000` |
| `HUB_PATH` | The absolute path to the "Hub" directory for models. | `/path/to/models/hub` |
| `EXPORT_API_KEY` | A secret key required for accessing export endpoints. **Required**. | A long, random string. |
| `WORKSPACE_PATH` | The root path for application data on the server. | `/workspace` |
| `IDLE_TIMEOUT_MINUTES` | In the `playground` environment, the number of minutes of GPU idle time before triggering a job. | `30` |
<!-- ENDSECTION -->

<!-- SECTION: 4. Features & Usage -->
## 4. Features & Usage

Risa provides a web interface for all its core functionalities.

### 4.1 Dashboard

The main dashboard is the central hub for monitoring the entire Risa network.

- **App Manager**: (Playground only) Start, stop, restart, and view logs for external AI applications like A1111 WebUI and Kohya\_ss GUI.
- **RunPod Status**: Displays live stats for the RunPod instance, including GPU usage, memory, and disk space.
- **Jobs Queue**: A real-time view of the jobs queue, showing pending, running, and completed tasks. You can also control the Huey consumer process from here.
- **Scripts**: A panel to launch predefined background scripts via the job queue.
- **Network State**: An overview of all connected Risa instances (`dev`, `local`, `host`, `playground`), showing their last-updated time and status.

### 4.2 Data Management

Risa provides dedicated sections for managing the core data models of the application.

#### Characters

Characters are central entities representing a person or concept. They link together various `SDExtraNetwork` models (LoRAs).

- **Create/View/Edit/Delete** characters.
- Associate LoRAs with characters.
- Define detailed attributes for a character (physical appearance, clothing, etc.) which can be used for dataset tagging.

#### SD Base Models, Checkpoints, and Extra Networks

These sections allow for granular management of your Stable Diffusion assets.

- **SD Base Models**: Define base model types (e.g., `SDXL`, `Pony`).
- **SD Checkpoints**: Manage specific `.safetensors` checkpoint files, linking them to a base model.
- **SD Extra Networks**: Manage LoRA/LyCORIS files. Each is linked to a `Character` and a `SDBaseModel`. You can specify trigger words, weights, and usage rules (e.g., restrict to realistic models only).

### 4.3 Tools

Risa includes several built-in tools to streamline AI workflows.

#### Safetensor Import Helper

- **Path**: `/tools/safetensor-import-helper`
- This tool scans the "Hub" directory for `.safetensors` files that are not yet in the Risa database.
- It intelligently categorizes them as Checkpoints or LoRAs based on their location.
- Provides a one-click import button to create `SDCheckpoint` or `SDExtraNetwork` entries from the discovered files, pre-filling information like name, SHA256 hash, and activation text from associated `.json` files.

#### Dataset Tagger

- **Path**: `/tools/dataset-tagger/setup`
- A comprehensive UI for tagging image datasets for AI training.
- It follows a guided workflow defined in a YAML configuration file.
- **Features**:
    - Walkthrough-based tagging process.
    - Image grid with thumbnail generation.
    - Ability to select multiple images and apply/remove tags in bulk.
    - Fetches character-specific tags automatically.
    - Handles manual text input for custom tags.

### 4.4 Scripts Runner

The application provides a UI to run predefined scripts as background jobs. Each script has a dedicated modal for inputs.

- **Generate XY for Lora Epochs**: Connects to the A1111 API to generate an XY plot comparing different LoRA training epochs.
- **Choose Best Epoch**: A workflow script to manage LoRA training outputs. It moves the user-selected "best" epoch safetensor to the main hub directory and deletes the other epoch files to save space. It can also create a job on the `rLocal` instance to sync the new file.
- **Fix Civitai Download Filenames**: A utility script to a common issue with filenames from a popular A1111 extension.
- **Rsync Files**: A powerful tool to synchronize files or directories between different Risa environments (e.g., push trained models from `rPlayground` to `rHost`).

<!-- ENDSECTION -->

<!-- SECTION: 5. API Reference -->
## 5. API Reference

Risa exposes a RESTful API under the `/api/v1/` prefix.

### Key Endpoints

- **Authentication**:
    - `POST /login/access-token`: Obtain JWT tokens using username and password.
    - `POST /login/refresh-token`: Refresh an access token.

- **CRUD Operations**: Standard `GET`, `POST`, `PUT`, `DELETE` endpoints are available for:
    - `/characters`
    - `/sd-base-models`
    - `/sd-checkpoints`
    - `/sd-extra-networks`
    - `/jobs`
    - `/job-schedulers`

- **State Management**:
    - `GET /state/instance`: Get the current state of the instance.
    - `GET /state/network`: Get the state of all instances in the network.
    - `POST /state/recieve-state`: Endpoint for an instance to push its state to the host. (Requires `EXPORT_API_KEY`).

- **App Manager**:
    - `POST /app_manager/{app_id}/start`: Start an external application.
    - `POST /app_manager/{app_id}/stop`: Stop an external application.
    - `POST /app_manager/{app_id}/restart`: Restart an external application.

- **WebSockets**:
    - `WS /ws/job-queue`: Provides real-time updates on job statuses and consumer health.
    - `WS /ws/app_manager`: Provides real-time updates for the App Manager, including application status and log streaming.

<!-- ENDSECTION -->

<!-- SECTION: 6. Project Architecture -->
## 6. Project Architecture

The application is logically divided into two main parts: `app` (the specific Risa project implementation) and `framework` (a reusable core for FastAPI applications).

- **`app`**: Contains project-specific models, business logic (`logic`), API endpoints, frontend handlers, and scripts.
- **`framework`**: Provides the base components for a modern web application, including:
    - Core services for the database (`db.py`), server (`server.py`), security (`security.py`), and logging (`logger.py`).
    - Generic CRUD base classes (`crud/base.py`).
    - Base models for users, jobs, etc.
    - A generic job queue and scheduler system.

### Data Flow for State Management

1. Each Risa instance runs a recurring background task (`update_instance_state`) every 4 minutes.
2. This task gathers system stats (CPU, GPU, Disk), RunPod info (if applicable), and other configuration details into an `InstanceState` model.
3. The state is saved to the instance's local database.
4. When a user accesses a page like the Dashboard, the `rHost` instance queries its own database to retrieve the last known state for all registered network instances (`dev`, `local`, `host`, `playground`), presenting a unified view of the network's health.

### Background Job Execution

1. Jobs are created via the API and stored in the database with a `pending` or `queued` status.
2. The `Huey` consumer process, running in the background, periodically checks for jobs.
3. Jobs are picked from the queue based on priority (`highest` to `lowest`).
4. The consumer executes the job (e.g., runs a shell command or a Python script from the `app/scripts` directory).
5. The job's status is updated in the database (`running` -> `done`/`failed`).
6. The `job_queue_ws` WebSocket manager broadcasts the updated job list to all connected clients, ensuring the UI updates in real-time.

<!-- ENDSECTION -->

<!-- SECTION: 7. Glossary -->
## 7. Glossary

| Term | Definition |
| :--- | :--- |
| Risa Network | The suite of Risa deployments that interact: rLocal, rHost, rPlayground, rDev. |
| rHost | Central, always-on server holding the master database. |
| rPlayground | On-demand, GPU-enabled environment for AI tasks. |
| rLocal | Local machine instance for dataset prep and file management. |
| rDev | Local development instance with access to all components. |
| SDBaseModel | Base model type for Stable Diffusion (e.g., SDXL, Pony). |
| SDCheckpoint | Specific checkpoint file for a base model. |
| SDExtraNetwork | LoRA/LyCORIS file, linked to a Character and SDBaseModel. |
| The Hub | Central directory for storing and organizing AI models. |
| App Manager | Feature to start/stop/restart external AI apps from dashboard. |
| Job Queue | Background task system powered by Huey. |
| InstanceState | Model representing the state of a Risa instance. |
| Huey | Python task queue used for background jobs. |
| RunPod | GPU cloud provider used for rPlayground. |
| LoRA | Low-Rank Adaptation file for Stable Diffusion. |
| LyCORIS | Alternative to LoRA for model adaptation. |
| CRUD | Create, Read, Update, Delete operations. |
| WebSocket | Real-time communication protocol used for job/app updates. |

<!-- ENDSECTION -->
