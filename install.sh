#!/usr/bin/env bash
# Universal Agent (uag) — Production One-Line Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/Max000110/universal-agent/main/install.sh | bash
set -e

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}=== Installing Universal Agent CLI (uag) ===${RESET}"

# 1. Detect Environment & Configure Termux Build Toolchain Variables
IS_TERMUX=0
if [ -n "$PREFIX" ] && [[ "$PREFIX" == *"com.termux"* ]]; then
    IS_TERMUX=1
    echo -e "• Detected Environment: ${YELLOW}Termux (Android POSIX)${RESET}"
    echo -e "• ${YELLOW}Notice: Mobile ARM setup may take 1-2 minutes. Please remain patient...${RESET}"
    
    # Fix Issue 3 & 5: Export NDK Android API level and disable heavy mobile Rust Fat LTO
    export DEBIAN_FRONTEND=noninteractive
    export ANDROID_API_LEVEL="${ANDROID_API_LEVEL:-24}"
    export CARGO_PROFILE_RELEASE_LTO="false"
    export RUSTFLAGS="${RUSTFLAGS} -C lto=off"
elif [ -f "/etc/os-release" ]; then
    echo -e "• Detected Environment: ${YELLOW}Linux / Ubuntu${RESET}"
else
    echo -e "• Detected Environment: ${YELLOW}Generic POSIX${RESET}"
fi

# 2. Check/Install System Dependencies & Pre-compiled Termux Binary Packages
if [ "$IS_TERMUX" -eq 1 ]; then
    echo -e "• Ensuring non-interactive Termux dependencies (python, git, cryptography, pydantic)..."
    # Fix Issue 1 & 2: Install native pre-compiled Termux C/Rust binary packages
    pkg install -y python git python-cryptography python-pydantic maturin 2>/dev/null || true
else
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not installed.${RESET}"
        exit 1
    fi
fi

# 3. Setup App Directory and Virtual Environment
APP_DIR="${HOME}/.antigravitycli"
VENV_DIR="${APP_DIR}/venv"
BIN_DIR="${HOME}/.local/bin"

mkdir -p "${APP_DIR}"
mkdir -p "${BIN_DIR}"

# Fix Issue 2 & 4: Use --system-site-packages on Termux to inherit pre-compiled binary packages
if [ ! -d "${VENV_DIR}" ]; then
    echo -e "• Creating Python virtual environment in ${VENV_DIR}..."
    if [ "$IS_TERMUX" -eq 1 ]; then
        python3 -m venv --system-site-packages "${VENV_DIR}"
    else
        python3 -m venv "${VENV_DIR}"
    fi
fi

# 4. Install / Update Package
echo -e "• Upgrading pip, setuptools, and wheel..."
"${VENV_DIR}/bin/pip" install --upgrade pip setuptools wheel --no-warn-script-location

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
if [ -f "${SCRIPT_DIR}/pyproject.toml" ]; then
    echo -e "• Installing package from local source directory..."
    if [ "$IS_TERMUX" -eq 1 ]; then
        "${VENV_DIR}/bin/pip" install --no-build-isolation -e "${SCRIPT_DIR}" || "${VENV_DIR}/bin/pip" install -e "${SCRIPT_DIR}"
    else
        "${VENV_DIR}/bin/pip" install -e "${SCRIPT_DIR}"
    fi
else
    TEMP_CLONE="${APP_DIR}/source_tmp"
    rm -rf "${TEMP_CLONE}"
    echo -e "• Cloning latest release from GitHub (Max000110/universal-agent)..."
    git clone --depth=1 https://github.com/Max000110/universal-agent.git "${TEMP_CLONE}"
    echo -e "• Installing Universal Agent python dependencies..."
    if [ "$IS_TERMUX" -eq 1 ]; then
        "${VENV_DIR}/bin/pip" install --no-build-isolation "${TEMP_CLONE}" || "${VENV_DIR}/bin/pip" install "${TEMP_CLONE}"
    else
        "${VENV_DIR}/bin/pip" install "${TEMP_CLONE}"
    fi
    rm -rf "${TEMP_CLONE}"
fi

# 5. Create Global Executable Symlinks
echo -e "• Symlinking global CLI launchers..."
for cmd_name in universal-agent uag antigravity; do
    ln -sf "${VENV_DIR}/bin/universal-agent" "${BIN_DIR}/${cmd_name}"
    if [ "$IS_TERMUX" -eq 1 ] && [ -d "$PREFIX/bin" ]; then
        ln -sf "${VENV_DIR}/bin/universal-agent" "${PREFIX}/bin/${cmd_name}" || true
    fi
done

# 6. Ensure ~/.local/bin is in Shell PATH
SHELL_CONFIG=""
if [ -n "$ZSH_VERSION" ] || [ "$(basename "$SHELL")" = "zsh" ]; then
    SHELL_CONFIG="${HOME}/.zshrc"
elif [ -n "$BASH_VERSION" ] || [ -f "${HOME}/.bashrc" ]; then
    SHELL_CONFIG="${HOME}/.bashrc"
elif [ -f "${HOME}/.profile" ]; then
    SHELL_CONFIG="${HOME}/.profile"
fi

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo -e "• Adding ${BIN_DIR} to PATH in ${SHELL_CONFIG}..."
    if [ -n "${SHELL_CONFIG}" ]; then
        if ! grep -qF "${BIN_DIR}" "${SHELL_CONFIG}" 2>/dev/null; then
            echo "export PATH=\"${BIN_DIR}:\$PATH\"" >> "${SHELL_CONFIG}"
        fi
    fi
    export PATH="${BIN_DIR}:$PATH"
fi

# 7. Verification Test
echo ""
echo -e "${BOLD}${GREEN}✓ Installation Successful!${RESET}"
echo -e "Version: $("${VENV_DIR}/bin/universal-agent" version 2>/dev/null || echo 'v1.0.0')"
echo ""
echo -e "${BOLD}Quick Start:${RESET}"
echo -e "  1. Launch CLI     : ${CYAN}universal-agent${RESET}  or  ${CYAN}uag${RESET}"
echo -e "  2. Import Session : ${CYAN}uag import-session chatgpt${RESET}"
echo -e "  3. View Status    : ${CYAN}uag status${RESET}"
echo -e "  4. Update CLI     : ${CYAN}uag update${RESET}"
echo ""
