#!/bin/bash

DIR=/var/lib/vastai_kaalia

fetch_update () {
    wget https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/$1      -O $DIR/$1.tmp && chmod +x $DIR/$1.tmp && mv -f $DIR/$1.tmp $DIR/$1; 
}

#wget https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/update_scripts.sh      -O DIR/update_scripts.sh;     chmod +x DIR/update_scripts.sh;
fetch_update send_mach_info.py
fetch_update read_packs.py
fetch_update list_container_ips.sh
fetch_update test_nvml_error.sh
fetch_update enable_vms.py
fetch_update vast_fuse
fetch_update sync_libvirt.sh
fetch_update start_self_test.sh
fetch_update update_launcher.sh
fetch_update report_copy_success.py
fetch_update purge_stale_cdi.py

# update old installs to pull install_update.sh from the new S3
cat $DIR/update_launcher.sh | sed -e 's/\/vast\.ai\/static\$/\/public\.vast\.ai\/kaalia\/daemons\$/' > $DIR/update_launcher.sh.tmp && mv -f $DIR/update_launcher.sh.tmp $DIR/update_launcher.sh;

wget https://raw.githubusercontent.com/vast-ai/vast-cli/master/vast.py -O vast; chmod +x vast;
echo "updating crontab"

crontab -l > mycron23; 
sed -i '/update_scripts.sh/d' mycron23; 
sed -i '/send_mach_info.py/d' mycron23; 
sed -i '/read_packs.py/d' mycron23; 
sed -i '/enable_vms.py/d' mycron23;
sed -i '/manage_cert_pool.py/d' mycron23;
sed -i '/sync_libvirt.sh/d' mycron23;
sed -i '/purge_stale_cdi.py/d' mycron23;
sed -i '/enforce_size_restrictions.sh/d' mycron23;
echo "$(shuf -i 0-59 -n 1) * * * * /var/lib/vastai_kaalia/update_scripts.sh" >> mycron23; 
echo "$(shuf -i 0-59 -n 1) * * * * python3 /var/lib/vastai_kaalia/send_mach_info.py >> send_mach_info.log" >> mycron23; 
echo "$(shuf -i 0-59 -n 1) * * * * wget https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/update_scripts.sh -O /var/lib/vastai_kaalia/update_scripts.sh; chmod +x /var/lib/vastai_kaalia/update_scripts.sh;" >> mycron23;
echo "*/5 * * * * python3 /var/lib/vastai_kaalia/read_packs.py" >> mycron23;
echo "$(shuf -i 0-59 -n 1) * * * * sudo /var/lib/vastai_kaalia/enable_vms.py on" >> mycron23;
#echo "$(shuf -i 0-59 -n 12 | paste -sd ',' -) * * * * python3 /var/lib/vastai_kaalia/manage_cert_pool.py" >> mycron23;
echo "$(shuf -i 0-59 -n 1) * * * * /var/lib/vastai_kaalia/sync_libvirt.sh" >> mycron23;
echo "$(shuf -i 0-59 -n 1) * * * * sudo python3 /var/lib/vastai_kaalia/purge_stale_cdi.py >> /var/lib/vastai_kaalia/purge_stale_cdi.log 2>&1" >> mycron23

crontab mycron23; 
rm mycron23;

sudo DEBIAN_FRONTEND=noninteractive apt-get install -yq tshark;

sudo sysctl -w kernel.core_pattern=/var/lib/vastai_kaalia/data/core-%e.%p.%h.%t;
sudo sed -i '/vastai_kaalia - /d' /etc/security/limits.conf;
sudo sed -i '$a vastai_kaalia - core 2097152' /etc/security/limits.conf;
