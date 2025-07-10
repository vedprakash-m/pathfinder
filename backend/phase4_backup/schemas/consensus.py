"""Consensus-related schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ConsensusCreate(BaseModel):
    """Schema for creating a consensus poll."""
    trip_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    options: List[str] = Field(..., min_items=2, max_items=10)

class ConsensusResponse(BaseModel):
    """Schema for consensus response."""
    id: str
    trip_id: str
    title: str
    description: Optional[str] = None
    options: List[str]
    responses: Dict[str, Any]
    ai_analysis: Optional[Dict[str, Any]] = None
    consensus_recommendation: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime

class ConsensusVote(BaseModel):
    """Schema for consensus voting."""
    option_index: int = Field(..., ge=0)
    weight: int = Field(default=1, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)

class ConsensusAnalysis(BaseModel):
    """Schema for AI consensus analysis."""
    agreement_level: float = Field(..., ge=0, le=1)
    top_choice: str
    conflicts: List[str]
    recommendations: List[str]
