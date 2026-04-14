#!/usr/bin/env python3
import os
import re
import argparse
import sys
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime

# Getting the current date and time
dt = datetime.now()
# getting the timestamp
ts = datetime.timestamp(dt)
pid = os.getpid()

parser = argparse.ArgumentParser(
    description='Called from Kaalia daemon binary to send pre-processed output to controller.')
parser.add_argument('-c', '--command', type=str, default="", help='Do not run standalone.')

_MiB = 2 ** 20

args = parser.parse_args()

# lockfile_path = "/var/lock/ktxt_tojson.lock"
# while os.path.exists(lockfile_path):
#     time.sleep(0.01)


def dispatch_ContainerList2(msg):
    jomsg = json.loads(msg)
    msglist = jomsg["msg"]

    a = "no_containers"
    if msglist is not None and len(msglist):
        a = (((msglist[0] or {}).get("GraphDriver") or {}).get("Data") or {}).get("UpperDir", "no_field")
    else:
        msglist = []

    if not a or not a.startswith("/var"):
        a = "no_containers"

    updates = {"msg": {"msglist": msglist, "a": a}, "type": "ContainerList2"}
    updates_str = json.dumps(updates)
    return updates_str


def dispatch_speedtest2(msg):
    jomsg = json.loads(msg)
    bwu_cur = jomsg["upload"] / _MiB
    bwd_cur = jomsg["download"] / _MiB
    return json.dumps({"bwu_cur": bwu_cur, "bwd_cur": bwd_cur})


def dispatch_meminfo2(msg):
    """The msg arg is a string made up of many lines that are the output of the meminfo command."""

    # jomsg = json.loads(msg)
    # msg = jomsg["msg"]
    # return json.dumps(msg)

    if not msg.strip():
        # log("Empty meminfo msg", level=L_WARNING, machine_id=self.machine_id)
        return json.dumps({"WARNING": "Empty meminfo2 msg"})
    # lines = msg.split("\n")

    # matches = re.findall("^([A-Za-z()_0-9]+): *([0-9]+)([^0-9\n].*)?$", msg, re.MULTILINE)
    matches = re.findall("^([A-Za-z()_0-9]+): *([0-9]+)([^0-9\n].*)?$", msg, re.MULTILINE)

        #re.findall(r'^(\w+): *(\d+) (.*)?$', msg, re.MULTILINE)

        #re.findall("([A-Za-z()_0-9]+):.*", msg, re.MULTILINE)
    if not all(kb in [" kB", ""] for key, value, kb in matches):
        raise Exception("Have some unknown integer types: {}".format(repr([x for x in matches if x[-1] != " kB"])))

    # updates = {"type": "meminfo2", "msg": matches}
    # updates_str = json.dumps(updates)
    # return updates_str

    # note: /proc/meminfo uses KiB, despite being labeled kB.
    # https://ubuntuforums.org/showthread.php?t=1165076

    kv = {key: int(value) for (key, value, kb) in matches if (kb == " kB")}
    # kv = {key: int(value) for (key, value, kb) in matches}
    extracted = kv
    fmt = extracted

        #json.dumps(extracted, indent=4, sort_keys=True)

    try:
        total_MiB = kv["MemTotal"] / 1024
    except:
        total_MiB = 0

    try:
        available_MiB = kv["MemAvailable"] / 1024
        # amount of ram that can be allocated by programs
    except:
        available_MiB = 0

    # also cached, buffers, etc - save to jsonb?

    # unused by *anything*
    try:
        free_MiB = kv["MemFree"] / 1024
    except:
        free_MiB = 0

    updates = {}
    updates["totalram"] = total_MiB
    updates["availram"] = available_MiB
    updates["freeram"] = free_MiB
    updates["fmt"] = fmt

    updates_str = json.dumps(updates)
    return updates_str


def convert_string_to_float(input_string):
    # Replace commas with dots
    input_string = input_string.replace(',', '.')
    # Convert to float
    output_float = float(input_string)
    return output_float


def dispatch_lscpu2(msg):
    lines = msg.split("\n")
    regex_matches = [re.match("^([A-Za-z()_0-9 -]+):[\t ]*([.,@a-zA-Z_0-9-][()@,.a-zA-Z_0-9+/ -]*)$", line) for line in
                     lines if line.strip()]
    groups = [match.groups() if match else (line, None) for line, match in zip(lines, regex_matches)]

    kv = {key: value for (key, value) in groups if value}
    fmt = json.dumps(kv, indent=4, sort_keys=True)
    product_name = kv.get("Model name")
    if (product_name is not None):
        product_name = product_name.replace("(TM)", "™")
        product_name = product_name.replace("(R)", "®")

    cpu_ghz = (convert_string_to_float(kv.get("CPU max MHz", "0")) / 1000.0) or None
    if (cpu_ghz is None) or (cpu_ghz < 0.001):
        cpu_ghz = (convert_string_to_float(kv.get("CPU MHz", "0")) / 1000.0) or None

    update = {
        "ghz": cpu_ghz,
        # "ncores": int(kv.get("Core(s) per socket", 0)) or None,
        "ncores": int(kv.get("CPU(s)", 0)) or None,
        "product_name": product_name,
        "threads_per_core": int(kv.get("Thread(s) per core", 0)) or None,
        "flags": kv.get("Flags"),
        "has_avx": 1 if ("avx" in kv.get("Flags", "").split()) else 0
    }
    return json.dumps(update)


def dispatch_uname2(msg):
    split_msg = msg.split(" ")
    hostname = None
    if len(split_msg) > 1:
        hostname = split_msg[1]
    # hostname = split_msg[1]
    update = {"hostname": hostname,
              "full_uname": msg}
    return json.dumps(update)


def dispatch_hdparm_timing2(msg):
    # FIXME: Seems to have no corresponding handle_request
    # in controller!

    r_D2H = re.search("seconds = *([0-9]+)", msg)

    if not r_D2H:
        r_D2H = None
        bw_dev_cpu = 0
    else:
        bw_dev_cpu = float(r_D2H.group(1))
    update = {"bw_dev_cpu": bw_dev_cpu}
    return json.dumps(update)


def dispatch_lshw_disk2(msg):
    r_product = re.search("product: ([A-Za-z0-9]+)", msg)
    r_vendor = re.search("vendor: ([A-Za-z0-9-]+)", msg)
    vendor = r_vendor.group(1) if r_vendor else ""
    product = r_product.group(1) if r_product else ""

    # r_product  = re.findall("product: ([A-Za-z0-9]+)", msg,  re.MULTILINE);
    # r_vendor   = re.findall("vendor: ([A-Za-z0-9-]+)", msg,  re.MULTILINE);

    if (vendor == '' and product == ''):
        if (msg.find('NVMe') > 0):
            product = 'nvme'
            vendor = ' '
        if (vendor == '' and product == ''):
            return json.dumps({"product_name": ""})

    # for (prod, vend) in zip(r_product, r_vendor):
    #    disk_product_name = vend + ' ' + prod;

    disk_product_name = (vendor + ' ' + product).strip()

    update = {"product_name": disk_product_name}
    return json.dumps(update)


def dispatch_dd_timing2(msg):
    r_time = re.search("copied, *([0-9.]+) s", msg)

    if not r_time:
        return

    bw_dev_cpu = 2.0 * 256.0 / float(r_time.group(1))
    update = {"bw_dev_cpu": bw_dev_cpu}
    return json.dumps(update)


def dispatch_dmidecode2(msg):
    r_product = re.search("Product Name: ([A-Za-z0-9 -]+)", msg)
    # if not r_product:
    #   return
    mobo_product_name = r_product.group(1)
    update = {"mobo_product_name": mobo_product_name}
    return json.dumps(update)


def dispatch_df2(msg):
    parts = msg.split()
    if len(msg) < 11:
        return

    disk_used_space  = int(parts[9])  / (1024*1024)
    disk_avail_space = int(parts[10]) / (1024*1024)
    disk_total_space = disk_used_space + disk_avail_space

    update = {"totalram": disk_total_space, "availram": disk_avail_space}
    return json.dumps(update)


def dispatch_bandwidthTest2(msg):

    gpu_idxs = re.search("Device ([0-9]+):", msg)
    r_H2D = re.search("bandwidthTest-H2D-Pinned, Bandwidth = ([0-9.]+) (MB/s|GB/s)", msg)
    r_D2H = re.search("bandwidthTest-D2H-Pinned, Bandwidth = ([0-9.]+) (MB/s|GB/s)", msg)
    r_D2D = re.search("bandwidthTest-D2D, Bandwidth = ([0-9.]+) (MB/s|GB/s)", msg)

    update = {}
    update["gpu_idx"] = 0

    if gpu_idxs:
        update["gpu_idx"] = int(gpu_idxs.group(1))

    if not r_H2D or not r_D2H or not r_D2D:
        update["ERROR_CONDITION"] = "not r_H2D or not r_D2H or not r_D2D"
        return json.dumps(update)

    def convert_bandwidth(value, unit):
        if unit == "MB/s":
            return float(value) / 1024.0
        else:
            return float(value)

    bw_cpu_dev = convert_bandwidth(*r_H2D.groups())
    bw_dev_cpu = convert_bandwidth(*r_D2H.groups())
    bw_dev_ram = convert_bandwidth(*r_D2D.groups())

    update["bw_cpu_dev"] = float(int(bw_cpu_dev * 10.0)) / 10.0
    update["bw_dev_cpu"] = float(int(bw_dev_cpu * 10.0)) / 10.0
    update["bw_dev_ram"] = float(int(bw_dev_ram * 10.0)) / 10.0

    update_str = json.dumps(update)
    return update_str


# from hsutils import get_cuda

def read_xml_text_part(node, keys, unit, defval):
    result = defval
    for k in keys:
        try:
            x, _, u = node.find(k).text.partition(" ")
            if u == unit:
                result = x
        except:
            pass
    return result


def dispatch_nvidia_smi2_(msg):
    updates = {}
    root = ET.fromstring(msg)
    # updates["root_str"] = msg
    # for idx,gpu in enumerate(parsed.xpath("/nvidia_smi_log/gpu")):
    # idx = 0;

    gpu_temp            = {}
    gpu_util            = {}
    vmem_usage          = {}
    uuid_idx_mapping    = {}
    pci_and_minor_no_info = []


    num_gpus = 0
    for gpu in root.iter('gpu'):
        num_gpus += 1
    inserts = []
    #inserts = [None] * num_gpus
    cidx = 0

    for gpu in root.iter('gpu'):
        prodname = gpu.find("product_name").text

        # dispname, corecount, compute_cap = match_gpu(prodname)

        display_active = gpu.find("display_active").text == "Enabled"
        idx = cidx # int(gpu.find("minor_number").text) # We never use or want minor number, having two separate idxs sometimes breaks nvidia_smi
        uuid = gpu.find("uuid").text
        uuid_idx_mapping[uuid] = cidx
        max_link_gen = current_link_gen = max_link_width = current_link_width = None

        try:
            max_link_gen       = gpu.find("pci").find("pci_gpu_link_info").find("pcie_gen").find("max_link_gen").text
            current_link_gen   = gpu.find("pci").find("pci_gpu_link_info").find("pcie_gen").find("current_link_gen").text
            max_link_width     = gpu.find("pci").find("pci_gpu_link_info").find("link_widths").find("max_link_width").text
            current_link_width = gpu.find("pci").find("pci_gpu_link_info").find("link_widths").find("current_link_width").text

            if current_link_width.endswith("x"):
                current_link_width = int(current_link_width[:-1])
            else:
                current_link_width = 0
        except:
            pass

        max_clock = gpu.find("max_clocks").find("sm_clock").text
        max_clock = re.match("^([0-9]+) MHz$", max_clock)
        if max_clock:
            max_clock = float(max_clock.group(1)) / 1000.0
        else:
            max_clock = 0
        cur_clock = gpu.find("clocks").find("sm_clock").text
        cur_clock = re.match("^([0-9]+) MHz$", cur_clock)
        if cur_clock:
            cur_clock = float(cur_clock.group(1)) / 1000.0
        else:
            cur_clock = 0

        # memclock           = gpu.xpath("//max_clocks/mem_clock/text()")[0]
        memclock = gpu.find("max_clocks").find("mem_clock").text
        memclock = re.match("^([0-9]+) MHz$", memclock)
        if memclock:
            memclock = int(memclock.group(1))
        else:
            memclock = 0

        pci_bus_id = gpu.find("pci").find("pci_bus_id").text
        minor_no = int(gpu.find("minor_number").text)
        pci_and_minor_no_info.append({"pci_bus_id": pci_bus_id, "minor_number": minor_no})

        total           = int(  read_xml_text_part(gpu, ["fb_memory_usage/total"], "MiB", 0))
        free            = int(  read_xml_text_part(gpu, ["fb_memory_usage/free"], "MiB", 0))
        cur_power       = float(read_xml_text_part(gpu, ["power_readings/power_draw",  "gpu_power_readings/power_draw"], "W", 0))
        max_power       = float(read_xml_text_part(gpu, ["power_readings/power_limit", "gpu_power_readings/current_power_limit"], "W", 0))
        cur_temp        = float(read_xml_text_part(gpu, ["temperature/gpu_temp"], "C", 0))
        gpu_temp[cidx]  = cur_temp
        max_temp        = float(read_xml_text_part(gpu, ["temperature/gpu_temp_max_threshold", "temperature/gpu_temp_tlimit"], "C", 80))
        gpu_util[cidx]  = float(read_xml_text_part(gpu, ["utilization/gpu_util"], "%", 0))


        vmem_usage[cidx] = (total-free) / 1024.0  # MB -> GB

        new_gpu = {
            "product_name": prodname,
            # "ncores": corecount,
            "totalram": total,
            "freeram": free,
            # "compute_cap": compute_cap,
            "display_active": display_active,
            "pci_gen": int(max_link_gen),
            "pci_width": current_link_width,
            "gpu_maxclock": max_clock,
            # "mem_maxclock": clock,
            "gpu_curclock": 0.8 * max_clock,
            "cur_power": cur_power,
            "max_power": max_power,
            "cur_temp": cur_temp,
            "max_temp": max_temp,
            # "tflops": (max_clock * (corecount or 0) * 2) / 1000.0,
            # "idx": int(gpu.xpath("//minor_number/text()")[0]),
            "idx": idx,
            # "machine_id": self.machine_id,
        }
        #inserts[idx] = new_gpu
        inserts.append(new_gpu)
        cidx += 1

    updates["uuid_idx_mapping"] = uuid_idx_mapping
    updates["inserts"]          = inserts
    updates["gpu_util"]         = gpu_util
    updates["vmem_usage"]       = vmem_usage
    updates["gpu_temp"]         = gpu_temp
    updates["pci_and_minor_no_info"]    = pci_and_minor_no_info

    try:
        driver_version = root.find("driver_version").text
        driver_version_float = float(".".join(driver_version.split(".")[:2]))
    except ValueError:
        updates["ERROR"] = "can't float() first section of driver version {driver_version}:"
    else:
        updates["driver_version"] = driver_version

    try:
        cuda_version = root.find("cuda_version").text
        cuda_version_float = float(".".join(cuda_version.split(".")[:2]))
    except:
        updates["ERROR"] = "can't float() first section of cuda version {cuda_version}:"
    else:
        updates["cuda_version"] = cuda_version

    json_str = json.dumps(updates)
    return json_str


def dispatch_nvidia_smi2(msg):
    try:
        return dispatch_nvidia_smi2_(msg)
    except:
        updates = {}
        updates['ERROR'] = msg[:256]
        json_str = json.dumps(updates)
        return json_str


def dict_to_file(d, fn):
    # print("dict_to_file() RUNNING")
    for item in d.items():
        k,v = item


def hrtxt_to_float(x):
    x = re.sub("0B", "0", x) if ("0B"  in x) else x
    x = re.sub("kiB", "", x) if ("kiB" in x) else x
    x = re.sub("kB", "", x)  if ("kB"  in x) else x
    x = re.sub("KiB", "", x) if ("KiB" in x) else x
    x = re.sub("KB", "", x)  if ("KB"  in x) else x
    x = re.sub("MiB", " * 2 ** 10", x) if ("MiB" in x) else x
    x = re.sub("MB",  " * 2 ** 10", x) if ("MB"  in x) else x
    x = re.sub("GiB", " * 2 ** 20", x) if ("GiB" in x) else x
    x = re.sub("GB",  " * 2 ** 20", x) if ("GB"  in x) else x
    x = re.sub("TiB", " * 2 ** 30", x) if ("TiB" in x) else x
    x = re.sub("TB",  " * 2 ** 30", x) if ("TB"  in x) else x
    x = re.sub("%", "", x) if ("%" in x) else x
    return x


def dispatch_ContainerStats2(msg):
    """FIXME: need to check contents of container_stats_fields."""
    rawstats = msg

    container_stats_lines = rawstats.split("\n")
    try:
        # Assumes that first line is the headers, 2nd is data.
        data_line = container_stats_lines[1]
        jomsg = {}
        data_line_single_spaced = re.sub(r"\s+", ' ', data_line)
        # In case they change the number of spaces on us
        container_stats_fields = data_line_single_spaced.split(" ")

        container_name = container_stats_fields[1]

        cont_pack_data = {}
        if os.path.exists('/var/lib/vastai_kaalia/cont_pack_data.json'):
            with open('/var/lib/vastai_kaalia/cont_pack_data.json') as json_file:
                cont_pack_data = json.load(json_file)

        odata = cont_pack_data.get(container_name, {})
        rbwd  = odata.get("rbwd", 1.0)
        rbwu  = odata.get("rbwu", 1.0)

        jomsg["name"]      = container_name
        jomsg["cpu_util"]  = eval( hrtxt_to_float(container_stats_fields[2]) )
        jomsg["mem_usage"] = eval( hrtxt_to_float(container_stats_fields[3]) ) / 1e6
        jomsg["mem_limit"] = eval( hrtxt_to_float(container_stats_fields[5]) ) / 1e6
        jomsg["eth0_bwd"]  = rbwd * eval( hrtxt_to_float(container_stats_fields[7]) )
        jomsg["eth0_bwu"]  = rbwu * eval( hrtxt_to_float(container_stats_fields[9]) )

    except Exception as ex:
        jomsg["ERROR"] = "ContainerStats2 parse exception"
        print(ex)
    # All of the above is to deal with the fact that the database wants
    # bandwidth in KiB/s with no units. There's a certain false precision
    # here in that the original figures seem to only have 4 sigfigs.
    #updates = {"msg": jomsg, "type": "ContainerStats2"}
    return json.dumps(jomsg)




def dispatch_docker_output2(msg):
    msg_parts = msg.split(" !$! ")

    msg = json.loads(msg)
    container_name = msg["container_name"]
    docker_msg = msg["docker_msg"]

    updates = {"container_name": container_name, "msg": docker_msg}

    updates_str = json.dumps(updates)
    return updates_str # updates_str


def float_version(version_str):
    parts = version_str.split('.')
    major = int(parts[0])
    minor = float('0.' + parts[1]) if len(parts) > 1 else 0.0
    
    # Start with major.minor as the base float version
    float_version = major + minor
    
    # Process any additional parts beyond the minor version
    if len(parts) > 2:
        additional_parts = parts[2:]
        m = 1.0
        for i, part in enumerate(additional_parts):
            m *= 0.01
            minor = float('0.' + part) if len(part) >= 1 else 0.0
            #print(f"{i} {part}  {m}*{minor}")
            #float_version += m*minor
    
    return float_version


def dispatch_ImgList2(msg):
    jomsg = json.loads(msg)

    #print(json.dumps(jomsg, indent=4))

    msg   = jomsg
    # msg = msg["msg"]
    for x in msg:
        cc = x.get('Config', None) or x.get('ContainerConfig', {}) or {}
        e = cc.get('Env', []) or []
        vs = {}
        rtags = x.get("RepoTags", [])
        #print(rtags)
        #print(e)
        for var in e:
            k, _, v = var.partition("=")
            vs[k] = v
        # x["Config"]=None
        # x["ContainerConfig"]=None
        #print(json.dumps(x, indent=2))

        # break
        rq = vs.get("NVIDIA_REQUIRE_CUDA", "")
        x["NVIDIA_REQUIRE_CUDA"] = rq

        if 'CUDA_VERSION' in vs:
            x['min_cuda_vers'] = float_version(vs['CUDA_VERSION'])

    handled = set()


    inserts = []
    updates = []
    update_list = []
    for idx, x in enumerate(msg):
        rtags = x.get("RepoTags", [])
        mincuda = x.get('min_cuda_vers', None)
        
        if mincuda is None:
            rq = x.get("NVIDIA_REQUIRE_CUDA") or ""
            stanzas = [x for x in rq.split(" ") if x]
            usable_stanzas = 0
            #print(rtags)
            for stanza in stanzas:
                stanza_usable = True
                for field in stanza.split(","):
                    m = re.match('^([a-zA-Z0-9_]+)([=><!]+)(.*)$', field)
                    if not m:
                        # WARN
                        #print(f"warn: re mismatch {field}, {rq}")
                        # log("warn: re mismatch", [field, rq], level=L_WARNING, machine_id=self.machine_id)
                        stanza_usable = False
                        continue
                    key, op, value = m.groups()
                    if key == "cuda":
                        if op != ">=":
                            # log("warn: op mismatch", [op, rq], level=L_WARNING, machine_id=self.machine_id)
                            stanza_usable = False
                            # WARN
                            continue
                        mincuda = float(value)
                    else:
                        stanza_usable = False
                if stanza_usable:
                    usable_stanzas += 1

            #print(f"stanzas: {stanzas} {usable_stanzas}")

            if usable_stanzas == 0 and len(stanzas):
                printf(f"unsuseable img: {rtags}")
                # level("warn: unuseable image!", rtags, rq, level=L_WARNING)
                pass

        for rtag in rtags:
            if rtag in handled:
                # log("warning: saw tag multiple times:", rtag, level=L_DEBUG, machine_id=self.machine_id)
                continue
            handled.add(rtag)
            #print(f" adding {rtag} {mincuda}")
            update_list.append({"rtag": rtag, "mincuda": mincuda})

            # global_image_tags[rtag] = AttrDict(global_image_tags.get(rtag, {}),
            #                                    min_cuda=mincuda,
            #                                    name=rtag,
            #                                    dirty=True
            #                                    )
    return json.dumps(update_list)



functions = dict()

functions["lscpu2"] = dispatch_lscpu2  # basic end-to-end testing passed
functions["lshw_disk2"] = dispatch_lshw_disk2  # basic end-to-end testing passed
functions["uname2"] = dispatch_uname2  # basic end-to-end testing passed
functions["hdparm_timing2"] = dispatch_hdparm_timing2  # basic end-to-end testing passed
functions["dd_timing2"] = dispatch_dd_timing2  # basic end-to-end testing passed
functions["dmidecode2"] = dispatch_dmidecode2  # basic end-to-end testing passed
functions["df2"] = dispatch_df2  # basic end-to-end testing passed
# functions["local_ips2"] = dispatch_local_ips2         # Does not require helper script.
functions["bandwidthTest2"] = dispatch_bandwidthTest2  # Tested with dummy data.
functions["nvidia_smi2"] = dispatch_nvidia_smi2
functions["docker_output2"] = dispatch_docker_output2
functions["ContainerStats2"] = dispatch_ContainerStats2
functions["meminfo2"] = dispatch_meminfo2
functions["speedtest2"] = dispatch_speedtest2
functions["ContainerList2"] = dispatch_ContainerList2
functions["ImgList2"] = dispatch_ImgList2


# take bash command input from stdin, print the output of the parser handler to stdout

input_str = str(sys.stdin.read())
output_str = functions[args.command](input_str)

if input_str is None or input_str == "": input_str = "NO INPUT!\n"
if output_str is None or output_str =="": output_str = "NO OUTPUT!\n"

print(output_str)


# async def handle_imglist_v2(self, db, msg):
# async def handle_ImgList2(self, db, msg):
# async def handle_ContainerList2(self, db, jomsg):
# async def handle_pspeedtest2(self, db, msg):
# async def handle_speedtest2(self, db, msg):
# async def handle_meminfo2(self, db, msg):   FIXME: not coming through after new lambdas
# async def handle_lshw_disk2(self, db, msg):
# async def handle_df2(self, db, msg):
# async def handle_bandwidthTest2(self, db, msg):
# async def handle_ContainerStats2(self, db, msg):
# async def handle_dd_timing2(self, db, msg):
# async def handle_dmidecode2(self, db, msg):
# async def handle_hdparm_timing2(self, db, msg):
# async def handle_lscpu2(self, db, msg):
# async def handle_uname2(self, db, msg):
# async def handle_nvidia_smi2(self, db, msg):
# async def handle_docker_output2(self, db, msg): FIXME: not called in Kaalia.cpp now???
