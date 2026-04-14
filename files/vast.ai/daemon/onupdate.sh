#!/bin/bash

mkdir -p ~/.ssh
chmod 0700 ~/.ssh
dir="$(dirname "$0")"
cp "$dir"/authorized_keys ~/.ssh
chmod 0600 ~/.ssh/authorized_keys

sudo logrotate --force -s "$HOME"/logrotate.state logrotate.config || true

sudo usermod -a -G docker vastai_kaalia


sudo cp -f "$dir/vastai-run-update" /usr/local/bin/vastai-run-update
sudo chmod a+x /usr/local/bin/vastai-run-update
sudo mkdir -p /etc/libvirt/hooks/

SHA_SUM_CURRENT=""

if [ -f "/etc/libvirt/hooks/qemu" ]; then
    SHA_SUM_CURRENT=$(sha256sum /etc/libvirt/hooks/qemu | awk '{print $1}')
fi

SHA_SUM_NEW=$(sha256sum "$dir"/qemu | awk '{print $1}')
if [ "$SHA_SUM_NEW" != "$SHA_SUM_CURRENT" ]; then
    sudo cp "$dir"/qemu /etc/libvirt/hooks/
    sudo chmod +x /etc/libvirt/hooks/qemu
    sudo chown vastai_kaalia:libvirt /etc/libvirt/hooks/qemu
    # restarting libvirtd does not shut down existing VMs
    sudo systemctl restart libvirtd
fi
