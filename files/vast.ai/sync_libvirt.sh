#!/bin/bash
f1=$(mktemp)
f2=$(mktemp)
sudo virsh list --name | sort > $f1
sudo docker ps --format "{{.Names}}" | sort > $f2
for GUEST in $(comm -23 "$f1" "$f2"); do
    if [[ "$GUEST" =~ ^C\.[0-9]+ ]]; then
        virsh destroy "$GUEST"
        virsh undefine "$GUEST" --nvram
    fi
done
rm "$f1" "$f2"
