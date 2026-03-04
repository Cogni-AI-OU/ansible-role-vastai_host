# Vast.ai Host Scripts

This directory contains the core scripts used for Vast.ai host setup and
management. These scripts are deployed by the Ansible role to configure GPU
hosts for the Vast.ai marketplace.

## Scripts Overview

### Core Installation & Setup

#### install.py

**Purpose**: Main installation script for setting up Vast.ai host software and
dependencies.

**Location**: `files/vast.ai/install.py`

**Source**: <https://s3.amazonaws.com/public.vast.ai/install>

**Functionality**:

- Installs NVIDIA drivers and CUDA toolkit
- Sets up the vastai_kaalia daemon user and data directory
- Configures Docker for GPU workloads
- Performs system compatibility checks
- Handles backup and restore operations

**Usage**:

```bash
sudo python3 install.py
```

#### update_scripts.sh

**Purpose**: Updates Vast.ai scripts and configures scheduled tasks.

**Location**: `files/vast.ai/update_scripts.sh`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/update_scripts.sh>

**Functionality**:

- Downloads latest versions of Vast.ai scripts from S3
- Updates cron jobs for periodic tasks
- Installs additional system dependencies (tshark)
- Configures automated script updates

**Usage**:

```bash
sudo ./update_scripts.sh
```

### Monitoring & Reporting

#### send_mach_info.py

**Purpose**: Collects detailed machine information and sends it to Vast.ai servers.

**Location**: `files/vast.ai/send_mach_info.py`

**Source**: <https://s3.amazonaws.com/vast.ai/send_mach_info.py>

**Functionality**:

- Gathers hardware specifications (CPU, GPU, RAM, storage)
- Collects PCI device information and IOMMU groups
- Reports system capabilities and available resources
- Sends periodic updates to Vast.ai marketplace

**Usage**:

```bash
python3 send_mach_info.py
```

#### read_packs.py

**Purpose**: Monitors network traffic and reads container IP assignments.

**Location**: `files/vast.ai/read_packs.py`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/read_packs.py>

**Functionality**:

- Uses tshark to capture network packets on docker0 interface
- Correlates captured traffic with Docker container IPs
- Monitors network activity for billing and security purposes
- Runs periodically via cron job

**Usage**:

```bash
python3 read_packs.py
```

#### report_copy_success.py

**Purpose**: Reports successful data copy operations to Vast.ai.

**Location**: `files/vast.ai/report_copy_success.py`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/report_copy_success.py>

**Functionality**:

- Monitors file copy operations
- Reports completion status to Vast.ai servers
- Tracks data transfer success/failure metrics

**Usage**:

```bash
python3 report_copy_success.py
```

### Virtual Machine Management

#### enable_vms.py

**Purpose**: Manages virtual machine enablement and PCI passthrough configuration.

**Location**: `files/vast.ai/enable_vms.py`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/enable_vms.py>

**Functionality**:

- Configures IOMMU groups for PCI passthrough
- Enables/disables VM functionality on the host
- Manages GPU and device assignment to virtual machines
- Handles libvirt integration for VM management

**Usage**:

```bash
sudo python3 enable_vms.py on    # Enable VMs
sudo python3 enable_vms.py off   # Disable VMs
```

#### sync_libvirt.sh

**Purpose**: Synchronizes libvirt configuration for virtual machine management.

**Location**: `files/vast.ai/sync_libvirt.sh`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/sync_libvirt.sh>

**Functionality**:

- Updates libvirt daemon configuration
- Ensures proper VM networking setup
- Synchronizes virtual machine definitions

**Usage**:

```bash
sudo ./sync_libvirt.sh
```

### Container Management

#### list_container_ips.sh

**Purpose**: Lists IP addresses of running Docker containers.

**Location**: `files/vast.ai/list_container_ips.sh`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/list_container_ips.sh>

**Functionality**:

- Queries Docker for running containers
- Extracts IP addresses from container network settings
- Outputs JSON-formatted IP mapping for monitoring

**Usage**:

```bash
./list_container_ips.sh
```

#### purge_stale_cdi.py

**Purpose**: Removes stale Container Device Interface (CDI) configuration files.

**Location**: `files/vast.ai/purge_stale_cdi.py`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/purge_stale_cdi.py>

**Functionality**:

- Scans /etc/cdi/ for CDI configuration files
- Identifies configs for non-existent containers
- Removes stale CDI YAML files to prevent conflicts
- Maintains clean CDI configuration state

**Usage**:

```bash
sudo python3 purge_stale_cdi.py
```

### Testing & Diagnostics

#### test_nvml_error.sh

**Purpose**: Tests for NVIDIA Management Library (NVML) initialization errors.

**Location**: `files/vast.ai/test_nvml_error.sh`

**Source**: <https://s3.amazonaws.com/vast.ai/test_nvml_error.sh>

**Functionality**:

- Launches a Docker container with NVIDIA GPU access
- Tests NVML initialization in containerized environment
- Detects "Unknown Error" issues that can affect GPU availability
- Validates GPU device access after systemd daemon reloads

**Usage**:

```bash
sudo ./test_nvml_error.sh
```

#### test_NCCL.py

**Purpose**: Tests NVIDIA Collective Communications Library (NCCL) functionality.

**Location**: `files/vast.ai/test_NCCL.py`

**Source**: <https://s3.amazonaws.com/vast.ai/test_NCCL.py>

**Functionality**:

- Tests multi-GPU communication using NCCL
- Validates PyTorch distributed training capabilities
- Performs GPU-to-GPU data transfer tests
- Checks for NCCL-related performance issues

**Usage**:

```bash
python3 test_NCCL.py --num_gpus 2 --backend nccl
```

#### start_self_test.sh

**Purpose**: Initiates self-test procedures for the Vast.ai host.

**Location**: `files/vast.ai/start_self_test.sh`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/start_self_test.sh>

**Functionality**:

- Runs comprehensive system diagnostics
- Tests GPU functionality and availability
- Validates network connectivity
- Performs automated health checks

**Usage**:

```bash
sudo ./start_self_test.sh
```

### Utilities

#### vast.py

**Purpose**: Vast.ai command-line interface tool.

**Location**: `files/vast.ai/vast.py`

**Source**: <https://raw.githubusercontent.com/vast-ai/vast-cli/master/vast.py>

**Functionality**:

- Command-line interface for Vast.ai marketplace
- Instance management and monitoring
- API interaction capabilities

**Usage**:

```bash
python3 vast.py --help
```

#### vast_fuse

**Purpose**: FUSE-based filesystem utilities for Vast.ai.

**Location**: `files/vast.ai/vast_fuse`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/vast_fuse>

**Functionality**:

- Provides filesystem mounting capabilities
- Handles data transfer operations
- Manages storage integration

**Usage**:

```bash
./vast_fuse [options]
```

#### update_launcher.sh

**Purpose**: Updates the launcher component of Vast.ai host software.

**Location**: `files/vast.ai/update_launcher.sh`

**Source**: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/update_launcher.sh>

**Functionality**:

- Downloads updated launcher binaries
- Updates launcher configuration
- Manages launcher service restarts

**Usage**:

```bash
sudo ./update_launcher.sh
```

## Deployment

These scripts are automatically deployed by the Ansible role to
`/var/lib/vastai_kaalia/` on target hosts. The role ensures proper permissions
and execution capabilities are set.

## Source URLs

- Primary: <https://s3.amazonaws.com/vast.ai/>
- Public: <https://s3.amazonaws.com/public.vast.ai/>
- Kaalia scripts: <https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/>
- CLI Tool: <https://raw.githubusercontent.com/vast-ai/vast-cli/master/vast.py>
