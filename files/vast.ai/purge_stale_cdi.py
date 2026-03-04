#!/usr/bin/python3
"""
purge_stale_cdi.py

Remove stale Vast.ai CDI config files from /etc/cdi.

Vast's kaalia docker shim writes CDI configs named:
  D.<dockerContainerId>.yaml

If the referenced docker container no longer exists (running or stopped),
this script removes the stale CDI YAML.

Intended host install location:
  /var/lib/vastai_kaalia/purge_stale_cdi.py
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


FILENAME_RE = re.compile(r"^D\.([0-9a-fA-F]+)\.yaml$")


@dataclass
class Removal:
    path: Path
    container_id: str
    reason: str


def container_exists(container_id: str) -> bool:
    """
    True iff docker knows about this container id (running or stopped).
    """
    cmd = ["docker", "container", "inspect", container_id]
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return process.returncode == 0


def iter_matching_files(cdi_dir: Path) -> Iterable[Tuple[Path, str]]:
    try:
        for path in cdi_dir.iterdir():
            if path.is_file() and (m := FILENAME_RE.match(path.name)):
                yield path, m.group(1)
    except FileNotFoundError:
        return []
    except PermissionError as e:
        raise RuntimeError(f"permission denied reading {cdi_dir}: {e}") from e


def purge(cdi_dir: Path, dry_run: bool = False) -> List[Removal]:
    removed: List[Removal] = []

    for path, cid in iter_matching_files(cdi_dir):
        try:
            exists = container_exists(cid)
        except FileNotFoundError as e:
            raise RuntimeError("docker not found on PATH; cannot validate container IDs") from e

        if exists:
            continue

        if dry_run:
            removed.append(Removal(path=path, container_id=cid, reason="stale (dry-run)"))
            continue

        try:
            path.unlink()
            removed.append(Removal(path=path, container_id=cid, reason="stale"))
        except FileNotFoundError:
            removed.append(Removal(path=path, container_id=cid, reason="missing (already removed)"))
        except PermissionError as e:
            raise RuntimeError(f"permission denied removing {path}: {e}") from e

    return removed


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Remove stale Vast.ai CDI configs from /etc/cdi")
    ap.add_argument("--cdi-dir", default="/etc/cdi", help="CDI directory (default: /etc/cdi)")
    ap.add_argument("--dry-run", action="store_true", help="List what would be removed without deleting")
    args = ap.parse_args(argv)

    removed = purge(Path(args.cdi_dir), dry_run=args.dry_run)

    if not removed:
        print("No stale CDI configs found.")
        return 0

    verb = "Would remove" if args.dry_run else "Removed"
    print(f"Total to remove: {len(removed)}")
    for r in removed:
        print(f"{verb}: {r.path} (container_id={r.container_id}, reason={r.reason})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
