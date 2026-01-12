import logging
from typing import List, Dict, Optional

import chromadb
from chromadb.config import Settings

from models import PersonProfile

# =========================================================
# Logging
# =========================================================

logger = logging.getLogger("matchmaking")
logging.basicConfig(level=logging.INFO)

# =========================================================
# Configuration
# =========================================================

CHROMA_DIR = "./chroma"
COLLECTION_NAME = "people_profiles"

CHROMA_RECALL_K = 25
RETURN_TOP_K = 5

# =========================================================
# Role taxonomy
# =========================================================

ROLE_TAXONOMY = {
    "Founder": ["founder", "co-founder", "ceo"],
    "DecisionMaker": ["cto", "cio", "vp", "director", "head"],
    "Builder": ["engineer", "developer", "data scientist", "designer"],
    "Advisor": ["advisor", "consultant", "partner"],
}

ROLE_PREFERENCE = {
    "Founder": ["Advisor", "Builder"],
    "DecisionMaker": ["Builder", "Advisor"],
    "Builder": ["Founder", "DecisionMaker"],
    "Advisor": ["Founder", "DecisionMaker"],
}

ROLE_MULTIPLIER = {
    "perfect": 1.2,
    "good": 1.1,
    "neutral": 1.0,
}

# =========================================================
# Embedding weights
# =========================================================

FIELD_WEIGHTS = {
    "skills": 2,
    "solutions": 3,
    "bio": 1,
}

# =========================================================
# ChromaDB (clean init)
# =========================================================

_chroma_client = chromadb.Client(
    Settings(persist_directory=CHROMA_DIR)
)

try:
    _chroma_client.delete_collection(COLLECTION_NAME)
except Exception:
    pass

_collection = _chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)

# =========================================================
# Role helpers
# =========================================================

def extract_role(profile: PersonProfile) -> Optional[str]:
    for attr in ("role", "title", "designation"):
        if hasattr(profile, attr):
            v = getattr(profile, attr)
            if isinstance(v, str) and v.strip():
                return v

    if hasattr(profile, "roles"):
        roles = getattr(profile, "roles")
        if isinstance(roles, list) and roles:
            return roles[0]

    return None


def infer_role_category(role: Optional[str]) -> Optional[str]:
    if not role:
        return None

    role = role.lower()
    for cat, keys in ROLE_TAXONOMY.items():
        if any(k in role for k in keys):
            return cat
    return None


def role_alignment_multiplier(
    user_role: Optional[str],
    candidate_role: Optional[str],
) -> float:

    if not user_role or not candidate_role:
        return ROLE_MULTIPLIER["neutral"]

    if candidate_role in ROLE_PREFERENCE.get(user_role, []):
        return ROLE_MULTIPLIER["perfect"]

    return ROLE_MULTIPLIER["good"]

# =========================================================
# Indexing
# =========================================================

def profile_to_document(p: PersonProfile) -> str:
    return " ".join(
        [
            (" ".join(p.skills or []) + " ") * FIELD_WEIGHTS["skills"],
            (" ".join(p.solutions or []) + " ") * FIELD_WEIGHTS["solutions"],
            p.bio or "",
        ]
    )


def ensure_indexed(candidates: List[PersonProfile]):
    documents, metadatas, ids = [], [], []

    for p in candidates:
        documents.append(profile_to_document(p))
        metadatas.append({"person_id": p.id})
        ids.append(p.id)

    _collection.add(documents=documents, metadatas=metadatas, ids=ids)
    logger.info(f"Indexed {len(documents)} profiles into ChromaDB")

# =========================================================
# Matchmaking + DEBUG EXPLAIN MODE
# =========================================================

def rank_best_matches_per_objective(
    user: PersonProfile,
    candidates: List[PersonProfile],
    debug: bool = False,
):

    ensure_indexed(candidates)

    candidate_map = {c.id: c for c in candidates}
    user_role_cat = infer_role_category(extract_role(user))

    aggregated_scores: Dict[str, float] = {}
    debug_trace: Dict[str, List[Dict]] = {}

    for objective in user.objectives:
        results = _collection.query(
            query_texts=[objective],
            n_results=CHROMA_RECALL_K,
            include=["distances"],
        )

        for cid, dist in zip(results["ids"][0], results["distances"][0]):
            candidate = candidate_map.get(cid)
            if not candidate:
                continue

            semantic_score = 1 / (1 + dist)
            candidate_role_cat = infer_role_category(extract_role(candidate))
            role_mult = role_alignment_multiplier(
                user_role_cat, candidate_role_cat
            )

            final_score = semantic_score * role_mult

            aggregated_scores[cid] = max(
                aggregated_scores.get(cid, 0.0),
                final_score,
            )

            if debug:
                debug_trace.setdefault(cid, []).append(
                    {
                        "objective": objective,
                        "distance": round(dist, 4),
                        "semantic_score": round(semantic_score, 4),
                        "role_multiplier": role_mult,
                        "final_score": round(final_score, 4),
                        "candidate_role": candidate_role_cat,
                    }
                )

    ranked = sorted(
        aggregated_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    results = []
    for cid, score in ranked[:RETURN_TOP_K]:
        entry = {
            "person": cid,
            "name": candidate_map[cid].name,
            "role": extract_role(candidate_map[cid]),
            "score": round(score, 4),
        }

        if debug:
            entry["debug"] = debug_trace.get(cid, [])

        results.append(entry)

    if debug:
        logger.info("==== DEBUG MATCH EXPLANATION ====")
        for r in results:
            logger.info(r)

    return results
