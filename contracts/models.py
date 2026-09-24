from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    analyst = "analyst"
    planner = "planner"
    commander = "commander"


class DoctrineRule(BaseModel):
    id: str
    text: str
    source: str
    constraint_type: str


class Unit(BaseModel):
    id: str
    name: str
    type: str
    strength: int
    location: str
    available: bool


class ForceList(BaseModel):
    scenario_id: str
    role_used: UserRole
    units: list[Unit]


class Action(BaseModel):
    action_type: str
    unit_id: str | None = None
    location: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    valid: bool
    violations: list[str] = Field(default_factory=list)
    action: Action


class CampaignDraft(BaseModel):
    scenario_id: str
    version: str
    actions: list[ValidationResult]
    metadata: dict[str, Any] = Field(default_factory=dict)


class SanityReport(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)
    force_ratio: float | None = None
    feasibility_score: float | None = None


class ToolCall(BaseModel):
    tool: str
    args: dict[str, Any]
    result: Any | None = None


class AgentTrace(BaseModel):
    question: str
    scenario_id: str
    user_role: UserRole
    tool_calls: list[ToolCall]
    final_output: str | None = None
    refused: bool = False
    escalated: bool = False
