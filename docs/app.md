# Risa

## Overview

Risa is a complete system to managing and viewing Risa data.

## Components

### Servers

- Server Host (AWS EC2 Instance)
    - Hosts:
        - Risa Host
        - Postgres (Database)
- Server Local (Local Machine/Laptop)
    - Hosts:
        - Risa Local
        - Risa Dev
- Server Playground (Containerized/RunPod)
    - Hosts:
        - Risa Playground
        - AI Web Apps (A1111, etc.)

### Risa Apps (Web Apps)

- Risa Host (Server Host)
- Risa Local (Server Local)
- Risa Dev (Server Local)
- Risa Playground (Server Playground)

### Docker Images

- docker-risa-playground (docker image for Risa Playground)
    - for runpod
    - for vast.ai/standalone Instance w/o persistent disk

### CLI Tools

- runpod (custom cli tool to manage runpod instances)
- runpodctl (cli tool to manage runpod, from runpod.io)

## External Services

- Cloudlfare R2 (S3 Object Storage)
- AWS EC2 (Risa Host)
- Runpod (GPU Cloud)
- Docker.io (hosts Risa Playground docker images)

## Features

### Risa (Web App)

    - Idle Watcher: Watches for GPU Idle or System Idle and performs actions, like starting the job queue.
    - Job Queue:
    
### Docker

---

# Risa

## What is Risa

Risa is a application ecosystem where each component works together to help the end user scrape, generate, edit, maintain, and view related content.

Risa works in the background as much as possible, automating the collection of new media, as well as the organization and viewing of already collected content.

## Definitions

| Key                         | Value                                                                                                                                   |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Collection                  | A collection of related content.                                                                                                        |
| Risa                        | Application to scrape, generate, edit, maintain, and view the collections content.                                                      |
| Risa Network                | The suite of Risa deplouments that interact with each other: rLocal, rHost, rPlayground.                                                |
| ENV_NAME                    | "local" \| "host" \| "dev" \| "playground"                                                                                              |
| RisaCollector/Collector | Feature that automatically scrapes, downloads, and organizes content.                                                                   |
| RisaAI/rAI               | Feature that generates, organizes, and manages AI Generated media works.                                                                |
| RisaFap                     | Feature that is the front-facing, client focused front end. Simple and too the point. Has one purpose, create a fap friendly front end. |

## Risa Network

The Risa Application can have different DEPLOYMENT_TYPE's:

### Local

- **Location**:
   	- Resides on local computer
- **Function**:
   	- Provides local computer access
- **Availability**:
   	- Only running/active when the computer is active and running the local server.
- **Access**:
   	- Has access to local files
   	- Has access to local backups
   	- Has access to the internet
- **Hosts**:
   	- Web App: rLocal

### Host

- **Location**:
   	- Resides on AWS servers
- **Function**:
   	- Provides 24/7 remote access.
   	- The always-on core of the system.
- **Availability**:
   	- Available 24/7. Always On.
- **Access**:
   	- Has access to the Master Database
   	- Has access to the internet
- **Hosts**:
   	- Web App: rHost
      		- Web App: rCollector
      		- Web App rFAP
   	- API: rHostAPI
   	- DB: Master Database

### Playground

- **Location**:
   	- Deployed on-demand. Resides on runpod/vast.ai/etc container.
   	- Is deployed in a container that also hosts all the Playground Web Apps (A1111, Kohya_ss, ComfyUI, etc.)
- **Function**:
   	- Provides access to all the Playground web apps.
- **Availability**:
   	- Only when the container is spun up.
- **Access**:
   	- Has access to the container's host machine.
   	- Has access to all the web apps
- **Hosts**:
   	- Web App: rPlayground

### Dev

- **Location**:
   	- Resides local development machine
- **Function**:
   	- Used for development. Provides access to everything.
- **Availability**:
   	- Available when the user chooses to run.
- **Access**:
   	- Has access to the Dev Database
   	- Has all accesses from all other deployment types
   	- Has access to the internet
- **Hosts**:
   	- All.

## Features: Wishlist

- Risa(python-fastapi-sqlmodel-stack):
- Logic
- Services
   	- Scraper

- **rLocal**
   	- Managers:
      		- Tasks (Crons, jobs, etc)
   	- rCollector
   	- rAI
      		- Import Checkpoints, LORAs from local hub
- **rHost**
   	- Managers:
      		- Character Manager
      		- Scrapers
      		- Tasks (Crons, jobs, etc)
   	- API:
   	- rAI
      		- Import Checkpoints, LORAs from remote files
      		- Maintains rPayground Processing Queue
- **rPayground**
   	- rAI
      		- Import Checkpoints, LORAs from Playground container
      		- Gets processing queue from rHost.

## Risa Fap

RisaFap refers to any app/workflow that allows for one handed, simple and liner execution. RisaFap MUST be mobile friendly, and mobile first.

- Characters
- Feed
   	- New AI Media
      		- By Date
      		- By Character
      		- By Base Model
      		- By Checkpoint
   	- New Scraped Media
- Browse
   	- Character
   	- AI

- Image Browser
   	- Info Overlay:
      		- Base Model
      		- Checkpoint
      		- Loras
      		- Character
      		- Character Lora
   	- Actions:
      		- Save
      		- Dislike/Like
         			- Dislike/Like Base Model
         			- Dislike/Like Checkpoint
         			- Dislike/Like Lora
         			- Dislike/Like Lora: Character Likeness
         			- Dislike/Like Lora: Prompt Adherence
         			- Dislike/Like Prompt
         			- Dislike/Like Prompt: Pose
      		- Delete
				- Delete All Inbox Items from this "run" (prompt?)
				- Delete All Inbox Items for this checkpoint
				- Delete All Inbox Items for this character lora
				- Delete All Inbox Items for this character lora + checkpoint
      		- View Metadata
         			- Metadata
         			- Prompt
         			- Character
			- Report Error
				- Character Lora not compatible with checkpoint
				- Other Lora not compatible with checkpoint
   	- Services:
      		- Job Queue
         			- Generate Similar: For Character
         			- Generate Similar: For All Characters
      		- Send To
			-
      		- Browser More...
         			- Browse more by Character
         			- Browse more by Checkpoint

## Stats

Stats section should include all sorts of stats about risa, the media, the collection, etc. Any stat can go here. Most viewed character, least viewed, most generated, etc.

## Navigation

- Home (Dashboard)
- RisaFap
   	- RisaFap Dashboard
   	- Workflows
- rPlayground
   	- RunPod
   	- ComfyUI
   	- A1111
   	- Kohya_ss
   	-
- Browse
   	- Saved
   	- AI Inbox
   	- Collector Inbox
- Manage
   	- Characters
   	- rAI
      		- Base Models
      		- Checkpoints
      		- Extra Networks
      		- Characters
   	- rCollector
      		- Subscriptions
      		- Scrapers
   	- Settings
   	- Jobs
      		- All Jobs
      		- rLOCAL Jobs
      		- rHOST Jobs
      		- rPLAYGROUND Jobs
      		- rDev Jobs
- Tools
    - rAI
      		- rAI Scripts
         			- Fix Civitai Filenames
      		- Safetensor Importer
      		- Dataset Tagger
    - rCollector
      		- rCollector Scripts
    - Backups
   	- System
   	- Logs
- Stats
- Network
    - Network Dashboard
   	   	- Instances
          		- rLOCAL
         			- Dashboard
         			- Jobs
          		- rHOST
         			- Dashboard
         			- Jobs
          		- rPLAYGROUND
         			- Dashboard
         			- Jobs
          		- rDEV
         			- Dashboard
         			- Jobs
- Dev
   	- Dev Dashboard
   	- Github Repo
   	- Create Github Issue
