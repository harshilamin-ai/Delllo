from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import sys
import logging

from models import PersonProfile
from matchmaking import rank_best_matches_per_objective

# =========================================================
# Logging
# =========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# App init
# =========================================================

app = FastAPI(title="RAIN Networking Assistant")

# =========================================================
# Paths
# =========================================================

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(__file__)

DATA_DIR = os.path.join(BASE_DIR, "data")
# =========================================================
# Request Model
# =========================================================
class ChatRequest(BaseModel):
    user_id: str
    message: Optional[str] = None
# =========================================================
# JSON helpers
# =========================================================
def load_json(filename: str):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        logger.warning(f"Missing data file: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
# =========================================================
# FIELD MAPPERS
# =========================================================

def extract_skills(p: dict) -> List[str]:
    """
    top_skills -> ["Capital markets technology", ...]
    """
    return [
        s.get("skill")
        for s in p.get("top_skills", [])
        if isinstance(s, dict) and s.get("skill")
    ]


def extract_solutions(p: dict) -> List[str]:
    """
    solutions_offered -> list[str]
    """
    return [
        s for s in p.get("solutions_offered", [])
        if isinstance(s, str)
    ]


def extract_bio(p: dict) -> str:
    """
    Build a semantic bio from current_role
    """
    role = p.get("current_role", {}) or {}
    title = role.get("title", "")
    company = role.get("company", "")
    location = role.get("location", "")

    parts = [title, company, location]
    return " | ".join([x for x in parts if x])


def extract_role(p: dict) -> str:
    """
    Normalize role using ROLE_TAXONOMY
    """
    role = p.get("current_role", {}) or {}
    title = role.get("title", "")
    return title

# =========================================================
# Load user
# =========================================================

def load_user(user_id: str) -> PersonProfile | None:
    people = load_json("people_profiles_updated.json")
    objectives = load_json("userProfileNetworkingObjectives_updated.json")

    person = next((p for p in people if p["id"] == user_id), None)
    if not person:
        return None

    user_objectives = next(
        (o["objectives"] for o in objectives if o["user_id"] == user_id),
        []
    )

    return PersonProfile(
        id=person["id"],
        name=person["name"],
        role=extract_role(person),
        bio=extract_bio(person),
        skills=extract_skills(person),
        solutions=extract_solutions(person),
        objectives=user_objectives
    )

# =========================================================
# Load candidates
# =========================================================

def load_candidates(user_id: str) -> List[PersonProfile]:
    people = load_json("people_profiles_updated.json")
    objectives = load_json("userProfileNetworkingObjectives_updated.json")

    candidates: List[PersonProfile] = []

    for p in people:
        if p["id"] == user_id:
            continue

        person_objectives = next(
            (o["objectives"] for o in objectives if o["user_id"] == p["id"]),
            []
        )

        candidates.append(
            PersonProfile(
                id=p["id"],
                name=p["name"],
                role=extract_role(p),
                bio=extract_bio(p),
                skills=extract_skills(p),
                solutions=extract_solutions(p),
                objectives=person_objectives
            )
        )

    logger.info(f"Loaded {len(candidates)} candidates")
    return candidates

# =========================================================
# Routes
# =========================================================

@app.post("/chat")
def chat(request: ChatRequest):
    user = load_user(request.user_id)
    if not user:
        return {"error": "User not found"}

    candidates = load_candidates(user.id)

    matches = rank_best_matches_per_objective(user, candidates,debug=True)

    return {
        "user_id": user.id,
        "matches": matches
    }

# =========================================================
# Run (local)
# =========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )
