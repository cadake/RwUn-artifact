#!/usr/bin/env bash
set -euo pipefail

artifact_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
output_dir="${artifact_root}/dist"
archive_name="rwun-artifact.tar.gz"
archive="${output_dir}/${archive_name}"
image_tag="rwun-artifact:2026"
image_platforms=("linux/amd64" "linux/arm64")
image_archive_names=(
    "rwun-artifact-image-linux-amd64.tar.gz"
    "rwun-artifact-image-linux-arm64.tar.gz"
)
build_args=()

if [[ -n "${PYTHON_IMAGE:-}" ]]; then
    build_args+=(--build-arg "PYTHON_IMAGE=${PYTHON_IMAGE}")
fi

for command in docker tar gzip sha256sum; do
    if ! command -v "${command}" >/dev/null 2>&1; then
        echo "error: required command not found: ${command}" >&2
        exit 1
    fi
done

if ! docker buildx version >/dev/null 2>&1; then
    echo "error: Docker Buildx is required for multi-platform builds" >&2
    exit 1
fi

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
archive_tmp="${archive}.tmp"
archive_checksum_tmp="${archive}.sha256.tmp"
temporary_files=("${archive_tmp}" "${archive_checksum_tmp}")

for image_archive_name in "${image_archive_names[@]}"; do
    image_archive="${output_dir}/${image_archive_name}"
    temporary_files+=("${image_archive}.tmp" "${image_archive}.sha256.tmp")
done

cleanup() {
    rm -rf "${staging_dir}"
    rm -f "${temporary_files[@]}"
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

mkdir -p "${staged_artifact}/dist"

for index in "${!image_platforms[@]}"; do
    image_platform="${image_platforms[index]}"
    image_archive_name="${image_archive_names[index]}"
    image_archive="${output_dir}/${image_archive_name}"
    image_archive_tmp="${image_archive}.tmp"
    image_checksum_tmp="${image_archive}.sha256.tmp"

    echo "building: ${image_tag} (${image_platform})"
    docker buildx build \
        "${build_args[@]}" \
        --platform "${image_platform}" \
        --provenance=false \
        --tag "${image_tag}" \
        --load \
        "${staged_artifact}"

    echo "validating: ${image_tag} (${image_platform})"
    docker run --rm --network none \
        --platform "${image_platform}" \
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

    cp "${image_archive}" "${image_archive}.sha256" "${staged_artifact}/dist/"
done

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
for image_archive_name in "${image_archive_names[@]}"; do
    tar --list --gzip --file="${archive_tmp}" \
        "rwun-artifact/dist/${image_archive_name}" >/dev/null
done
mv "${archive_tmp}" "${archive}"

(
    cd "${output_dir}"
    sha256sum "${archive_name}" > "${archive_checksum_tmp}"
)
mv "${archive_checksum_tmp}" "${archive}.sha256"

for image_archive_name in "${image_archive_names[@]}"; do
    echo "created: ${output_dir}/${image_archive_name}"
    echo "created: ${output_dir}/${image_archive_name}.sha256"
done
echo "created: ${archive}"
echo "created: ${archive}.sha256"
