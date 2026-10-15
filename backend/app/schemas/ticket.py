from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict

TicketCategory = Literal["IT", "HR", "Finance", "Admin", "Other"]
TicketPriority = Literal["Low", "Medium", "High"]
TicketStatus = Literal["Open", "Resolved"]

ALLOWED_CATEGORIES = {"IT", "HR", "Finance", "Admin", "Other"}
ALLOWED_PRIORITIES = {"Low", "Medium", "High"}


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Short summary of the issue")
    description: str = Field(..., min_length=5, max_length=5000, description="Full explanation of the problem")
    attachment_filename: Optional[str] = Field(None, max_length=255, description="Optional filename")


class TicketEmployeeSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TicketCitation(BaseModel):
    article_id: str
    title: str
    source: str
    category: Optional[str] = None
    score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    attachment_filename: Optional[str]
    employee_id: int
    employee: Optional[TicketEmployeeSummary] = None

    category: str
    priority: str

    ai_suggested_category: Optional[str] = None
    ai_suggested_priority: Optional[str] = None
    ai_suggestion_method: str = "pending"

    status: str
    ai_draft_reply: Optional[str] = None
    final_reply: Optional[str] = None
    citations: List[TicketCitation] = []

    created_at: datetime
    resolved_at: Optional[datetime] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassificationOverrideRequest(BaseModel):
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None


class TicketReplyRequest(BaseModel):
    reply: str = Field(..., min_length=1, max_length=5000, description="The reviewed and edited final reply")
