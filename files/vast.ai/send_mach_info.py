#!/usr/bin/python3
import json
import subprocess
import requests
import random
import os
import subprocess
import platform
import time
from argparse import ArgumentParser

from datetime import datetime


from pathlib import Path
import re

def iommu_groups():
    return Path('/sys/kernel/iommu_groups').glob('*')
def iommu_groups_by_index():
    return ((int(path.name) , path) for path in iommu_groups())

class PCI:
    def __init__(self, id_string):
        parts: list[str] = re.split(r':|\.', id_string)
        if len(parts) == 4:
            PCI.domain = int(parts[0], 16)
            parts = parts[1:]
        else:
            PCI.domain = 0
        assert len(parts) == 3
        PCI.bus = int(parts[0], 16)
        PCI.device = int(parts[1], 16)
        PCI.fn = int(parts[2], 16)

# returns an iterator of devices, each of which contains the list of device functions.
def iommu_devices(iommu_path : Path):
    paths = (iommu_path / "devices").glob("*")
    devices= {}
    for path in paths:
        pci = PCI(path.name)
        device = (pci.domain, pci.bus,pci.device)
        if device in devices:
            devices[device].append((pci,path))
        else:
            devices[device] = [(pci,path)]
    return devices

# given a list of device function IDs belonging to a device and their paths,
# gets the render_node if it has one, using a list as an optional
def render_no_if_gpu(device_fns):
    for (_, path) in device_fns:
        if (path / 'drm').exists():
            return [r.name for r in (path/'drm').glob("render*")]
    return []

# returns a dict of bus:device -> (all pci ids, renderNode) for all gpus in an iommu group, by iommu group
def gpus_by_iommu_by_index():
    iommus = iommu_groups_by_index()
    for index,path in iommus:
        devices = iommu_devices(path)
        gpus= {}
        for d in devices:
            gpu_m = render_no_if_gpu(devices[d])
            if gpu_m:
                gpus[d] = (devices[d], gpu_m[0])
        if len(gpus) > 0:
            yield (index,gpus)

def devices_by_iommu_by_index():
    iommus = iommu_groups_by_index()
    devices = {}
    for index,path in iommus:
        devices[index] = iommu_devices(path)
    return devices

# check if each iommu group has only one gpu
def check_if_iommu_ok(iommu_gpus, iommu_devices):
    has_iommu_gpus = False
    for (index, gpus) in iommu_gpus:
        group_has_iommu_gpus = False
        has_iommu_gpus = True
        if len(iommu_devices[index]) > 1:
            for pci_address in iommu_devices[index]:
                # check if device is gpu itself
                if pci_address in gpus:
                    if group_has_iommu_gpus:
                        return False
                    group_has_iommu_gpus = True
                    continue
                # else, check if device is bridge
                for (pci_fn, path) in iommu_devices[index][pci_address]:
                    try:
                        pci_class = subprocess.run(
                            ['sudo', 'cat', path / 'class'],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        # bridges have class 06, class is stored in hex fmt, so 0x06XXXX should be fine to pass along w/ group
                        if pci_class.stdout[2:4] != '06':
                            return False
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        return False
    try:
        result = subprocess.run(
            ['sudo', 'cat', '/sys/module/nvidia_drm/parameters/modeset'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout[0] == 'N' and has_iommu_gpus
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def numeric_version(version_str):
    try:
        # Split the version string by the period
        try:
            major, minor, patch = version_str.split('.')
        except:
            major, minor = version_str.split('.')
            patch = ''

        # Pad each part with leading zeros to make it 3 digits
        major = major.zfill(3)
        minor = minor.zfill(3)
        patch = patch.zfill(3)

        # Concatenate the padded parts
        numeric_version_str = f"{major}{minor}{patch}"

        # Convert the concatenated string to an integer
        return int(numeric_version_str)

    except ValueError:
        print("Invalid version string format. Expected format: X.X.X")
        return None

def get_nvidia_driver_version():
    try:
        # Run the nvidia-smi command and capture its output
        output = subprocess.check_output(['nvidia-smi'], stderr=subprocess.STDOUT, text=True)

        # Split the output by lines
        lines = output.strip().split('\n')

        # Loop through each line and search for the driver version
        for line in lines:
            if "Driver Version" in line:
                # Extract driver version
                version_info = line.split(":")[1].strip()
                vers = version_info.split(" ")[0]
                return numeric_version(vers)

    except subprocess.CalledProcessError:
        print("Error: Failed to run nvidia-smi.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None


def cond_install(package, extra=None):
    result = False
    location = ""
    try:
        location = subprocess.check_output(f"which {package}", shell=True).decode('utf-8').strip()
        print(location)
    except:
        pass

    if (len(location) < 1):
        print(f"installing {package}")
        output = None
        try:
            if (extra is not None):
                output  = subprocess.check_output(extra, shell=True).decode('utf-8')
            output  = subprocess.check_output(f"sudo apt install -y {package}", shell=True).decode('utf-8')
            result = True
        except:
            print(output)
    else:
        result = True
    return result

def find_drive_of_mountpoint(target):
    output = subprocess.check_output("lsblk -sJap",  shell=True).decode('utf-8')
    jomsg = json.loads(output)
    blockdevs = jomsg.get("blockdevices", [])
    mountpoints = None
    devname = None
    for bdev in blockdevs:
        mountpoints = bdev.get("mountpoints", [])
        if (not mountpoints):
            # for ubuntu version < 22.04
            mountpoints = [bdev.get("mountpoint", None)]
        if (target in mountpoints):
            devname = bdev.get("name", None)
            nextn = bdev
            while nextn is not None:
                devname = nextn.get("name", None)
                try:
                    nextn = nextn.get("children",[None])[0]
                except:
                    nextn = None
    return devname

def epsilon_greedyish_speedtest():
    def epsilon(greedy):
        subprocess.run(["mkdir", "-p", "/var/lib/vastai_kaalia/.config"])
        output  = subprocess.check_output("docker run --rm -v /var/lib/vastai_kaalia/.config:/root/.config vastai/test:speedtest -L --accept-license --accept-gdpr --format=json", shell=True).decode('utf-8')
        mirrors = [server["id"] for server in json.loads(output)["servers"]]
        mirror = mirrors[random.randint(0,len(mirrors)-1)]
        print(f"running speedtest on random server id {mirror}")
        output = subprocess.check_output(f"docker run --rm -v /var/lib/vastai_kaalia/.config:/root/.config vastai/test:speedtest -s {mirror} --accept-license --accept-gdpr --format=json", shell=True).decode('utf-8')
        joutput = json.loads(output)
        score = joutput["download"]["bandwidth"] + joutput["upload"]["bandwidth"]
        if int(score) > int(greedy):
            with open("/var/lib/vastai_kaalia/data/speedtest_mirrors", "w") as f:
                f.write(f"{mirror},{score}")
        return output
    def greedy(id):
        print(f"running speedtest on known best server id {id}")
        output = subprocess.check_output(f"docker run --rm -v /var/lib/vastai_kaalia/.config:/root/.config vastai/test:speedtest -s {id} --accept-license --accept-gdpr --format=json", shell=True).decode('utf-8')
        joutput = json.loads(output)
        score = joutput["download"]["bandwidth"] + joutput["upload"]["bandwidth"]
        with open("/var/lib/vastai_kaalia/data/speedtest_mirrors", "w") as f: # we always want to update best in case it gets worse
            f.write(f"{id},{score}")
        return output
    try:
        with open("/var/lib/vastai_kaalia/data/speedtest_mirrors") as f:
            id, score = f.read().split(',')[0:2]
        if random.randint(0,2):
            return greedy(id)
        else:
            return epsilon(score)
    except:
        return epsilon(0)

def is_vms_enabled():
    try:
        with open('/var/lib/vastai_kaalia/kaalia.cfg') as conf:
            for field in conf.readlines():
                entries = field.split('=')
                if len(entries) == 2 and entries[0].strip() == 'gpu_type' and entries[1].strip() == 'nvidia_vm':
                    return True
    except:
        pass
    return False


def get_container_start_times():
    # Run `docker ps -q` to get all running container IDs
    result = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True)
    container_ids = result.stdout.splitlines()

    containerName_to_startTimes = {}
    for container_id in container_ids:
        # Run `docker inspect` for each container to get details
        inspect_result = subprocess.run(["docker", "inspect", container_id], capture_output=True, text=True)

        container_info = json.loads(inspect_result.stdout)

        container_name = container_info[0]["Name"].strip("/")
        start_time = container_info[0]["State"]["StartedAt"]

        # Convert date time to unix timestamp for easy storage and computation
        dt = datetime.strptime(start_time[:26], "%Y-%m-%dT%H:%M:%S.%f")
        containerName_to_startTimes[container_name] = dt.timestamp()

    return containerName_to_startTimes
def dict_to_fio_ini(job_dict):
    lines = []
    for section, options in job_dict.items():
        lines.append(f"[{section}]")
        for key, value in options.items():
            lines.append(f"{key}={value}")
        lines.append("")
    return "\n".join(lines)
def measure_read_bandwidth(disk_path, path, size_gb=1, block_size="4M"):
    try:
        with open(disk_path, "wb") as f:
            written = 0
            total_bytes = size_gb * 1024**3
            chunk_size = 1024**2
            while written < total_bytes:
                to_write = min(chunk_size, total_bytes - written)
                f.write(os.urandom(to_write))
                written += to_write
        job = {
            "global": {
                "ioengine": "libaio",
                "direct": 0,
                "bs": block_size,
                "size": f"{size_gb}G",
                "readwrite": "read",
                "directory": path,
                "filename" : "readtest",
                "numjobs": 1,
                "group_reporting": 1
            },
            "readtest": {
                "name": "readtest"
            }
        }
        job_file_content = dict_to_fio_ini(job)
        result = subprocess.run(
            ["sudo", "fio", "--output-format=json", "-"],
            input=job_file_content,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if result.returncode != 0:
            raise RuntimeError(f"fio failed: {result.stderr.strip()}")

        output = json.loads(result.stdout)
        bw_bytes = output["jobs"][0]["read"]["bw_bytes"]
        bw_mib = bw_bytes / (1024 * 1024)
        print(f"Read bandwidth: {bw_mib:.2f} MiB/sec")
        return bw_mib
    finally:
        os.remove(disk_path)

def mount_fuse(size, disk_mountpoint, fs_mountpoint, timeout=10):
    os.makedirs(disk_mountpoint, exist_ok=True)
    os.makedirs(fs_mountpoint, exist_ok=True)
    mounted = False
    if is_mounted(fs_mountpoint):
        mounted = True
        try:
            subprocess.run(["sudo", "fusermount", "-u", fs_mountpoint], check=True)
            print(f"Unmounted {fs_mountpoint}")
        except subprocess.CalledProcessError as e:
            print(f"{e}")
            print(f"Could not unmount mounted FS at {fs_mountpoint}! Not running bandwidth test")
            return
    if mounted:
        # Confirm unmount
        for _ in range(20):
            if not is_mounted(fs_mountpoint):
                mounted = False
                break
            time.sleep(0.1)
    if mounted:
        print(f"Could not unmount mounted FS at {fs_mountpoint}! Not running bandwidth test")
        return

    fuse_location = "/var/lib/vastai_kaalia/vast_fuse"
    cmd_args = [
        "sudo",
        fuse_location,
        "-m",
        disk_mountpoint,
        "-q",
        str(size),
        "--",
        "-o",
        "allow_other",
        fs_mountpoint
    ]
    proc = subprocess.Popen(
        cmd_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_mounted(fs_mountpoint):
            return proc
        time.sleep(0.2)
    print("Timeout reached waiting for fs to mount, killing FUSE process")
    # Timeout reached
    proc.terminate()

def is_mounted(path):
    """Check if path is a mount point."""
    try:
        subprocess.run(
            ["sudo", "mountpoint", "-q", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def get_channel():
    try:
        with open('/var/lib/vastai_kaalia/.channel') as f:
            channel = f.read()
            return channel
    except:
        pass
    return "" # default channel is just "" on purpose.

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--speedtest", action='store_true')
    parser.add_argument("--disk", action='store_true')
    parser.add_argument("--server", action='store', default="https://console.vast.ai")
    parser.add_argument("--nw-disk", action='store_true')
    args = parser.parse_args()
    output = None
    try:
        r = random.randint(0, 5)
        #print(r)
        if r == 3:
            print("apt update")
            output  = subprocess.check_output("sudo apt update", shell=True).decode('utf-8')
    except:
        print(output)


    # Command to get disk usage in GB
    print(datetime.now())

    print('os version')
    cmd = "lsb_release -a 2>&1 | grep 'Release:' | awk '{printf $2}'"
    os_version = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()

    print('running df')
    cmd_df = "df --output=avail -BG /var/lib/docker | tail -n1 | awk '{print $1}'"
    free_space = subprocess.check_output(cmd_df, shell=True).decode('utf-8').strip()[:-1]


    print("checking errors")
    cmd_df = "grep -e 'device error' -e 'nvml error' kaalia.log | tail -n 1"
    device_error = subprocess.check_output(cmd_df, shell=True).decode('utf-8')

    cmd_df = "sudo timeout --foreground 3s journalctl -o short-precise -r -k --since '24 hours ago' -g 'AER' -n 1"
    cmd_df = "sudo timeout --foreground 3s journalctl -o short-precise -r -k --since '24 hours ago' | grep 'AER' | tail -n 1"
    aer_error = subprocess.check_output(cmd_df, shell=True).decode('utf-8')
    if len(aer_error) < 4:
        aer_error = None

    cmd_df = "sudo timeout --foreground 3s journalctl -o short-precise -r -k --since '24 hours ago' -g 'Uncorrected' -n 1"
    cmd_df = "sudo timeout --foreground 3s journalctl -o short-precise -r -k --since '24 hours ago' | grep 'Uncorrected' | tail -n 1"
    uncorr_error = subprocess.check_output(cmd_df, shell=True).decode('utf-8')
    if len(uncorr_error) < 4:
        uncorr_error = None

    aer_error = uncorr_error or aer_error


    print("nvidia-smi")
    nv_driver_version = get_nvidia_driver_version()
    print(nv_driver_version)

    cond_install("fio")

    bwu_cur = bwd_cur = None
    speedtest_found = False

    print("checking speedtest")
    try:
        r = random.randint(0, 8)
        if r == 3 or args.speedtest:
            print("speedtest")
            try:
                output  = epsilon_greedyish_speedtest()
            except subprocess.CalledProcessError as e:
                output = e.output.decode('utf-8')
                print(output)
                output = None


            print(output)
            jomsg = json.loads(output)
            _MiB = 2 ** 20
            try:
                bwu_cur = 8*jomsg["upload"]["bandwidth"] / _MiB
                bwd_cur = 8*jomsg["download"]["bandwidth"] / _MiB
            except Exception as e:
                bwu_cur = 8*jomsg["upload"] / _MiB
                bwd_cur = 8*jomsg["download"] / _MiB

            #return json.dumps({"bwu_cur": bwu_cur, "bwd_cur": bwd_cur})

    except Exception as e:
        print("Exception:")
        print(e)
        print(output)

    disk_prodname = None

    try:
        docker_drive  = find_drive_of_mountpoint("/var/lib/docker")
        disk_prodname = subprocess.check_output(f"cat /sys/block/{docker_drive[5:]}/device/model",  shell=True).decode('utf-8')
        disk_prodname = disk_prodname.strip()
        print(f'found disk_name:{disk_prodname} from {docker_drive}')
    except:
        pass


    try:
        r = random.randint(0, 48)
        if r == 31:
            print('cleaning build cache')
            output  = subprocess.check_output("docker builder prune --force",  shell=True).decode('utf-8')
            print(output)
    except:
        pass


    fio_command_read  = "sudo fio --numjobs=16 --ioengine=libaio --direct=1 --verify=0 --name=read_test  --directory=/var/lib/docker --bs=32k --iodepth=64 --size=128MB --readwrite=randread  --time_based --runtime=1.0s --group_reporting=1 --iodepth_batch_submit=64 --iodepth_batch_complete_max=64"
    fio_command_write = "sudo fio --numjobs=16 --ioengine=libaio --direct=1 --verify=0 --name=write_test --directory=/var/lib/docker --bs=32k --iodepth=64 --size=128MB --readwrite=randwrite --time_based --runtime=0.5s --group_reporting=1 --iodepth_batch_submit=64 --iodepth_batch_complete_max=64"

    print('running fio')
    # Parse the output to get the bandwidth (in MB/s)
    disk_read_bw  = None
    disk_write_bw = None

    # Get the machine key
    mach_api_key = None
    try:
        with open('/var/lib/vastai_kaalia/machine_id', 'r') as f:
            mach_api_key = f.read()
    except Exception as e:
        print(str(e))

    # Prepare the data for the POST request
    data = { "mach_api_key": mach_api_key }

    r = random.randint(0, 3)
    if r == 3 or args.disk:
        data["availram"] = int(free_space)
        if disk_prodname:
            data["product_name"] = disk_prodname

        try:
            output_read   = subprocess.check_output(fio_command_read,  shell=True).decode('utf-8')
            disk_read_bw  = float(output_read.split('bw=')[1].split('MiB/s')[0].strip())
        except:
            pass

        try:
            disk_read_bw  = float(output_read.split('bw=')[1].split('GiB/s')[0].strip()) * 1024.0
        except:
            pass

        try:
            output_write  = subprocess.check_output(fio_command_write, shell=True).decode('utf-8')
            disk_write_bw = float(output_write.split('bw=')[1].split('MiB/s')[0].strip())
        except:
            pass

        try:
            disk_write_bw  = float(output_write.split('bw=')[1].split('GiB/s')[0].strip()) * 1024.0
        except:
            pass

        if disk_read_bw:
            data["bw_dev_cpu"] = disk_read_bw

        if disk_write_bw:
            data["bw_cpu_dev"] = disk_write_bw


    r = random.randint(0, 10)
    if mach_api_key and (r == 3 or args.nw_disk):
        print("nw_disk")
        headers = {"Authorization" : f"Bearer {mach_api_key}"}
        response = requests.get(args.server+'/api/v0/network_disks/', headers=headers)
        if response.status_code == 200:
            # for each disk, check if a certain amount is in use, if so, dont mount
            # otherwise mount half of remaining space and run speed test
            disk_speeds = []
            r_json = response.json()
            for mount in r_json["mounts"] :
                space_in_use = int(subprocess.check_output(['du','-s', mount.get("mount_point")]).split()[0].decode('utf-8'))
                total_space = mount.get("total_space") * 1024 * 1024 * 1024 # GB -> bytes
                print(f"total_space: {total_space}")
                print(f"in use: {space_in_use}")
                if space_in_use < total_space / 2:
                    space_to_test = int((total_space - space_in_use) / (2 * 1024 * 1024 * 1024))
                    if int(space_to_test) >= 2:
                        fs_mountpoint = f"/var/lib/vastai_kaalia/data/D_{mount.get('network_disk_id')}"
                        disk_mountpoint = mount.get("mount_point") + f"/D_{mount.get('network_disk_id')}"
                        proc = mount_fuse(space_to_test, disk_mountpoint, fs_mountpoint)
                        if proc:
                            readfile = disk_mountpoint + "/readtest"
                            bw = measure_read_bandwidth(readfile, fs_mountpoint, int(space_to_test / 2))
                            subprocess.run(["sudo", "fusermount", "-u", fs_mountpoint], check=True)
                            disk_speeds.append({"network_disk_id": mount.get("network_disk_id"), "bandwidth": int(bw)})
                            proc.terminate()

            if disk_speeds:
                response = requests.put(args.server+'/api/v0/network_disks/', headers=headers, json={"disk_speeds": disk_speeds})


    data['release_channel'] = get_channel()

    if os_version:
        data["ubuntu_version"] = os_version

    if bwu_cur and bwu_cur > 0:
        data["bwu_cur"] = bwu_cur

    if bwd_cur and bwd_cur > 0:
        data["bwd_cur"] = bwd_cur

    if nv_driver_version:
        data["driver_vers"] = nv_driver_version

    if device_error and len(device_error) > 8:
        data["error_msg"] = device_error

    if aer_error and len(aer_error) > 8:
        data["aer_error"] = aer_error

    architecture = platform.machine()
    if architecture in ["AMD64", "amd64", "x86_64", "x86-64", "x64"]:
        data["cpu_arch"] = "amd64"
    elif architecture in ["aarch64", "ARM64", "arm64"]:
        data["cpu_arch"] = "arm64"
    else:
        data["cpu_arch"] = "amd64"

    try:
        with open("/var/lib/vastai_kaalia/data/nvidia_smi.json", mode='r') as f:
            try:
                data["gpu_arch"] = json.loads(f.read())["gpu_arch"]
            except:
                data["gpu_arch"] = "nvidia"
            print(f"got gpu_arch: {data['gpu_arch']}")
    except:
        pass

    try:
        data["iommu_virtualizable"] = check_if_iommu_ok(gpus_by_iommu_by_index(), devices_by_iommu_by_index())
        print(f"got iommu virtualization capability: {data['iommu_virtualizable']}")
    except:
        pass
    try:
        vm_status = is_vms_enabled()
        data["vms_enabled"] = vm_status and data["iommu_virtualizable"]
        if vm_status:
            if not data["iommu_virtualizable"]:
                data["vm_error_msg"] = "IOMMU config or Nvidia DRM Modeset has changed to no longer support VMs"
            if not subprocess.run(
                    ["systemctl", "is-active", "gdm"],
                ).returncode:
                data["vm_error_msg"] = "GDM is on; VMs will no longer work."
        print(f"Got VM feature enablement status: {vm_status}")
    except:
        pass

    try:
        containerNames_to_startTimes = get_container_start_times()
        data["container_startTimes"] = containerNames_to_startTimes
        print(f"Got container start times: {containerNames_to_startTimes}")
    except Exception as e:
        print(f"Exception Occured: {e}")

    print(data)
    # Perform the POST request
    if mach_api_key:
        response = requests.put(args.server+'/api/v0/disks/update/', json=data)
        if response.status_code == 404 and mach_api_key.strip() != mach_api_key:
            print("Machine not found, retrying with stripped api key...")
            data["mach_api_key"] = mach_api_key.strip()
            print(data)
            response = requests.put(args.server+'/api/v0/disks/update/', json=data)
        # Check the response
        if response.status_code == 200:
            print("Data sent successfully.")
        else:
            print(response)
            print(f"Failed to send data, status code: {response.status_code}.")
    else:
        print('no machine key!')
