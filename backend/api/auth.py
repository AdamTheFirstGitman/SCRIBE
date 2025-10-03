"""
Authentication API endpoints
Simple auth for single user (King)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user_id: str
    session_id: str
    expires_at: datetime


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Simple auth check for single user"""

    logger.info("Login attempt", username=request.username)

    # Credentials check
    if request.username == "KING" and request.password == "Faire la diff":
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=30)

        logger.info("Login successful", username=request.username, session_id=session_id)

        return LoginResponse(
            success=True,
            user_id="king_001",
            session_id=session_id,
            expires_at=expires_at
        )

    logger.warning("Login failed - incorrect credentials", username=request.username)

    raise HTTPException(
        status_code=401,
        detail="Identifiants incorrects"
    )
