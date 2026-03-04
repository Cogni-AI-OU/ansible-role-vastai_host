# Known Issues

This document describes known issues and their workarounds.

## NixOS Docker Containers with containerd 2.2.0+ and Go 1.24

### Problem

NixOS Docker containers fail to start with containerd 2.2.0+ (built with Go 1.24) due to
stricter path validation in Go's `os.DirFS`. The error manifests as:

```text
openat etc/group: path escapes from parent
```

or

```text
openat etc/passwd: path escapes from parent
```

### Root Cause

NixOS images use absolute symlinks for `/etc/passwd` and `/etc/group` that point to the Nix store:

```text
/etc/passwd -> /nix/store/<hash>-etc-passwd
/etc/group  -> /nix/store/<hash>-etc-group
```

Go 1.24 introduced stricter path validation in `os.DirFS` that rejects paths escaping the root
directory. When containerd tries to read these symlinks relative to the container's root
filesystem, the absolute symlink targets are interpreted as escaping the parent directory.

### Workaround

Convert the absolute symlinks to relative symlinks in the Dockerfile before running any
commands that require user/group resolution:

```dockerfile
FROM nixos/nix:latest

# Workaround for containerd 2.2.0+ / Go 1.24 "path escapes from parent" error.
# Convert absolute symlinks (/nix/store/...) to relative ones.
# See: https://github.com/containerd/containerd/issues/12683
RUN ln --symbolic --force \
      "$(realpath --relative-to=/etc /etc/passwd)" /etc/passwd && \
    ln --symbolic --force \
      "$(realpath --relative-to=/etc /etc/group)" /etc/group

# Continue with other commands...
RUN nix-channel --update && \
    nix-env -iA nixpkgs.python3
```

This converts the symlinks from absolute to relative paths:

- Before: `/etc/passwd` -> `/nix/store/<hash>-etc-passwd` (absolute)
- After: `/etc/passwd` -> `../nix/store/<hash>-etc-passwd` (relative)

### Affected Components

- [molecule/resources/playbooks/Dockerfile.j2](molecule/resources/playbooks/Dockerfile.j2) -
  Molecule NixOS image template
- [tests/playbooks/docker-containers.yml](tests/playbooks/docker-containers.yml) -
  Docker test playbook (uses pre-built image)

### References

- [containerd/containerd#12683](https://github.com/containerd/containerd/issues/12683) -
  Original issue report
- [Go 1.24 Release Notes](https://go.dev/doc/go1.24) - os.DirFS path validation changes

### Status

**Workaround implemented** - The Dockerfile template includes the symlink conversion fix.

This issue affects any environment running:

- containerd >= 2.2.0 built with Go >= 1.24
- Docker Desktop with updated containerd
- Kubernetes clusters with updated containerd
