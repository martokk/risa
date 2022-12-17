import os
from pathlib import Path

from risa.config.config import RISA_PROFILES

# RISA PROJECT STRUCTURE
RISA_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STATS_PATH = RISA_PATH / "stats"
STAT_PATH = STATS_PATH / "stat"


# DATA STRUCTURE
DATA_PATH = RISA_PATH / "data"
CACHE_PATH = DATA_PATH / "cache"
LOGS_PATH = DATA_PATH / "logs"

LOG_FILE = LOGS_PATH / "log.log"
CACHE_PROFILES_FILE = CACHE_PATH / "profiles.yaml"
PROFILE_LOG_FILE = DATA_PATH / "profile_log.yaml"
DOWNLOAD_LOG_FILE = DATA_PATH / "download_log.yaml"
FEED_FILE = DATA_PATH / "feed.yaml"
SUBSCRIPTIONS_FILE = DATA_PATH / "subscriptions.yaml"
IMAGE_METADATA_FILE = DATA_PATH / "image_metadata.yaml"

# PROFILE STRUCTURE
RISA_PROFILES_PATH = Path(RISA_PROFILES)
TEMPLATE_PATH = RISA_PROFILES_PATH / "__TEMPLATE__"

TEMPLATE_USER_YAML_FILE = TEMPLATE_PATH / "user.yaml"


# PROFILE CONSTANTS
WIP_FOLDERNAME = "__wip__"
NO_NUDES_FOLDERNAME = "__no_nudes__"
UNKNOWN_FOLDERNAME = "__unknown__"
