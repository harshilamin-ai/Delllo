import logging
import json
from pathlib import Path
from models import PersonProfile
from matchmaking import generate_pairing_summary

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

def run_networking_event(event_id: str):
    profiles_file = DATA_DIR / f"{event_id}_profiles.json"
    if not profiles_file.exists():
        logger.error(f"Missing profiles file: {profiles_file}")
        return
    try:
        raw = json.loads(profiles_file.read_text())
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {profiles_file}: {e}")
        return
    profiles = []
    for item in raw:
        try:
            profiles.append(PersonProfile(**item))
        except Exception as e:
            logger.error(f"Invalid profile {item}: {e}")
    if not profiles:
        logger.warning(f"No profiles for event '{event_id}'")
        return
    matchups = generate_pairing_summary(profiles)
    output_file = DATA_DIR / f"{event_id}_matchups.json"
    output_file.write_text(json.dumps(matchups, indent=2))
    logger.info(f"Matchups written to {output_file}")
