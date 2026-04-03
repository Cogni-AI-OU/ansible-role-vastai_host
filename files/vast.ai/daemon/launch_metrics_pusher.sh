#!/bin/bash
cd "$(dirname "$0")"
exec python3 machine_metrics_pusher.py
