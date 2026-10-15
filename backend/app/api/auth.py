from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_agent
from app.core.security import verify_password, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserLogin, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user with email and password.
    Returns signed JWT access token and user profile on success.
    """
    email_clean = credentials.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue token containing verified subject ID and role
    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve profile of the currently authenticated user.
    """
    return current_user


@router.get("/agent-only-test")
def test_agent_rbac(current_agent: User = Depends(require_agent)):
    """
    Test endpoint strictly restricted to users with the 'agent' role.
    Employees calling this receive HTTP 403 Forbidden.
    """
    return {
        "message": f"Hello Agent {current_agent.name}! RBAC check passed.",
        "agent_id": current_agent.id,
        "role": current_agent.role,
    }
