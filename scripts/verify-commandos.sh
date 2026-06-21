#!/bin/bash
# CommandOS - Dependency verification and final setup
# Run with: bash scripts/verify-commandos.sh

set -e

echo "=== Checking Python packages ==="
python3 -c "
from aiogram import Bot; print('aiogram OK')
from claude_agent_sdk import query; print('claude-agent-sdk OK')
from dotenv import load_dotenv; print('dotenv OK')
from weasyprint import HTML; print('weasyprint OK')
import matplotlib; print('matplotlib OK')
"

echo ""
echo "=== Checking .env keys ==="
python3 -c "
from dotenv import load_dotenv; import os; load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN', '')
group = os.getenv('TELEGRAM_GROUP_ID', '')
anthropic = os.getenv('ANTHROPIC_API_KEY', '')
print(f'Bot token: {\"OK\" if token else \"MISSING\"}')
print(f'Group ID: {\"OK\" if group else \"MISSING\"} ({group})')
print(f'Anthropic key: {\"OK\" if anthropic else \"MISSING\"}')
"

echo ""
echo "=== Creating data directory ==="
mkdir -p data/command
echo "data/command created"

echo ""
echo "=== All checks complete. If everything above says OK, you're ready to test the bot. ==="
