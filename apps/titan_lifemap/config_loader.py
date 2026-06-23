"""
Titan LifeMap - Configuration Loader

The ONLY module in this app that knows about config file paths or YAML
parsing. Every other module asks this module for config objects rather
than reading YAML directly.

Fails loudly (raises) if a required config file is missing or malformed -
a broken config should never silently degrade and reach a live session.
"""

from pathlib import Path
from functools import lru_cache

try:
    import yaml
except ImportError:
    raise ImportError("Missing 'pyyaml' - run: pip install pyyaml")

CONFIG_DIR = Path(__file__).resolve().parent / "config"

REQUIRED_STAGE_KEYS = {"name", "titan", "framing", "questions", "output_name"}
REQUIRED_SCORING_KEYS = {"behavioural_friction", "clarity_score", "momentum_plan"}


class ConfigError(Exception):
    """Raised when a config file is missing, malformed, or fails validation."""


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Required config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Malformed YAML in {path}: {e}") from e
    if data is None:
        raise ConfigError(f"Config file is empty: {path}")
    return data


@lru_cache(maxsize=1)
def get_stages() -> list[dict]:
    """Return the five Titan LifeMap discovery stages, in order, from stages.yaml."""
    data = _load_yaml(CONFIG_DIR / "stages.yaml")
    stages = data.get("stages")
    if not stages or not isinstance(stages, list):
        raise ConfigError("stages.yaml must contain a top-level 'stages' list")
    for i, stage in enumerate(stages):
        missing = REQUIRED_STAGE_KEYS - stage.keys()
        if missing:
            raise ConfigError(f"stages.yaml stage #{i} ('{stage.get('name', '?')}') "
                               f"missing required keys: {missing}")
    return stages


@lru_cache(maxsize=1)
def get_scoring_rules() -> dict:
    """Return the scoring rules (Clarity Score, Momentum Plan, Behavioural Friction) from scoring_rules.yaml."""
    data = _load_yaml(CONFIG_DIR / "scoring_rules.yaml")
    missing = REQUIRED_SCORING_KEYS - data.keys()
    if missing:
        raise ConfigError(f"scoring_rules.yaml missing required top-level keys: {missing}")
    return data


@lru_cache(maxsize=8)
def get_prompt(name: str) -> dict:
    """Return a named prompt config from config/prompts/{name}.yaml
    (e.g. get_prompt('conversation'), get_prompt('analysis'), get_prompt('reports'))."""
    data = _load_yaml(CONFIG_DIR / "prompts" / f"{name}.yaml")
    return data


@lru_cache(maxsize=8)
def get_report_template(name: str) -> dict:
    """Return a named report template config from config/report_templates/{name}.yaml
    (e.g. get_report_template('consumer'), get_report_template('internal'))."""
    data = _load_yaml(CONFIG_DIR / "report_templates" / f"{name}.yaml")
    if "sections" not in data:
        raise ConfigError(f"report_templates/{name}.yaml missing required 'sections' key")
    return data


def validate_all() -> None:
    """Load and validate every config file. Call at app startup so a broken
    config fails immediately and loudly, not partway through a live session."""
    get_stages()
    get_scoring_rules()
    for prompt_name in ("conversation", "analysis", "reports"):
        get_prompt(prompt_name)
    for report_name in ("consumer", "coaching", "adviser", "internal"):
        get_report_template(report_name)


if __name__ == "__main__":
    # Quick self-test - run this after editing any config file
    try:
        validate_all()
        stages = get_stages()
        print(f"All config valid. {len(stages)} stages loaded: "
              f"{[s['name'] for s in stages]}")
    except ConfigError as e:
        print(f"CONFIG ERROR: {e}")
        raise
