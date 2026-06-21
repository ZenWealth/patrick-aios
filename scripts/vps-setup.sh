#!/bin/bash
# CommandOS - VPS prerequisite installer
# Run with: curl -fsSL https://raw.githubusercontent.com/ZenWealth/patrick-aios/main/scripts/vps-setup.sh | bash

set -e

echo "=== Installing Python ==="
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

echo "=== Installing Node.js ==="
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

echo "=== Installing Claude Code CLI ==="
sudo npm install -g @anthropic-ai/claude-code

echo "=== Installing WeasyPrint (PDF support) ==="
sudo apt install -y python3-weasyprint

echo ""
echo "=== Done. Versions installed: ==="
python3 --version
node --version
claude --version

echo ""
echo "Next: clone your workspace with:"
echo "  git clone https://github.com/ZenWealth/patrick-aios.git"
