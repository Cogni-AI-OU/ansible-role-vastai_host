#!/usr/bin/env python3
import json
import subprocess
import sys
from argparse import ArgumentParser
import re
import os
import traceback
import requests

server_url = "https://console.vast.ai"


def webserver_call(url, data):
    m_id = get_machine_id()
    return requests.post(url, json=data,headers={ "Authorization": f"Bearer {m_id}"})

def get_machine_id():
    with open("/var/lib/vastai_kaalia/machine_id") as mid_file:
        return mid_file.read()

def get_current_gpus():
    """Get list of current GPU UUIDs using nvidia-smi."""
    try:
        result = subprocess.run(['nvidia-smi', '-L'], 
                                capture_output=True, 
                                text=True, 
                                check=True)
        # Extract UUIDs from nvidia-smi output
        # Example line: "GPU 0: NVIDIA A100-SXM4-40GB (UUID: GPU-123456...)"
        uuids = re.findall(r'GPU-[\w-]+', result.stdout)
        return uuids
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get GPU list: {e}")

def read_nvidia_smi_json(filepath='/var/lib/vastai_kaalia/data/nvidia_smi.json'):
    """Read and parse the nvidia-smi.json file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"nvidia-smi.json not found at {filepath}")
    except json.JSONDecodeError:
        raise RuntimeError("Invalid JSON format in nvidia-smi.json")

def write_nvidia_smi_json(data, filepath='/var/lib/vastai_kaalia/data/nvidia_smi.json'):
    """Write updated data to nvidia-smi.json file."""
    with open(filepath, 'w') as f:
        json.dump(data, f)

def replace_gpu_uuid(data, old_uuid, new_uuid):
    """Replace old GPU UUID with new one in the JSON data."""
    if data.get(old_uuid, False):
        data[new_uuid] = data[old_uuid]
        del data[old_uuid]
    return data

def get_vast_containers():
    """Get list of Vast.ai container IDs."""
    try:
        result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}'], 
                                capture_output=True, 
                                text=True, 
                                check=True)
        # Filter for Vast.ai containers (those starting with C. followed by numbers)
        containers = result.stdout.strip().split('\n')
        vast_containers = []
        for container in containers:
            if container and re.search(r'C\.\d+', container):
                    vast_containers.append(container)
        return vast_containers
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get container list: {e}")

def handle_container(container_name, old_uuid, new_uuid):
    """Handle container that uses the old GPU."""
    try:
        inspect_result = inspect_container(container_name)
        cont_uuids = get_gpus_used(inspect_result)
        if old_uuid in cont_uuids:
            task_info = {
                    "task_id" : container_name[2:],
                    "task_name" : "commit_container",
                    "op" : "rebuild"
            }
            task_context = {
                "container_name": container_name
            }
            cont_uuids.remove(old_uuid)
            cont_uuids.append(new_uuid)
            
            env_override_str = ",".join(cont_uuids)
            task_context["env_override"] = { "NVIDIA_VISIBLE_DEVICES" : env_override_str }
            res = subprocess.run(["/var/lib/vastai_kaalia/task_handlers/commit_container.py", json.dumps(task_info), json.dumps(task_context)],
                capture_output=True,
                text = True
            )
            if res.stderr or res.returncode != 0:
                print(res.stdout)
                raise RuntimeError(res.stderr or f"commit_container.py returned non-zero exit code: {res.returncode}")
            if res.stdout != "success":
                raise RuntimeError(res.stdout)
            else:
                return True
        return False
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError) as e:
        print(f"Warning: Failed to handle container {container_name}: {e}")
        return False

def inspect_container(container_name):
    try:
        inspect_result = subprocess.run(['docker', 'inspect', container_name],
                                        capture_output=True,
                                        text=True,
                                        check=True)
        return json.loads(inspect_result.stdout)[0]
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError) as e:
        print(f"Warning: Failed to find information on container {container_name}: {e}")
        return False


def download_commit_script():
    commit_container_path = "/var/lib/vastai_kaalia/task_handlers/commit_container.py"
    if not os.path.exists(commit_container_path):
        print("Downloading commit_container script...")
        try:
            subprocess.run(['mkdir', '-p', '/var/lib/vastai_kaalia/task_handlers/'], check=True)
            # Download the file using wget
            subprocess.run(['wget', '-O', commit_container_path, "https://s3.amazonaws.com/public.vast.ai/commit_container.py"], check=True)
            subprocess.run(['chmod', '+x', commit_container_path], check=True)
            print("Succesfully downloaded commit_container script")            
        except Exception as e:
            print("Failed to download commit_container script")
            raise e

def get_gpus_used(inspect_cont):
    cont_uuids = []
    env = inspect_cont["Config"]["Env"]
    for env_var in env:
        entries = env_var.split('=')
        if len(entries) == 2 and entries[0].strip() == 'NVIDIA_VISIBLE_DEVICES':
            cont_uuids = entries[1].strip().split(',')
    return cont_uuids



if __name__ == "__main__":
    usage_str = "sudo python3 swap_gpu.py [OPTIONS]"
    help_str = "Swap a broken GPU with the given new GPU. If old GPU UUID is provided, " \
               "it will replace it, otherwise, it replaces the first missing GPU it finds"
    
    parser = ArgumentParser(usage=usage_str, description=help_str)
    parser.add_argument("-n", "--new_uuid", help="UUID of the new GPU to use as replacement. Required if containers are using old GPU uuid", type=str)
    parser.add_argument("-o", "--old_uuid", 
                        help="If supplied, tries to replace this GPU UUID with the new one", type=str)
    parser.add_argument("-s", "--skip_swap", help="If set, only calls webserver to reset count, without changing anything on the machine", action='store_true')
    args = parser.parse_args()
    # Get current GPUs
    current_uuids = get_current_gpus()
    if not args.skip_swap:
        try:
            vast_containers = get_vast_containers()
            if len(vast_containers) == 0:
                os.remove("/var/lib/vastai_kaalia/data/nvidia_smi.json")
            else:
                if not args.new_uuid:
                    print("Must include new gpu id")
                    exit(1)
                # Validate new GPU UUID
                if args.new_uuid not in current_uuids:
                    raise RuntimeError(f"New GPU UUID {args.new_uuid} not found in system")
                
                # Read the current configuration
                nvidia_smi_data = read_nvidia_smi_json()
                
                if args.old_uuid:
                    # Specific replacement mode
                    if args.old_uuid in current_uuids:
                        raise RuntimeError(f"Old GPU UUID {args.old_uuid} is still present in system")
                    
                    # Replace the specified UUID
                    nvidia_smi_data["uuid_idx_mapping"] = replace_gpu_uuid(nvidia_smi_data["uuid_idx_mapping"], args.old_uuid, args.new_uuid)
                else:
                    # Auto-replacement mode
                    # Get configured UUIDs from nvidia-smi.json
                    configured_uuids = set()
                    for uuid in nvidia_smi_data["uuid_idx_mapping"].keys():
                        configured_uuids.add(uuid)
                    
                    # Find missing GPUs
                    missing_uuids = configured_uuids - set(current_uuids)
                    if missing_uuids:
                        # Replace the first missing UUID
                        old_uuid = next(iter(missing_uuids))
                        nvidia_smi_data["uuid_idx_mapping"] = replace_gpu_uuid(nvidia_smi_data["uuid_idx_mapping"], old_uuid, args.new_uuid)
                        args.old_uuid = old_uuid  # Set for container handling
                
                # Write updated configuration
                write_nvidia_smi_json(nvidia_smi_data)
                print(f"Successfully replaced GPU UUID in configuration")

                # Handle containers
                if not args.old_uuid:
                    for container in vast_containers:
                        inspect_result = inspect_container(container)
                        if inspect_result:
                            # filter out old containers still using GPU index, they shouldn't care about the new gpu
                            cont_uuids = [gpu_id for gpu_id in get_gpus_used(inspect_result) if not gpu_id.isdigit()]
                            diff = set(cont_uuids) - set(current_uuids)
                            if len(diff) > 0:
                                args.old_uuid = diff.pop()
                                break
                
                if not args.old_uuid:
                    print("No containers stored using old uuid. Process complete.")
                    exit()
                
                download_commit_script()


                handled_containers = 0
                for container in vast_containers:
                    if handle_container(container, args.old_uuid, args.new_uuid):
                        handled_containers += 1
                
                print(f"Processed {handled_containers} containers using the old GPU")
                print("GPU swap completed successfully")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)
        
    print("Updating machine on webserver...")
    print(f"{server_url}/api/v0/machine/set_gpus")
    result = webserver_call(f"{server_url}/api/v0/machine/set_gpus/", {"gpu_ids" : current_uuids})
    print("Got Result: ")
    print(result.text)
