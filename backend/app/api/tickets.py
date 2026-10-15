from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.deps import get_current_user, require_agent
from app.db.session import get_db
from app.models.user import User
from app.models.ticket import Ticket
from app.models.audit import OverrideAuditLog
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    ClassificationOverrideRequest,
    TicketReplyRequest,
    ALLOWED_CATEGORIES,
    ALLOWED_PRIORITIES,
)
from app.schemas.audit import OverrideAuditResponse

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


def _deterministic_placeholder_classifier(title: str, description: str):
    """
    Deterministic rule-based placeholder classification for Phase 3.
    This will be enhanced with live Groq LLM structured inference in Phase 4.
    """
    text = f"{title} {description}".lower()

    # Category matching
    if any(k in text for k in ["vpn", "wifi", "network", "laptop", "battery", "screen", "login", "password"]):
        category = "IT"
    elif any(k in text for k in ["leave", "holiday", "sick", "salary", "payroll", "benefits", "policy"]):
        category = "HR"
    elif any(k in text for k in ["expense", "reimbursement", "invoice", "receipt", "finance", "budget"]):
        category = "Finance"
    elif any(k in text for k in ["desk", "chair", "badge", "access card", "parking", "building", "office"]):
        category = "Admin"
    else:
        category = "Other"

    # Priority matching
    if any(k in text for k in ["urgent", "critical", "emergency", "immediately", "broken", "blocked", "dying"]):
        priority = "High"
    elif any(k in text for k in ["soon", "important", "slow", "error", "failing"]):
        priority = "Medium"
    else:
        priority = "Low"

    draft_reply = (
        f"Thank you for contacting QuickDesk Support regarding '{title}'. "
        f"Our team has received your ticket and categorized it under {category} with {priority} priority. "
        "A support technician is reviewing your request and will follow up shortly."
    )

    return category, priority, draft_reply


from app.services.classifier import classify_ticket


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new support ticket.
    - Derived employee_id comes exclusively from the authenticated user.
    - Applies initial AI classification (Groq LLM or deterministic fallback).
    - Stores immutable baselines for audit and evaluation metrics.
    """
    # Execute AI classification with safe fallback
    classification = classify_ticket(ticket_in.title, ticket_in.description)

    draft_reply = (
        f"Thank you for contacting QuickDesk Support regarding '{ticket_in.title}'. "
        f"Our team has categorized your ticket under {classification.category} ({classification.priority} priority). "
        "A support technician is reviewing your request and will follow up shortly."
    )

    ticket = Ticket(
        title=ticket_in.title.strip(),
        description=ticket_in.description.strip(),
        attachment_filename=ticket_in.attachment_filename.strip() if ticket_in.attachment_filename else None,
        employee_id=current_user.id,
        # Active values
        category=classification.category,
        priority=classification.priority,
        # Immutable AI baseline
        ai_suggested_category=classification.category,
        ai_suggested_priority=classification.priority,
        ai_suggestion_method=classification.method,
        status="Open",
        ai_draft_reply=draft_reply,
        final_reply=None,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/my", response_model=List[TicketResponse])
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve tickets submitted by the authenticated user only.
    Employees can never see other employees' tickets.
    """
    tickets = (
        db.query(Ticket)
        .filter(Ticket.employee_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )
    return tickets


@router.get("", response_model=List[TicketResponse])
def get_all_tickets_agent(
    search: Optional[str] = Query(None, description="Search ticket title"),
    status: Optional[str] = Query(None, description="Filter by status: Open or Resolved"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db),
    current_agent: User = Depends(require_agent),
):
    """
    Agent-only endpoint to list, search, and filter all tickets across the organization.
    """
    query = db.query(Ticket)

    if search:
        search_clean = f"%{search.strip().lower()}%"
        query = query.filter(Ticket.title.ilike(search_clean))

    if status:
        query = query.filter(Ticket.status == status)

    if category:
        query = query.filter(Ticket.category == category)

    if priority:
        query = query.filter(Ticket.priority == priority)

    return query.order_by(Ticket.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket_detail(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single ticket by ID.
    - If user is an employee, they can only view their own ticket (returns 404 if not found or unauthorized).
    - If user is an agent, they can view any ticket.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Cross-employee authorization check: return 404 to avoid ID enumeration
    if current_user.role == "employee" and ticket.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    return ticket


@router.patch("/{ticket_id}/classification", response_model=TicketResponse)
def override_ticket_classification(
    ticket_id: int,
    override_in: ClassificationOverrideRequest,
    db: Session = Depends(get_db),
    current_agent: User = Depends(require_agent),
):
    """
    Agent-only endpoint to override a ticket's category or priority.
    - Validates values against allowed sets.
    - Creates an atomic entry in override_audit_logs only if a value actually changed.
    - Preserves immutable original AI suggestions.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    changed = False

    # Check category override
    if override_in.category is not None:
        if override_in.category not in ALLOWED_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid category. Allowed: {sorted(list(ALLOWED_CATEGORIES))}",
            )
        if override_in.category != ticket.category:
            audit_entry = OverrideAuditLog(
                ticket_id=ticket.id,
                agent_id=current_agent.id,
                field_name="category",
                old_value=ticket.category,
                new_value=override_in.category,
            )
            db.add(audit_entry)
            ticket.category = override_in.category
            changed = True

    # Check priority override
    if override_in.priority is not None:
        if override_in.priority not in ALLOWED_PRIORITIES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid priority. Allowed: {sorted(list(ALLOWED_PRIORITIES))}",
            )
        if override_in.priority != ticket.priority:
            audit_entry = OverrideAuditLog(
                ticket_id=ticket.id,
                agent_id=current_agent.id,
                field_name="priority",
                old_value=ticket.priority,
                new_value=override_in.priority,
            )
            db.add(audit_entry)
            ticket.priority = override_in.priority
            changed = True

    if changed:
        db.commit()
        db.refresh(ticket)

    return ticket


@router.post("/{ticket_id}/reply", response_model=TicketResponse)
def reply_and_resolve_ticket(
    ticket_id: int,
    reply_in: TicketReplyRequest,
    db: Session = Depends(get_db),
    current_agent: User = Depends(require_agent),
):
    """
    Agent-only endpoint to send the final reply and resolve the ticket.
    - Rejects resolving an already resolved ticket.
    - Stores final_reply while preserving ai_draft_reply intact.
    - Marks status = Resolved and sets resolved_at timestamp.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    if ticket.status == "Resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket is already resolved. Cannot submit duplicate final reply.",
        )

    reply_clean = reply_in.reply.strip()
    if not reply_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reply cannot be empty",
        )

    ticket.final_reply = reply_clean
    ticket.status = "Resolved"
    ticket.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}/audit", response_model=List[OverrideAuditResponse])
def get_ticket_audit_logs(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_agent: User = Depends(require_agent),
):
    """
    Agent-only endpoint to view the complete override history of a ticket.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    audit_logs = (
        db.query(OverrideAuditLog)
        .filter(OverrideAuditLog.ticket_id == ticket_id)
        .order_by(OverrideAuditLog.created_at.desc())
        .all()
    )
    return audit_logs
