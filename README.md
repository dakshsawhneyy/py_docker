# py-docker: Python Container Runtime

A lightweight, OCI-compliant container runtime implementation in Python and Bash Scripting. This project mimics the core functionality of the Docker engine, providing deep insights into Linux process isolation, filesystem jailing, and container image supply chains.

## Project Overview

This tool demonstrates how containers work at the kernel level by implementing the two fundamental pillars of containerization:

1. **Process Isolation:** Utilizing Linux Namespaces to create isolated execution environments.
2. **Filesystem Isolation:** Implementing `chroot` jails to restrict file access to the container image.

It operates without dependencies on existing container runtimes (like containerd or runc), interacting directly with the Linux kernel and the Docker Registry API.

## Architecture

### 1. The Puller (Supply Chain)

Implements a custom client for the Docker Registry HTTP API V2.

* **Authentication:** Handles bearer token retrieval from `auth.docker.io`.
* **Manifest Parsing:** Parses OCI Manifest Lists (Schema 2) to correctly identify and fetch `amd64/linux` layers.
* **Layer Extraction:** Downloads and extracts gzip-compressed image layers into a local filesystem jail.

### 2. The Runtime (Engine)

Manages the lifecycle of the container process using low-level system calls via Python's `ctypes` library.

* **Namespace Isolation:**
* `CLONE_NEWPID`: Creates a new PID namespace, ensuring the containerized process runs as PID 1.
* `CLONE_NEWNS`: Creates a new Mount namespace to prevent container mounts (like `/proc`) from leaking to the host.


* **Filesystem Jailing:** Uses `os.chroot` to change the root directory of the calling process to the extracted image path.
* **Resource Mounting:** Automates the mounting of the `/proc` pseudo-filesystem to enable process monitoring tools (e.g., `ps`, `top`) within the container.

## Prerequisites

* **OS:** Linux (Kernel 4.0+ recommended)
* **Privileges:** Root access (required for `unshare` and `chroot` syscalls)
* **Dependencies:** Python 3.x, `requests` library

## Installation

```bash
git clone https://github.com/dakshsawhneyy/py-docker.git
cd py-docker
pip install requests

```

## Usage

**1. Pull an Image**
Fetches the latest Alpine Linux image from the official Docker Hub registry.

```bash
sudo python3 my_docker.py pull alpine

```

**2. Run a Container**
Executes a command inside the isolated environment.

```bash
sudo python3 my_docker.py run /bin/sh
```
