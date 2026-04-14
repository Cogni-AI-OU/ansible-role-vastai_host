#!/bin/bash
cd "$HOME"
#sudo logrotate -s "$HOME"/logrotate.state logrotate.config || true

if test `find "$HOME/kaalia.log" -mmin +1`; then
    sudo systemctl stop vastai
    sleep 5
    sudo systemctl start vastai
fi
