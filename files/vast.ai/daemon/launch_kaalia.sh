#!/bin/bash
cd "$HOME/data"
auth="$(cat "$HOME/api_key")"
ipath="$(dirname "$0")"
"${ipath}/kaalia" backend=DKR installpath="${ipath}/" machineid_fn="$HOME/machine_id" fast_init=1 skip_bwtest=1 rlogfile="$HOME/kaalia.log" &>/dev/null
