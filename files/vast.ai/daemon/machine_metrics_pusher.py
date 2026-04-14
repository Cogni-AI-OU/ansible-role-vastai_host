#!/usr/bin/env python3
from abc import ABC, abstractmethod
import time
import os
import re
import shutil
import requests

main_loop_polling_timer = 30

class BaseMetric(ABC):
    def __init__(self, metric_name: str):
        self.metric_name = metric_name
    @abstractmethod
    def get_docker_metric(self) -> float:
        pass
    @abstractmethod
    def get_host_metric(self) -> float:
        pass

    def get_metrics(self) -> tuple[float, float]:
        return self.get_docker_metric(), self.get_host_metric()

    def __str__(self):
        return f"{self.metric_name} - \nDocker usage: {self.get_docker_metric()} Host usage: {self.get_host_metric()}"

class DiskUsage(BaseMetric):
    def __init__(self):
        super().__init__(__class__.__name__)

    def get_docker_metric(self):
        return shutil.disk_usage("/var/lib/docker/").used // 1000**3

    def get_host_metric(self):
        return shutil.disk_usage("/").used // 1000**3

class CPUUsage(BaseMetric):
    def __init__(self):
        super().__init__(__class__.__name__)
        self.docker_pct, self.host_pct = parse_cpu_stats()

    def get_docker_metric(self):
        return self.docker_pct

    def get_host_metric(self):
        return self.host_pct

CLK_TCK = os.sysconf(os.sysconf_names.get("SC_CLK_TCK", "SC_CLK_TCK"))
NCPU = os.cpu_count() or 1

# Patterns that indicate the process is in a containerized cgroup (Docker/containerd/K8s/Podman)
CGROUP_CONTAINER_PAT = re.compile(r"(docker|containerd|kubepods|libpod)", re.IGNORECASE)


def read_proc_stat_cpu():
    """
    Read the aggregated CPU times from /proc/stat.
    Returns (total_jiffies, idle_jiffies).
    """
    with open("/proc/stat", "r") as f:
        for line in f:
            if line.startswith("cpu "):
                parts = line.split()
                # cpu user nice system idle iowait irq softirq steal guest guest_nice
                # Use standard kernel accounting: total is sum of first 8 fields (user..steal)
                # idle time is idle + iowait
                # Some kernels have fewer/more fields; guard accordingly.
                values = [int(x) for x in parts[1:]]
                # Ensure length >= 8
                while len(values) < 8:
                    values.append(0)
                user, nice, system, idle, iowait, irq, softirq, steal = values[:8]
                idle_all = idle + iowait
                total = user + nice + system + idle + iowait + irq + softirq + steal
                return total, idle_all
    # Fallback if cpu line missing (shouldn't happen on Linux)
    return 0, 0


def list_pids():
    for name in os.listdir("/proc"):
        if name.isdigit():
            yield name


def pid_in_container(pid):
    """
    Heuristic: check /proc/<pid>/cgroup entries for container-runtime markers.
    """
    try:
        with open(f"/proc/{pid}/cgroup", "r") as f:
            data = f.read()
        return bool(CGROUP_CONTAINER_PAT.search(data))
    except Exception:
        return False


def pid_utime_stime_jiffies(pid):
    """
    Return utime + stime for a process, in jiffies.
    We do not add children's times to avoid double counting when summing across PIDs.
    """
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            stat = f.read().split()
        # utime is field 14, stime is field 15 (1-indexed in manpage; 0-indexed here -> 13,14)
        utime = int(stat[13])
        stime = int(stat[14])
        return utime + stime
    except Exception:
        return 0


def sample_process_cpu_split():
    """
    Sum utime+stime across all PIDs, split by (inside_container vs outside).
    Returns tuple (sum_in_docker_jiffies, sum_outside_jiffies).
    """
    in_docker = 0
    outside = 0
    for pid in list_pids():
        j = pid_utime_stime_jiffies(pid)
        if j == 0:
            # could be kernel thread or permission error; skip quietly
            continue
        if pid_in_container(pid):
            in_docker += j
        else:
            outside += j
    return in_docker, outside


def compute_total_busy_pct(t0_total, t0_idle, t1_total, t1_idle):
    total_delta = max(1, t1_total - t0_total)
    idle_delta = max(0, t1_idle - t0_idle)
    busy_delta = max(0, total_delta - idle_delta)
    # busy fraction across all cores; normalized to 0..100
    return (busy_delta / total_delta) * 100.0

def parse_cpu_stats():
    # First snapshot
    t0_total, t0_idle = read_proc_stat_cpu()
    d0_in, _ = sample_process_cpu_split()
    wall0 = time.time()

    # Sleep ~interval
    time.sleep(0.1)

    # Second snapshot
    t1_total, t1_idle = read_proc_stat_cpu()
    d1_in, _ = sample_process_cpu_split()
    wall1 = time.time()

    elapsed = max(1e-6, wall1 - wall0)

    total_pct = compute_total_busy_pct(t0_total, t0_idle, t1_total, t1_idle)

    # Convert jiffies deltas to "CPU capacity" consumed, normalize to percent
    delta_in_j = max(0, d1_in - d0_in)

    # outside processes' direct measurement (optional; we prefer computing outside as total - docker to avoid drift)
    docker_pct = (delta_in_j / (CLK_TCK * elapsed * NCPU)) * 100.0

    # outside as residual; clamp to [0, 100]
    outside_pct = max(0.0, min(100.0, total_pct - docker_pct))

    # Also clamp docker and total into [0,100] to be safe on jittery machines
    docker_pct = max(0.0, min(100.0, docker_pct))

    return docker_pct, outside_pct

def main():
    while True:
        try:
            docker_cpu_usage, host_cpu_usage = CPUUsage().get_metrics()
            docker_disk_usage, host_disk_usage = DiskUsage().get_metrics()


            data = {
                "machine_api_key": open("machine_id").read(),
                "metrics": {
                    "cpu_usage": [docker_cpu_usage, host_cpu_usage],
                    "disk_usage": [docker_disk_usage, host_disk_usage]
                },
                "timestamp": int(time.time())
            }

            server_url = os.environ.get("VAST_SERVER", "https://console.vast.ai")
            response = requests.post(f"{server_url}/api/v0/machine/metrics/", json=data)
            response.raise_for_status()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            time.sleep(main_loop_polling_timer)

#INFO: Ensures that the main loop will only run when executing this file directly
if __name__ == "__main__":
    main()
