import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    attachment_filename = Column(String(255), nullable=True)

    employee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Current active classification
    category = Column(String(50), nullable=False, default="Other", index=True)
    priority = Column(String(20), nullable=False, default="Medium", index=True)

    # Original AI-suggested values (IMMUTABLE baseline for accuracy metrics)
    ai_suggested_category = Column(String(50), nullable=True)
    ai_suggested_priority = Column(String(20), nullable=True)
    ai_suggestion_method = Column(String(30), nullable=False, default="pending")  # "llm" | "fallback" | "pending"

    # Status: Open | Resolved
    status = Column(String(20), nullable=False, default="Open", index=True)

    # Separation of AI draft vs Agent Final Reply
    ai_draft_reply = Column(Text, nullable=True)
    final_reply = Column(Text, nullable=True)

    # Serialized citations list from RAG retrieval
    citations_json = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    employee = relationship("User", back_populates="tickets")
    audit_logs = relationship("OverrideAuditLog", back_populates="ticket", cascade="all, delete-orphan", order_by="OverrideAuditLog.created_at.desc()")

    @property
    def citations(self):
        if self.citations_json:
            try:
                return json.loads(self.citations_json)
            except Exception:
                return []
        return []

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} title='{self.title[:20]}' status='{self.status}'>"
