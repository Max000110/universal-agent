#!/usr/bin/env bash
set -e

echo "=== Installing Antigravity CLI ==="

INSTALL_DIR="${HOME}/.antigravitycli"
VENV_DIR="${INSTALL_DIR}/venv"
BIN_DIR="${HOME}/.local/bin"

mkdir -p "${INSTALL_DIR}"
mkdir -p "${BIN_DIR}"

if [ ! -d "${VENV_DIR}" ]; then
    echo "• Creating Python virtual environment in ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
fi

echo "• Installing dependencies and antigravity package..."
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -e .

echo "• Symlinking binary to ${BIN_DIR}/antigravity..."
ln -sf "${VENV_DIR}/bin/antigravity" "${BIN_DIR}/antigravity"

echo ""
echo "✓ Installation successful!"
echo "Run 'antigravity' or '${BIN_DIR}/antigravity' to start."
