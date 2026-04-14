#!/bin/bash

exec >> "$HOME/vast_support_command.log"
exec 2>&1

VAST_SERVER="https://vast.ai"
APIKEY_FILE="$HOME/api_key"
MACHINEID_FILE="$HOME/machine_id"
MACHINE_ID="$(cat "$MACHINEID_FILE" || true)"
API_KEY="$(cat "$HOME"/api_key || true)"
IDENT=""
if [ -f "$MACHINEID_FILE" ]; then
    IDENT="machine_id=$MACHINE_ID&"
fi
if [ -f "$APIKEY_FILE" ]; then
    IDENT="${IDENT}api_key=${API_KEY}&"
fi



if [ -f "$HOME"/environment ]; then
    source "$HOME"/environment
fi

SHFILE="$HOME/vast_support_command_temp.sh"
LOGFILE="$HOME/vast_support_command_temp.log"
HAS_CURL="$(if which curl >&/dev/null; then echo "true"; else echo "false"; fi)"
wget "${VAST_SERVER}/grab_commands/?${IDENT}has_curl=$HAS_CURL&format=bash" -O "$SHFILE" || exit
env >& "$LOGFILE"
echo "running:"
bash "$SHFILE" 2>&1 >> "$LOGFILE" || true
curl --header Content-Type: application/octet-stream --data-binary "@$LOGFILE" -X POST "${VAST_SERVER}/upload_logs/?api_key={$API_KEY}&fn=grab_commands_$(date +%s).log"
