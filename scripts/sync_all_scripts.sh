#!/usr/bin/env bash
# Re-download and replace all upstream Vast.ai script files in files/vast.ai/.

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${ROOT_DIR}/files/vast.ai"
TMP_DIR="$(mktemp -d)"
DRY_RUN=false

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "Target directory not found: ${TARGET_DIR}" >&2
  exit 1
fi

download() {
  local url="$1"
  local output_path="$2"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL --retry 3 --retry-delay 1 --connect-timeout 15 "${url}" -o "${output_path}"
    return
  fi

  if command -v wget >/dev/null 2>&1; then
    wget -qO "${output_path}" "${url}"
    return
  fi

  echo "Neither curl nor wget is available." >&2
  exit 1
}

declare -a FILE_MAP=(
  "install.py|https://s3.amazonaws.com/public.vast.ai/install"
  "update_scripts.sh|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/update_scripts.sh"
  "send_mach_info.py|https://s3.amazonaws.com/vast.ai/send_mach_info.py"
  "read_packs.py|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/read_packs.py"
  "report_copy_success.py|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/report_copy_success.py"
  "enable_vms.py|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/enable_vms.py"
  "sync_libvirt.sh|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/sync_libvirt.sh"
  "list_container_ips.sh|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/list_container_ips.sh"
  "purge_stale_cdi.py|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/purge_stale_cdi.py"
  "test_nvml_error.sh|https://s3.amazonaws.com/vast.ai/test_nvml_error.sh"
  "test_NCCL.py|https://s3.amazonaws.com/vast.ai/test_NCCL.py"
  "start_self_test.sh|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/start_self_test.sh"
  "vast.py|https://raw.githubusercontent.com/vast-ai/vast-cli/master/vast.py"
  "vast_fuse|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/vast_fuse"
  "update_launcher.sh|https://s3.amazonaws.com/public.vast.ai/kaalia/scripts/update_launcher.sh"
)

echo "Syncing ${#FILE_MAP[@]} files into ${TARGET_DIR}"

for entry in "${FILE_MAP[@]}"; do
  file_name="${entry%%|*}"
  source_url="${entry#*|}"

  destination_path="${TARGET_DIR}/${file_name}"
  temp_path="${TMP_DIR}/${file_name}"

  echo "- ${file_name}"
  echo "  source: ${source_url}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    continue
  fi

  download "${source_url}" "${temp_path}"

  if [[ -f "${destination_path}" ]]; then
    current_mode="$(stat -c '%a' "${destination_path}")"
  else
    current_mode="0644"
    if [[ "${file_name}" == *.sh || "${file_name}" == "vast_fuse" ]]; then
      current_mode="0755"
    fi
  fi

  install -m "${current_mode}" "${temp_path}" "${destination_path}"
done

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "Dry run complete. No files changed."
else
  echo "Sync complete."
fi
