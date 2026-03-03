from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class EvidenceSpan(BaseModel):
    quote: str
    char_start: int
    char_end: int


class Entity(BaseModel):
    type: Literal["Person", "Organization", "Project", "Topic","Location"]
    name: str
    email: Optional[str] = None


class Claim(BaseModel):
    type: Literal[
        "RoleAssignment",
        "Decision",
        "Intent",
        "Commitment",
        "Ownership",
        "FinancialStatement",
        "MeetingPlan",
        "Misc"
    ]
    subject: str
    object: Optional[str] = None
    value: Optional[dict] = None
    event_time: Optional[datetime]
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: EvidenceSpan


class ExtractedOutput(BaseModel):
    entities: List[Entity]
    claims: List[Claim]