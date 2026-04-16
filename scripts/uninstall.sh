#!/usr/bin/env bash
# Stop and remove the Health Timer LaunchAgent.
set -euo pipefail

LABEL="com.jamesgriz.healthtimer"
PLIST_DST="${HOME}/Library/LaunchAgents/${LABEL}.plist"

if [[ -f "${PLIST_DST}" ]]; then
    echo "→ Unloading agent"
    launchctl bootout "gui/$(id -u)" "${PLIST_DST}" 2>/dev/null || true
    rm -f "${PLIST_DST}"
    echo "✓ Removed ${PLIST_DST}"
else
    echo "✓ Nothing to remove (${PLIST_DST} not found)"
fi
