import csv
import logging
import os
from typing import List, Dict

import chromadb
from chromadb.config import Settings

from models import PersonProfile

# =========================================================
# Logging
# =========================================================

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# =========================================================
# Configuration (TUNABLE)
# =========================================================

# ChromaDB
CHROMA_DIR = "./chroma"
COLLECTION_NAME = "people_profiles"

# Structural weighting for embeddings
SKILLS_REPEAT = 3
SOLUTIONS_REPEAT = 4
BIO_REPEAT = 2   # weakest signal

# Retrieval
CHROMA_RECALL_K = 7
RETURN_TOP_K = 5

# Scoring weights
SEMANTIC_WEIGHT = 0.9
ROLE_WEIGHT = 0.0   # soft preference only

# Debugging
DEBUG_CSV = "matchmaking_debug.csv"
REINDEX_EVERY_RUN = True

# =========================================================
# ChromaDB Client
# =========================================================

chroma_client = chromadb.Client(
    Settings(persist_directory=CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)

# =========================================================
# Document Construction (Embeddings Only)
# =========================================================

def profile_to_document(p: PersonProfile) -> str:
    """
    Embedding document:
    - Skills & solutions dominate
    - Bio provides weak context
    - Role is EXCLUDED on purpose
    """

    skills = ", ".join(p.skills or [])
    solutions = ", ".join(p.solutions or [])
    bio = (p.bio or "")[:200]

    sections = []

    for _ in range(SKILLS_REPEAT):
        sections.append(f"Skills: {skills}")

    for _ in range(SOLUTIONS_REPEAT):
        sections.append(f"Solutions: {solutions}")

    for _ in range(BIO_REPEAT):
        sections.append(f"Background: {bio}")

    return "\n".join(sections).strip()

# =========================================================
# Indexing
# =========================================================

def ensure_indexed(candidates: List[PersonProfile]) -> None:
    global collection

    if REINDEX_EVERY_RUN:
        logger.info("🔄 Resetting Chroma collection")
        try:
            chroma_client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass

        collection = chroma_client.get_or_create_collection(
            name=COLLECTION_NAME
        )

    documents, ids = [], []

    for c in candidates:
        documents.append(profile_to_document(c))
        ids.append(c.id)

    if documents:
        collection.add(documents=documents, ids=ids)
        logger.info(f"✅ Indexed {len(documents)} profiles")

# =========================================================
# Role Scoring (NO embeddings, NO Chroma)
# =========================================================

def compute_role_alignment_score(
    objective: str,
    candidate: PersonProfile
) -> float:
    """
    Lightweight role alignment using keyword overlap.

    Uses EXISTING fields only:
    - role
    - title
    - designation
    - headline
    - roles[]
    """

    role_parts = []

    for field in [
        candidate.role,
        candidate.title,
        candidate.designation,
        candidate.headline,
    ]:
        if field:
            role_parts.append(field.lower())

    for r in candidate.roles or []:
        role_parts.append(r.lower())

    if not role_parts:
        return 0.0

    role_text = " ".join(role_parts)
    objective_words = set(objective.lower().split())
    role_words = set(role_text.split())

    overlap = objective_words.intersection(role_words)

    if not overlap:
        return 0.0

    # Normalize by objective length
    return min(len(overlap) / max(len(objective_words), 1), 1.0)

# =========================================================
# Matchmaking Pipeline
# =========================================================

def rank_best_matches_per_objective(
    user: PersonProfile,
    candidates: List[PersonProfile],
    debug: bool = False,
):
    """
    Pipeline:
    1. Index candidates (skills/solutions only)
    3. Normalize semantic score
    2. Semantic recall per objective
    4. Add role-based preference boost
    5. Aggregate across objectives
    """

    ensure_indexed(candidates)

    candidate_map: Dict[str, PersonProfile] = {
        c.id: c for c in candidates
    }

    aggregated_scores: Dict[str, float] = {}
    debug_rows = []

    objectives = user.objectives or []
    if not objectives:
        return []

    for obj_idx, objective in enumerate(objectives):

        query = (
            "I want someone who can help me achieve "
            f"the following objective: {objective}"
        )

        results = collection.query(
            query_texts=[query],
            n_results=min(CHROMA_RECALL_K, len(candidates)),
            include=["distances"],
        )

        ids = results["ids"][0]
        distances = results["distances"][0]

        raw_semantic_scores = [1 / (1 + d) for d in distances]
        total_raw = sum(raw_semantic_scores) or 1.0

        for rank, (cid, distance, raw) in enumerate(
            zip(ids, distances, raw_semantic_scores), start=1
        ):
            candidate = candidate_map.get(cid)
            if not candidate:
                continue

            semantic_score = raw / total_raw
            role_score = compute_role_alignment_score(
                objective, candidate
            )

            final_score = (
                SEMANTIC_WEIGHT * semantic_score
                + ROLE_WEIGHT * role_score
            )

            aggregated_scores[cid] = (
                aggregated_scores.get(cid, 0.0)
                + final_score
            )

            if debug:
                debug_rows.append({
                    "objective_index": obj_idx,
                    "objective": objective,
                    "candidate_id": cid,
                    "candidate_name": candidate.name,
                    "rank": rank,
                    "distance": round(distance, 4),
                    "semantic_score": round(semantic_score, 6),
                    "role_score": round(role_score, 6),
                    "final_score": round(final_score, 6),
                    "cumulative_score": round(
                        aggregated_scores[cid], 6
                    ),
                })

    # =====================================================
    # Debug CSV
    # =====================================================

    if debug and debug_rows:
        file_exists = os.path.exists(DEBUG_CSV)
        fieldnames = list(debug_rows[0].keys())

        with open(DEBUG_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(debug_rows)

        logger.info(f"📊 Debug CSV updated: {DEBUG_CSV}")

    # =====================================================
    # Final Ranking
    # =====================================================

    ranked = sorted(
        aggregated_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return [
        {
            "person": cid,
            "name": candidate_map[cid].name,
            "score": round(score, 6),
        }
        for cid, score in ranked[:RETURN_TOP_K]
    ]
