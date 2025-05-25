from pathlib import Path

THIS_FILE_PATH = Path(__file__)

WEBUI_DIR = THIS_FILE_PATH.parent.parent.parent

EXTENSIONS_DIR = WEBUI_DIR / "extensions"

CHARACTER_WILDCARDS_DIR = EXTENSIONS_DIR / "character-wildcards"
SD_DYNAMIC_PROMPTS_DIR = EXTENSIONS_DIR / "sd-dynamic-prompts"

CSS_PATH = CHARACTER_WILDCARDS_DIR / "style.css"

DATA_DIR = CHARACTER_WILDCARDS_DIR / "data"
CONFIG_PATH = DATA_DIR / "config.yaml"

DATABASE_FILE = DATA_DIR / "database.sqlite3"
