#!/usr/bin/env bash
set -e

echo "=== Updating Antigravity CLI ==="

INSTALL_DIR="${HOME}/.antigravitycli"
VENV_DIR="${INSTALL_DIR}/venv"

if [ -d "${VENV_DIR}" ]; then
    echo "• Updating package in virtual environment..."
    "${VENV_DIR}/bin/pip" install --upgrade -e .
else
    echo "• Virtual environment not found. Running install.sh..."
    bash install.sh
fi

echo "✓ Update complete!"
