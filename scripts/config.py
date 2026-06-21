"""
DataOS - Configuration Loader

Reads credentials from .env file in workspace root.
Provides helpers for loading API keys and Google credentials.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from workspace root (one level up from scripts/)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = WORKSPACE_ROOT / ".env"

load_dotenv(ENV_PATH)

# Some networks (corporate firewalls, antivirus) intercept TLS with a local
# root certificate that gRPC-based clients (e.g. Google Analytics) don't trust
# by default. If a combined cert bundle exists, point gRPC at it.
_COMBINED_ROOTS = WORKSPACE_ROOT / "credentials" / "combined-roots.pem"
if _COMBINED_ROOTS.exists():
    os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", str(_COMBINED_ROOTS))


def get_env(key, required=True):
    """
    Get an environment variable. Returns None if not set.
    Callers handle missing credentials gracefully (skip the collector).
    """
    value = os.getenv(key, "").strip()
    if not value:
        return None
    return value


def get_env_prefixed(prefix):
    """
    Get all environment variables starting with a prefix, as {suffix: value}.
    Used for multi-account setups (e.g. GA4_PROPERTY_ID_GOIA, GA4_PROPERTY_ID_SM).
    """
    result = {}
    for key, value in os.environ.items():
        if key.startswith(prefix) and value.strip():
            suffix = key[len(prefix):].lstrip("_")
            result[suffix] = value.strip()
    return result


def get_google_credentials_path():
    """
    Get the path to the Google service account JSON file.
    Resolves relative paths against the workspace root.
    """
    path = get_env("GOOGLE_SERVICE_ACCOUNT_JSON")
    if path is None:
        return None
    full_path = Path(path)
    if not full_path.is_absolute():
        full_path = WORKSPACE_ROOT / path
    if not full_path.exists():
        return None
    return str(full_path)
