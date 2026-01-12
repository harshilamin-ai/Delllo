from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PersonProfile(BaseModel):
    id: str
    name: Optional[str] = None
    bio: Optional[str] = None

    skills: List[str] = Field(default_factory=list)
    solutions: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)

    # 🔑 ROLE / TITLE FIELDS
    role: Optional[str] = None
    currentRole: Optional[str] = None
    title: Optional[str] = None
    designation: Optional[str] = None
    headline: Optional[str] = None

    # 🔑 EXPERIENCE (VERY IMPORTANT)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"  # 🚀 DO NOT REMOVE
