"""Shared data shapes for solutions, critiques and the execution trace."""

import time

from pydantic import BaseModel, Field


class Solution(BaseModel):
    agent: str
    content: str
    confidence: float = Field(ge=0.0, le=1.0)


class Critique(BaseModel):
    correctness: bool
    missing_information: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    agree: bool


class TraceEvent(BaseModel):
    step: str
    agent: str
    iteration: int
    payload: dict
    timestamp: float = Field(default_factory=time.time)


class RunResult(BaseModel):
    final_answer: str
    consensus_reached: bool
    iterations_used: int
    trace: list[TraceEvent]
