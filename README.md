# Delllo Networking

Delllo Networking is a semantic matchmaking system designed to intelligently connect users based on objectives, skills, and role preferences. The system prioritizes semantic relevance, balanced scoring across multiple objectives, and post-retrieval role alignment to produce high-quality networking matches.

## Matchmaking Pipeline

The end-to-end matchmaking flow follows these stages:

User Profile (Objectives + Role Preference)
|
v
Candidate Profiles
|
v
Profile → Semantic Document Construction
|
v
ChromaDB Indexing
|
v
Objective-by-Objective Semantic Retrieval
|
v
Per-Objective Score Normalization
|
v
Score Aggregation Across Objectives
|
v
Role Alignment Scoring (Post-retrieval)
|
v
Final Ranking (Top-K Matches)

