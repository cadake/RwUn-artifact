#!/usr/bin/env bash
set -euo pipefail

artifact_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
output_dir="${artifact_root}/dist"
archive="${output_dir}/rwun-artifact.tar.gz"

if [[ -n "${SOURCE_DATE_EPOCH:-}" ]]; then
    epoch="${SOURCE_DATE_EPOCH}"
elif git -C "${artifact_root}" rev-parse --git-dir >/dev/null 2>&1; then
    epoch=$(git -C "${artifact_root}" log -1 --format=%ct)
else
    epoch=$(date +%s)
fi

mkdir -p "${output_dir}"

tar \
    --directory="${artifact_root}" \
    --sort=name \
    --mtime="@${epoch}" \
    --owner=0 \
    --group=0 \
    --numeric-owner \
    --exclude=.git \
    --exclude=.github \
    --exclude=.idea \
    --exclude=.vscode \
    --exclude='*/__pycache__' \
    --exclude='*.py[cod]' \
    --exclude='*.egg-info' \
    --exclude=build \
    --exclude='*/build' \
    --exclude=dist \
    --exclude=evaluation \
    --exclude=evaluation-docker \
    --transform='s,^\./,rwun-artifact/,' \
    --create \
    --file=- \
    . | gzip --no-name > "${archive}"

(
    cd "${output_dir}"
    sha256sum "$(basename "${archive}")" > "$(basename "${archive}").sha256"
)

echo "created: ${archive}"
echo "created: ${archive}.sha256"
