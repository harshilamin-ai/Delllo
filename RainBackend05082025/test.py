import json
import logging
from openpyxl import Workbook

from models import PersonProfile
from matchmaking import rank_best_matches_per_objective

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROFILES_FILE = "data/people_profiles.json"
OBJECTIVES_FILE = "data/userProfileNetworkingObjectives.json"
OUTPUT_FILE = "matchmaking_results.xlsx"


# =========================================================
# Helpers to map JSON → PersonProfile
# =========================================================

def extract_skills(p: dict):
    return [
        s.get("skill")
        for s in p.get("top_skills", [])
        if isinstance(s, dict) and s.get("skill")
    ]


def extract_solutions(p: dict):
    return [s for s in p.get("solutions_offered", []) if isinstance(s, str)]


def extract_bio(p: dict):
    role = p.get("current_role", {}) or {}
    parts = [
        role.get("title"),
        role.get("company"),
        role.get("location"),
    ]
    return " | ".join([p for p in parts if p])


# =========================================================
# Load profiles
# =========================================================

def load_profiles():
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        people = json.load(f)

    profiles = {}

    for p in people:
        profile = PersonProfile(
            id=p["id"],
            name=p["name"],
            bio=extract_bio(p),
            skills=extract_skills(p),
            solutions=extract_solutions(p),
            interests=[],
            objectives=[]
        )
        profiles[p["id"]] = profile

    return profiles


# =========================================================
# Load objectives
# =========================================================

def load_users_with_objectives(profiles):
    with open(OBJECTIVES_FILE, "r", encoding="utf-8") as f:
        objectives = json.load(f)

    users = []

    for obj in objectives:
        user_id = obj["user_id"]
        if user_id not in profiles:
            continue

        profile = profiles[user_id]
        profile.objectives = obj.get("objectives", [])

        users.append(profile)

    return users


# =========================================================
# Main
# =========================================================

def main():
    logger.info("Loading profiles...")
    profiles = load_profiles()

    logger.info("Loading objectives...")
    users = load_users_with_objectives(profiles)

    all_candidates = list(profiles.values())

    logger.info("Creating Excel workbook...")
    wb = Workbook()
    ws = wb.active
    ws.title = "Matchmaking Results"

    ws.append([
        "User ID",
        "User Name",
        "Profile_JSON",
        "Networking_Objectives_JSON",
        "Match_1_Name",
        "Match_1_Reason",
        "Match_2_Name",
        "Match_2_Reason",
        "Match_3_Name",
        "Match_3_Reason",
    ])

    for user in users:
        candidates = [c for c in all_candidates if c.id != user.id]

        # ✅ This already generates LLM reasons internally
        results = rank_best_matches_per_objective(user, candidates)

        row = [
            user.id,
            user.name,
            json.dumps(user.dict(), ensure_ascii=False),
            json.dumps(
                {"user_id": user.id, "objectives": user.objectives},
                ensure_ascii=False
            )
        ]

        # ---- Take TOP 3 people ----
        for match in results[:3]:
            row.append(match["person"])

            # ✅ Combine LLM reasons from all objectives
            combined_reason = " | ".join(
                d["reason"] for d in match.get("details", [])
            )

            row.append(combined_reason)

        # ---- Pad if fewer than 3 matches ----
        while len(row) < 10:
            row.append("")

        ws.append(row)
        logger.info(f"Processed user: {user.name}")

    logger.info(f"Saving Excel file to {OUTPUT_FILE}")
    wb.save(OUTPUT_FILE)
    logger.info("Excel file created successfully ✅")



if __name__ == "__main__":
    main()
