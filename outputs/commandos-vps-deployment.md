# CommandOS — VPS Deployment Guide

Run these commands on your Linux VPS via SSH. Replace `patrick` with your actual VPS username wherever it appears.

---

## 1. Install prerequisites

```bash
# Update package list
sudo apt update

# Python 3.11+ and pip
sudo apt install -y python3 python3-pip python3-venv

# Node.js (for the Claude Code CLI)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Claude Code CLI
sudo npm install -g @anthropic-ai/claude-code

# PDF generation dependencies (WeasyPrint)
sudo apt install -y python3-weasyprint
```

Verify:
```bash
python3 --version    # should show 3.11+
node --version        # should show v20.x
claude --version      # should show a version number
```

---

## 2. Clone your workspace

```bash
git clone https://github.com/ZenWealth/patrick-aios.git
cd patrick-aios
```

---

## 3. Create your `.env` file

This is the one file NOT in git (it has your secrets). Create it directly on the server:

```bash
nano .env
```

Paste in everything from your local `.env` file — easiest way: open your local `.env` in a text editor, copy the whole thing, paste into nano, then `Ctrl+O` to save, `Ctrl+X` to exit.

At minimum, these three must be set for CommandOS to work (copy the actual values from your local `.env` — do not paste real keys into any file that gets committed to git):
```
TELEGRAM_BOT_TOKEN=<from your local .env>
TELEGRAM_GROUP_ID=<from your local .env>
ANTHROPIC_API_KEY=<from your local .env>
```

---

## 4. Set up Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install weasyprint matplotlib
```

Verify:
```bash
python3 -c "
from aiogram import Bot; print('aiogram OK')
from claude_agent_sdk import query; print('claude-agent-sdk OK')
from weasyprint import HTML; print('weasyprint OK')
import matplotlib; print('matplotlib OK')
"
```

---

## 5. Create the data directory

```bash
mkdir -p data/command
```

---

## 6. Test run (before making it a service)

```bash
source .venv/bin/activate
python -m apps.command.main
```

You should see a boot banner, config summary, and "Online — polling for messages."

**Test in Telegram:**
1. Open your "Command Centre" group, General topic
2. Send: "Hello! What workspace are you working in?"
3. Wait 10-30 seconds for the first response (it primes the agent)
4. It should respond with details about your GOIA/Sustain Momentum/GAIA workspace

If that works, press `Ctrl+C` to stop the manual run, then continue to step 7.

---

## 7. Set up as an always-on service (systemd)

Find your paths first:
```bash
pwd                                    # your workspace root — note this down
which python                          # while venv is active — note this down
whoami                                 # your username — note this down
```

Copy the service template:
```bash
sudo cp "module-installs/command-os-v1/AIOS Command OS/config/command-bot.service" /etc/systemd/system/command-bot.service
sudo nano /etc/systemd/system/command-bot.service
```

Replace these placeholders with the values from above:
- `__USERNAME__` → your username
- `__WORKSPACE_ROOT__` → your workspace root path (e.g. `/home/patrick/patrick-aios`)
- `__VENV_PYTHON__` → full path to venv python (e.g. `/home/patrick/patrick-aios/.venv/bin/python`)

Save (`Ctrl+O`, `Ctrl+X`), then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable command-bot
sudo systemctl start command-bot
sudo systemctl status command-bot
```

Should show "active (running)".

---

## Managing the bot

| Action | Command |
|---|---|
| Stop | `sudo systemctl stop command-bot` |
| Restart | `sudo systemctl restart command-bot` (or send `/reboot` in Telegram) |
| View live logs | `journalctl -u command-bot -f` |
| Check status | `sudo systemctl status command-bot` |

---

## Keeping it updated

Whenever changes are made to the workspace (locally or via Claude Code), pull them to the VPS:

```bash
cd ~/patrick-aios
git pull
sudo systemctl restart command-bot
```

---

## Command Reference (once running)

| Command | Where | What it does |
|---|---|---|
| `/new` | General | Spawn a fresh Sonnet agent in a new topic |
| `/new opus` | General | Spawn a fresh Opus agent (more capable, costs more) |
| `/name` | Any agent topic | Rename the topic based on the conversation |
| `/compact` | Any agent topic | Compress context if the agent starts forgetting things |
| `/reset` | Any agent topic | Clear the session and start fresh |
| `/help` | General | Show the command list |
| `/reboot` | Anywhere | Restart the bot process |

**Daily workflow:** General topic is your home base for quick questions across all three ventures. Use `/new` when you want a dedicated thread for deep work — research, drafting, analysis — so it doesn't clutter the General conversation.
