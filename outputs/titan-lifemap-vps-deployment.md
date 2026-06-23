# Titan LifeMap — VPS Deployment

**Target:** Hostinger VPS running the aios-starter-kit workspace
**Domain:** api.sustain-momentum.com
**Service:** titan-lifemap (FastAPI via uvicorn, managed by systemd)

---

## Prerequisites

These steps assume:
- Git repository is pushed to GitHub and the VPS has a working clone
- The VPS already runs CommandOS (systemd service `aios-command`)
- Python 3.11+ with a `.venv` at the workspace root
- Nginx is installed (`apt install nginx`)
- Certbot is installed (`apt install certbot python3-certbot-nginx`)

---

## Step 1: Pull latest code and install dependencies

```bash
cd /path/to/aios-starter-kit
git pull origin main
.venv/bin/pip install fastapi uvicorn pyyaml jinja2 pydantic anthropic
```

WeasyPrint (PDF generation) requires system libraries:
```bash
apt install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi-dev
.venv/bin/pip install weasyprint
```

---

## Step 2: Add .env variables

The following variables are needed in the workspace `.env` (if not already present):

```
# Titan LifeMap (email + webhook — add when ready)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=patrick@sustain-momentum.com
SMTP_PASSWORD=<google-workspace-app-password>
MAKE_WEBHOOK_URL=<make.com-webhook-url>
```

The `ANTHROPIC_API_KEY` is already in `.env` from the CommandOS setup.

---

## Step 3: Create the systemd service

Create `/etc/systemd/system/titan-lifemap.service`:

```ini
[Unit]
Description=Titan LifeMap API (FastAPI)
After=network.target

[Service]
Type=simple
User=patrick
WorkingDirectory=/path/to/aios-starter-kit
ExecStart=/path/to/aios-starter-kit/.venv/bin/uvicorn apps.titan_lifemap.main:app --host 127.0.0.1 --port 8001 --workers 2
Restart=always
RestartSec=5
Environment=PYTHONPATH=/path/to/aios-starter-kit

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable titan-lifemap
systemctl start titan-lifemap
systemctl status titan-lifemap
```

Verify it's running:
```bash
curl http://127.0.0.1:8001/health
# Expected: {"status":"ok","service":"titan-lifemap"}
```

---

## Step 4: Nginx reverse proxy

Add to `/etc/nginx/sites-available/api.sustain-momentum.com`:

```nginx
server {
    listen 80;
    server_name api.sustain-momentum.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

Enable and test:
```bash
ln -s /etc/nginx/sites-available/api.sustain-momentum.com /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## Step 5: SSL via Certbot

```bash
certbot --nginx -d api.sustain-momentum.com
```

Certbot will update the nginx config automatically. Test:
```bash
curl https://api.sustain-momentum.com/health
# Expected: {"status":"ok","service":"titan-lifemap"}
```

---

## Verification

```bash
# Service running
systemctl is-active titan-lifemap

# Logs
journalctl -u titan-lifemap -n 50 --no-pager

# API docs (FastAPI auto-generated)
curl https://api.sustain-momentum.com/docs
```

---

## Common Operations

**Redeploy after code change:**
```bash
cd /path/to/aios-starter-kit
git pull origin main
systemctl restart titan-lifemap
```

**View recent logs:**
```bash
journalctl -u titan-lifemap -n 100 -f
```

**Check config is valid:**
```bash
cd /path/to/aios-starter-kit
.venv/bin/python apps/titan_lifemap/config_loader.py
```
