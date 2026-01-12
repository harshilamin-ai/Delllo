# Delllo Networking

Delllo Networking is a semantic matchmaking system designed to intelligently connect users based on objectives, skills, and role preferences. The system prioritizes semantic relevance, balanced scoring across multiple objectives, and post-retrieval role alignment to produce high-quality networking matches.

## Matchmaking Pipeline

The end-to-end matchmaking flow follows these stages:

User Profile (Objectives + Role Preference) -> Candidate Profiles -> Profile → Semantic Document Construction -> ChromaDB Indexing -> Objective-by-Objective Semantic Retrieval -> Per-Objective Score Normalization ->Score Aggregation Across Objectives -> Role Alignment Scoring (Post-retrieval) -> Final Ranking (Top-K Matches)

