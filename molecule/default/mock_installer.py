#!/usr/bin/env python3
import os
from pathlib import Path

# Create expected artifacts for verify.yml
data_dir = Path("/var/lib/vastai_kaalia")
data_dir.mkdir(parents=True, exist_ok=True)

# Create completion marker
(data_dir / ".ansible_vastai_install_done").write_text("completed\n")

# Create latest dir
latest_dir = data_dir / "latest"
latest_dir.mkdir(parents=True, exist_ok=True)

# Touch expected files
(data_dir / "machine_id").touch()
(data_dir / "update_launcher.sh").touch()
(latest_dir / "launch_kaalia.sh").touch()
(latest_dir / "machine_metrics_pusher.py").touch()
launcher = latest_dir / "launch_metrics_pusher.sh"
launcher.touch()
launcher.chmod(0o755)

print("Mock installer completed successfully.")
