#!/usr/bin/env python3

import sys
import requests


def report_copy_success(container_name):
    with open("/var/lib/vastai_kaalia/machine_id", "r") as f:
        machine_api_key = f.read().strip()

    payload = {
        "task_id": container_name.replace("C.", ""),
        "task_name": "copy_direct",
        "op": "initiate_container_rsync",
        "status": "info",
        "info": "Done receiving copy",
        "machine_api_key": machine_api_key,
        "dst_container_id": container_name,
        "src_container_id": "local",
    }

    try:
        response = requests.put(
            "https://console.vast.ai/api/daemon/task/", json=payload, timeout=5
        )
        return response.status_code
    except Exception as e:
        with open(
            f"/var/lib/vastai_kaalia/data/instance_extra_logs/C.{container_name}", "a"
        ) as f:
            f.write(f"Failed to report copy success: {e}\n")
        return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <container_name>", file=sys.stderr)
        sys.exit(1)

    report_copy_success(sys.argv[1])
    sys.exit(0)
