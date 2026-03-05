#!/usr/bin/python3
import subprocess
import sys
import shutil 
import json
from base64 import b64decode
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import logging
import os
import time
import shutil
from datetime import datetime, timezone

VERSION=0

def get_directory_size(directory):
    result = subprocess.run(['sudo', 'du', '-sb', directory], stdout=subprocess.PIPE, text=True)
    size_in_bytes = int(result.stdout.split()[0])
    return size_in_bytes


def inspect_cont(cont_name):
    result = subprocess.run(
        ["docker", "container", "inspect", cont_name],
        check=True,
        capture_output=True,
        text=True
    )
    container_info = json.loads(result.stdout)
    
    if not container_info or not isinstance(container_info, list):
        raise RuntimeError(f"Invalid Container {cont_name}")
    return container_info[0]

def get_container_volumes(container_info):
    mounts = container_info.get("HostConfig", {}).get("Mounts", [])
    volume_configs = []
    
    for mount in mounts:
        if mount.get("Type") == "volume" and not mount.get("Name"):
            volume_configs.append(mount["Source"])
        elif mount.get("Type") == "volume" and mount.get("Name"):
            volume_configs.append(mount["Name"])
        elif mount.get("Type") == "bind":
            volume_configs.append(f"{mount['Source']}:{mount['Destination']}")
    return volume_configs

def get_storage_opts(container_info):
    storage_opts = []
    storage_opt = container_info.get("HostConfig", {}).get("StorageOpt", {})
    for key, value in storage_opt.items():
        storage_opts.append(f"{key}={value}")
        
    return storage_opts

def get_ports(container_info):
    formatted_ports = []
    ports = container_info.get("HostConfig", {}).get("PortBindings", {})
    for container_port, host_port_arr in ports.items():
        host_port = host_port_arr[0]["HostPort"]
        formatted_ports.append(f"{host_port}:{container_port}")
    return formatted_ports

def rollback(old_name, cur_name):
    print("exception creating container! rolling back old contianer...")
    try:
        res = subprocess.run([
                "docker",
                "rm",
                old_name
            ],
            capture_output=True,
            text = True)
        res = subprocess.run([
                "docker",
                "rename",
                cur_name,
                old_name
            ],
            check=True,
            capture_output=True,
            text = True)
    except Exception as e:
        print("unable to rollback to old container!")
        exit(1)



# rebuild a container by tarring its contents, instead of committing
# 
# 
# The difference is that committing creates a new read-only layer,
# which creates issues with storage tracking, as storage-opt only
# manages write layers. Tarring will maintain the same write layer,
# but the image will remain the same, so it's less useful for reusing
# changes made in the container.
# In general:
# committing will be useful for clients to reuse their container (once storage tracking is updated)
# rebuilding is useful for vast specific operations
def rebuild(task_context):
    cont_name = task_context.get("container_name", "")
    env_override = task_context.get("env_override", {})
    vast_name_pattern = r"C\.\d+"
    if not cont_name or not re.search(vast_name_pattern, cont_name):
        print(f"Invalid container - {cont_name}")
        exit(1)

    cont_data = inspect_cont(cont_name)
    
    write_dir = cont_data["GraphDriver"]["Data"]["UpperDir"]
    write_dir_size = get_directory_size(write_dir)
    docker_space = shutil.disk_usage("/var/lib/docker")

    if write_dir_size > (.9 * docker_space.free):
        raise RuntimeError("Not enough space left on device!")

    res = subprocess.run([
                "docker",
                "rename",
                cont_name,
                cont_name + "_old"
            ],
            check=True,
            capture_output=True,
            text = True)
    if res.returncode != 0:
        print(res.stderr)
        raise RuntimeError("exception renaming container!")

    try:


        base_dir = str(Path(write_dir).parent)
        res = subprocess.run([
            "sudo",
            "tar",
            f"--directory={base_dir}",
            "--exclude=diff/tmp/tmux-0/default",
            "-cf",
            f"{cont_name}.tar",
            "diff"
        ],
        capture_output=True,
        text = True)
        if res.returncode != 0:
            print(res.stderr)
            raise RuntimeError("exception generating container tarball!")
        # docker stores env as a list of strings
        old_env_arr = cont_data["Config"]["Env"]
        new_env = {}
        for env in old_env_arr:
            [env_key, env_val] = env.split("=", 1)
            new_env[env_key] = env_val
        for env_key, env_val in env_override.items():
            new_env[env_key] = str(env_val)
        volume_configs = get_container_volumes(cont_data)
        storage_opts = get_storage_opts(cont_data)
        ports = get_ports(cont_data)
        create_cmd = ["docker", "create", "--name", cont_name, "--runtime=nvidia"]
        for env_key, env_val in new_env.items():
            create_cmd.extend(["--env", f"{env_key}={env_val}"])
        for opt in storage_opts:
            create_cmd.extend(["--storage-opt", opt])
        for volume in volume_configs:
            create_cmd.extend(["-v", volume])
        for port in ports:
            create_cmd.extend(["-p", port])
        create_cmd.append(cont_data["Image"])
        res = subprocess.run(create_cmd, check=True, capture_output=True, text=True)
        new_cont_data = inspect_cont(cont_name)
        new_cont_write_dir = new_cont_data["GraphDriver"]["Data"]["UpperDir"]
        new_cont_base_dir = str(Path(new_cont_write_dir).parent)
        if new_cont_base_dir == base_dir:
            raise RuntimeError("Did not get new container after create!")
        res = subprocess.run([
            "sudo",
            "tar",
            f"--directory={new_cont_base_dir}",
            "-xf",
            f"{cont_name}.tar"
        ],
        check=True,
        capture_output=True,
        text = True)
    except Exception as e:
        print(str(e))
        rollback(cont_name, cont_name + "_old")

    res = subprocess.run([
            "sudo",
            "rm",
            f"{cont_name}.tar"
        ],
        capture_output=True,
        text = True)
    if res.stderr:
        print(res.stderr)
    res = subprocess.run([
                "docker",
                "rm",
                cont_name + "_old"
            ],
            capture_output=True,
            text = True)
    if res.stderr:
        print(res.stderr)
        print("exception removing old container!")
        exit(1)
    return "success"


#TODO: this is unused, test before using
def commit(task_context):
    cont_name = task_context.get("container_name", "")
    img_name = task_context.get("image_name", "") or cont_name.lower()
    preserve_old = task_context.get("preserve_old", False)
    create_new = task_context.get("create_new", False)
    env_override = task_context.get("env_override", {})
    size = task_context.get("size", False)
    vast_name_pattern = r"C\.\d+"
    if not cont_name or not re.search(vast_name_pattern, cont_name):
        print(f"Invalid container - {cont_name}")
        exit(1)

    cont_data = inspect_cont(cont_name)

    res = subprocess.run([
        "docker",
        "commit",
        cont_name,
        img_name
    ],
    check=True,
    capture_output=True,
    text = True)
    if res.stderr:
        print(res.stderr)
        raise RuntimeError("exception commiting container!")

    if create_new:                
        res = subprocess.run([
                "docker",
                "rename",
                cont_name,
                cont_name + "_old"
            ],
            check=True,
            capture_output=True,
            text = True)
        if res.stderr:
            print(res.stderr)
            raise RuntimeError("exception renaming container!")
        volume_configs = get_container_volumes(cont_data)
        storage_opts = []
        if size and isinstance(size, int):
            storage_opts.push(f"size={size}G")
        else:
            storage_opts = get_storage_opts(cont_data)
            # todo: amd?
        cmd = ["docker", "create", "--name", cont_name, "--runtime=nvidia"]    
        if env_override:
            if not isinstance(env_override, list):
                env_override = [env_override]
            for env in env_override:
                cmd.extend(["--env", env])
        for opt in storage_opts:
            cmd.extend(["--storage-opt", opt])
        for volume in volume_configs:
            cmd.extend(["-v", volume])
        cmd.append(img_name)
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stderr or res.returncode != 0:
            print(res.stderr)
            rollback(cont_name, cont_name + '_old')
            exit(1)
        if not preserve_old:
            res = subprocess.run([
                        "docker",
                        "rm",
                        cont_name + "_old"
                    ],
                    check=True,
                    capture_output=True,
                    text = True)
            if res.stderr:
                print(res.stderr)
                print("exception removing old container!")
    return "success"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# The secret tag that separates the password from the safe login info.
SAFE_TAG = "57622453103216354000313551466901646037476519937101486855362243730337611576411602"

def run_docker_command(cmd, desc, input_data=None):
    warning_text = "WARNING!"
    try:
        res = subprocess.run(cmd, shell=False, check=True,
                             capture_output=True, text=True, input=input_data)
        stderr = res.stderr.strip()
        if stderr and warning_text not in stderr:
            logging.error(f"{desc} error: {stderr}")
            exit(1)
        return res.stdout
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else ""
        if stderr and warning_text in stderr:
            return e.stdout
        else:
            logging.error(f"{desc} failed: {stderr}")
            exit(1)

def extract_credentials(safe_creds):
    parts = safe_creds.split(SAFE_TAG)
    if len(parts) != 2:
        return None, None, None
    password = parts[0]
    tokens = parts[1].strip().split()
    if len(tokens) < 3 or tokens[0] != "-u":
        return None, None, None
    user = tokens[1]
    container_registry = tokens[2]
    return user, password, container_registry

def get_timestamp():
    # Get current UTC time
    now = datetime.now(timezone.utc)
    # Determine the correct suffix for the day
    day = now.day
    if 4 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    # Create a formatted string like "April_17th_2025_at_01-42-30_PM_UTC"
    timestamp = now.strftime("%B") + f"_{day}{suffix}_" + now.strftime("%Y_at_%I-%M-%S_%p_UTC")
    return timestamp

def take_snapshot_and_push(task_context):
    safe_creds  = task_context["docker_login_creds"]
    snapshot_tag = task_context["snapshot_tag"] + "_at_" + get_timestamp()
    instance_id = task_context["instance_id"]
    container_name = f"C.{instance_id}"
    docker_config_file = f"/var/lib/vastai_kaalia/data/configs/{container_name}_snapshot/config.json"
    config_directory = os.path.dirname(docker_config_file)

    if not os.path.exists(config_directory):
        os.makedirs(config_directory)
        print(f"Created directory: {config_directory}")

    if not os.path.exists(docker_config_file):
        with open(docker_config_file, "w") as f:
            # Write a minimal config.json. Adjust content as needed.
            f.write('{ "auths": {} }')
        print(f"Created config file: {docker_config_file}")
    else:
        print(f"Config file already exists: {docker_config_file}")

    if not safe_creds:
        logging.error("%s: No docker login credentials provided. Exiting.", container_name)
        exit(1)

    pause_param = task_context.get("pause")
    if isinstance(pause_param, bool):
        pause_value = pause_param
    elif isinstance(pause_param, str) and pause_param.lower() in ["true", "false"]:
        pause_value = pause_param.lower() == "true"
    else:
        logging.error("Invalid pause value: %s", pause_param)
        exit(1)


    username, password, container_registry = extract_credentials(safe_creds)
    if not (username and password and container_registry):
        logging.error("%s: Invalid safe docker credentials format. Exiting.", container_name)
        exit(1)

    run_docker_command(["docker", f"--config={config_directory}", "logout"], f"{container_name} docker logout")
    run_docker_command(["docker", f"--config={config_directory}", "login", "-u", username, "--password-stdin", container_registry],
                       f"{container_name} docker login", input_data=password)

    commit_cmd = ["docker", "container", "commit", f"--pause={pause_value}", container_name, snapshot_tag]
    run_docker_command(commit_cmd, f"{container_name} docker commit")

    push_error = None
    try:
        run_docker_command(["docker", f"--config={config_directory}", "push", snapshot_tag], f"{container_name} docker push")
    except SystemExit as e:
        push_error = e
    finally:
        run_docker_command(["docker", "image", "rm", snapshot_tag], f"{container_name} docker image rm")
        if os.path.exists(config_directory):
            shutil.rmtree(config_directory)
            print(f"Removed config directory: {config_directory}")

    if push_error is not None:
        exit(1)
    
    return "success"

if __name__ == "__main__":
    task_info = json.loads(sys.argv[1])
    args = json.loads(sys.argv[2])
    op = task_info["op"]
    if op is not None:
        if op == "version":
            print(VERSION, end="")
        if op == "commit":
            print(commit(args), end="")
        if op == "rebuild":
            print(rebuild(args), end="")
        if op == "take_snapshot_and_push":
            print(take_snapshot_and_push(args), end="")
