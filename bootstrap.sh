#!/usr/bin/env bash
set -euo pipefail

MANIFEST_REPO="https://github.com/fuquery/.github.git"

if ! command -v repo &>/dev/null; then
    echo "ERROR: 'repo' is not installed. Please install it first."
    exit 1
fi

echo "Initializing repo workspace..."
repo init -u "$MANIFEST_REPO"

echo "Syncing all repositories..."
repo sync -c -j$(nproc)
