from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class OverrideAuditLog(Base):
    __tablename__ = "override_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    field_name = Column(String(50), nullable=False)  # "category" | "priority"
    old_value = Column(String(50), nullable=False)
    new_value = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="audit_logs")
    agent = relationship("User", back_populates="overrides")

    def __repr__(self) -> str:
        return f"<OverrideAuditLog id={self.id} ticket={self.ticket_id} {self.field_name}: {self.old_value}->{self.new_value}>"
