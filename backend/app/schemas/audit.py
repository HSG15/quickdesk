from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AgentSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class OverrideAuditResponse(BaseModel):
    id: int
    ticket_id: int
    agent_id: int
    agent: AgentSummary
    field_name: str
    old_value: str
    new_value: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
