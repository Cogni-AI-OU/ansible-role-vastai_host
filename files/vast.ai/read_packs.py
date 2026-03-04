import os
import subprocess
import json
import ipaddress

from collections import defaultdict

# Parameters
interface = 'docker0'
duration = 0.05  # duration in seconds
output_file = '/tmp/output.pcap'

# Run tshark
cmd = f'sudo tshark -p -i {interface} -c 4096 -a duration:{duration} -w {output_file}'
#cmd = f'tshark -a duration:{duration} -w {output_file}'
print(cmd)
os.system(cmd)

# container ips
cmd = ['/var/lib/vastai_kaalia/list_container_ips.sh']
print(cmd)
container_ips = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
#print(container_ips)
container_ip = json.loads(container_ips)
#print(container_ip)

container_ip2 = {}
for k,v in container_ip.items():
    container_ip2[v] = k[1:]
print(container_ip2)


# Analyze the output
#cmd = ['tshark', '-r', output_file, '-T', 'fields', '-e', 'ip.src', '-e', 'ip.dst', '-e', 'frame.len']
cmd = f'sudo tshark -r {output_file} -T fields -e ip.src -e ip.dst -e frame.len'
result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')



# Define private IP address spaces
private_networks = [ipaddress.ip_network('10.0.0.0/8'),
                    ipaddress.ip_network('172.16.0.0/12'),
                    ipaddress.ip_network('192.168.0.0/16')]

def is_intranet(ip):
    ip = ipaddress.ip_address(ip)
    for network in private_networks:
        if ip in network:
            return True
    return False

# Parse the result and accumulate packet sizes
packet_sizes = defaultdict(int)

gbwu = defaultdict(int)
gbwd = defaultdict(int)
lbwu = defaultdict(int)
lbwd = defaultdict(int)

linelist = result.splitlines()
print(f'captured {len(linelist)} lines')
for line in linelist:
    src, dst, size = line.split('\t')
    
    srcn = container_ip2.get(src, None)
    dstn = container_ip2.get(dst, None)

    if (srcn != None):
        if (is_intranet(dst)):
            lbwu[srcn] += int(size)
        else:
            gbwu[srcn] += int(size)

    if (dstn != None):
        if (is_intranet(src)):
            lbwd[dstn] += int(size)
        else:
            gbwd[dstn] += int(size)

    packet_sizes[(src, dst)] += int(size)

print(dict(gbwu))
print(dict(gbwd))
print(dict(lbwu))
print(dict(lbwd))

cont_pack_data = defaultdict(int)
cont_pack_data_old = {}

try:
    if os.path.exists('cont_pack_data.json'):
        with open('cont_pack_data.json') as json_file:
            cont_pack_data_old = json.load(json_file)
except Exception as ex:
    print(ex)


print("previous:")
print(dict(cont_pack_data_old))

for k,v in container_ip.items():
    cname = k[1:]
    ndata = {"gbwu": gbwu[cname], "gbwd": gbwd[cname], "lbwu": lbwu[cname], "lbwd": lbwd[cname]}
    odata = cont_pack_data_old.get(cname, {})

    totals = ndata
    totals["gbwu"] += odata.get("gbwu",0)
    totals["gbwd"] += odata.get("gbwd",0)
    totals["lbwu"] += odata.get("lbwu",0)
    totals["lbwd"] += odata.get("lbwd",0)

    totals["rbwu"] = (totals["gbwu"] + 1) / (totals["gbwu"] + totals["lbwu"] + 1)
    totals["rbwd"] = (totals["gbwd"] + 1) / (totals["gbwd"] + totals["lbwd"] + 1)

    cont_pack_data[cname] = totals

print("new:")
print(dict(cont_pack_data))

with open('cont_pack_data.json', 'w') as fp:
    json.dump(dict(cont_pack_data), fp)


# Print the results
for (src, dst), size in packet_sizes.items():
    print(f'Source: {src}, Destination: {dst}, Total size: {size} bytes')
