#!/usr/bin/env bash
# Install Health Timer as a launchd LaunchAgent that auto-starts at login.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.jamesgriz.healthtimer"
PLIST_SRC="${REPO_DIR}/launchd/${LABEL}.plist"
PLIST_DST="${HOME}/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="${HOME}/Library/Logs"

# Prefer the venv interpreter if it exists, otherwise fall back to system python3.
if [[ -x "${REPO_DIR}/.venv/bin/python" ]]; then
    PYTHON_BIN="${REPO_DIR}/.venv/bin/python"
else
    PYTHON_BIN="$(command -v python3)"
fi

if [[ -z "${PYTHON_BIN}" ]]; then
    echo "error: python3 not found on PATH" >&2
    exit 1
fi

echo "→ Using Python: ${PYTHON_BIN}"
echo "→ Repo dir:     ${REPO_DIR}"
echo "→ Installing to: ${PLIST_DST}"

mkdir -p "${HOME}/Library/LaunchAgents" "${LOG_DIR}"

# Substitute placeholders into the plist.
sed \
    -e "s|__PYTHON__|${PYTHON_BIN}|g" \
    -e "s|__INSTALL_DIR__|${REPO_DIR}|g" \
    -e "s|__LOG_DIR__|${LOG_DIR}|g" \
    "${PLIST_SRC}" > "${PLIST_DST}"

# Reload if already loaded.
if launchctl list | grep -q "${LABEL}"; then
    echo "→ Unloading existing agent"
    launchctl bootout "gui/$(id -u)" "${PLIST_DST}" 2>/dev/null || true
fi

echo "→ Loading agent"
launchctl bootstrap "gui/$(id -u)" "${PLIST_DST}"

echo
echo "✓ Installed. Logs: ${LOG_DIR}/healthtimer.log"
echo "  Status:    launchctl list | grep ${LABEL}"
echo "  Uninstall: ${REPO_DIR}/scripts/uninstall.sh"
