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
- Server Playground (Containerized)
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

    - Idle Watcher: Watches for GPU Idle and starts job queue
    - Job Queue
    
### Docker
