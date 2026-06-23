"""
Titan LifeMap - Configuration

Loads .env from workspace root. Single source for all environment access
within the Titan LifeMap app. Other modules import from here, never from
scripts/config.py (which is DataOS-specific).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = WORKSPACE_ROOT / ".env"

load_dotenv(ENV_PATH)

# gRPC TLS fix (same pattern as scripts/config.py — needed if Anthropic SDK
# uses gRPC internally on networks with TLS interception)
_COMBINED_ROOTS = WORKSPACE_ROOT / "credentials" / "combined-roots.pem"
if _COMBINED_ROOTS.exists():
    os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", str(_COMBINED_ROOTS))


def get_env(key: str, required: bool = True) -> str | None:
    value = os.getenv(key, "").strip()
    if not value:
        if required:
            raise EnvironmentError(
                f"Required environment variable '{key}' is not set. "
                f"Check your .env file at {ENV_PATH}"
            )
        return None
    return value


ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY")
SMTP_HOST = get_env("SMTP_HOST", required=False)
SMTP_PORT = get_env("SMTP_PORT", required=False)
SMTP_USER = get_env("SMTP_USER", required=False)
SMTP_PASSWORD = get_env("SMTP_PASSWORD", required=False)
MAKE_WEBHOOK_URL = get_env("MAKE_WEBHOOK_URL", required=False)
