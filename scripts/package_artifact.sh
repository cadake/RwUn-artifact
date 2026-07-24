#!/usr/bin/env bash
set -euo pipefail

artifact_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
output_dir="${artifact_root}/dist"
archive_name="rwun-artifact.tar.gz"
archive="${output_dir}/${archive_name}"
image_tag="rwun-artifact:2026"
image_platform="linux/amd64"
image_archive_name="rwun-artifact-image-linux-amd64.tar.gz"
image_archive="${output_dir}/${image_archive_name}"

for command in docker tar gzip sha256sum; do
    if ! command -v "${command}" >/dev/null 2>&1; then
        echo "error: required command not found: ${command}" >&2
        exit 1
    fi
done

if [[ -n "${SOURCE_DATE_EPOCH:-}" ]]; then
    epoch="${SOURCE_DATE_EPOCH}"
elif git -C "${artifact_root}" rev-parse --git-dir >/dev/null 2>&1; then
    epoch=$(git -C "${artifact_root}" log -1 --format=%ct)
else
    epoch=$(date +%s)
fi

if [[ ! "${epoch}" =~ ^[0-9]+$ ]]; then
    echo "error: SOURCE_DATE_EPOCH must be a non-negative integer" >&2
    exit 1
fi

mkdir -p "${output_dir}"

staging_dir=$(mktemp -d)
staged_artifact="${staging_dir}/rwun-artifact"
image_archive_tmp="${image_archive}.tmp"
image_checksum_tmp="${image_archive}.sha256.tmp"
archive_tmp="${archive}.tmp"
archive_checksum_tmp="${archive}.sha256.tmp"

cleanup() {
    rm -rf "${staging_dir}"
    rm -f \
        "${image_archive_tmp}" \
        "${image_checksum_tmp}" \
        "${archive_tmp}" \
        "${archive_checksum_tmp}"
}
trap cleanup EXIT

mkdir -p "${staged_artifact}"

# Stage only reviewer-facing source files so the Docker image and archive are
# built from the same clean tree.
tar \
    --directory="${artifact_root}" \
    --exclude=.git \
    --exclude=.github \
    --exclude=.agents \
    --exclude=.codex \
    --exclude=.idea \
    --exclude=.vscode \
    --exclude='*/.git-backup' \
    --exclude='*/__pycache__' \
    --exclude='*.py[cod]' \
    --exclude='*.egg-info' \
    --exclude=build \
    --exclude='*/build' \
    --exclude=dist \
    --exclude=evaluation \
    --exclude=evaluation-docker \
    --exclude=evaluation_results \
    --create \
    --file=- \
    . | tar --directory="${staged_artifact}" --extract --file=-

echo "building: ${image_tag} (${image_platform})"
docker build \
    --platform "${image_platform}" \
    --tag "${image_tag}" \
    "${staged_artifact}"

echo "validating: ${image_tag}"
docker run --rm --network none \
    "${image_tag}" \
    python run_evaluation.py 0

echo "exporting: ${image_archive}"
docker save "${image_tag}" | gzip --no-name --stdout > "${image_archive_tmp}"
gzip --test "${image_archive_tmp}"
mv "${image_archive_tmp}" "${image_archive}"

(
    cd "${output_dir}"
    sha256sum "${image_archive_name}" > "${image_checksum_tmp}"
)
mv "${image_checksum_tmp}" "${image_archive}.sha256"

mkdir -p "${staged_artifact}/dist"
cp "${image_archive}" "${image_archive}.sha256" "${staged_artifact}/dist/"

echo "packaging: ${archive}"
tar \
    --directory="${staging_dir}" \
    --sort=name \
    --mtime="@${epoch}" \
    --owner=0 \
    --group=0 \
    --numeric-owner \
    --create \
    --file=- \
    rwun-artifact | gzip --no-name --stdout > "${archive_tmp}"
gzip --test "${archive_tmp}"
tar --list --gzip --file="${archive_tmp}" \
    "rwun-artifact/dist/${image_archive_name}" >/dev/null
mv "${archive_tmp}" "${archive}"

(
    cd "${output_dir}"
    sha256sum "${archive_name}" > "${archive_checksum_tmp}"
)
mv "${archive_checksum_tmp}" "${archive}.sha256"

echo "created: ${image_archive}"
echo "created: ${image_archive}.sha256"
echo "created: ${archive}"
echo "created: ${archive}.sha256"
