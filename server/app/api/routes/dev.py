from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...repositories.password_reset_token import PasswordResetTokenRepository

router = APIRouter(
    prefix="/dev",
    tags=["Development"],
)


@router.get("/password-reset-token/{token_hash}")
def get_password_reset_token(
    token_hash: str,
    db: Session = Depends(get_db),
):
    token = PasswordResetTokenRepository(db).get_by_hash(token_hash)

    if token is None:
        raise HTTPException(
            status_code=404,
            detail="Token not found",
        )

    return {
        "id": token.id,
        "user_id": token.user_id,
        "expires_at": token.expires_at,
        "used_at": token.used_at,
    }
