"""Activity log endpoints and helper."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db.database import get_db
from app.db.models import ActivityLog, User

router = APIRouter()


def log_activity(db: Session, user_id: int, action: str, detail: str) -> None:
    """Write one activity row. Call from any endpoint after a successful action."""
    db.add(ActivityLog(user_id=user_id, action=action, detail=detail))
    db.commit()


@router.get("")
def list_activity(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
):
    """Return the current user's recent activity, newest first."""
    rows = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return {
        "items": [
            {
                "id": r.id,
                "action": r.action,
                "detail": r.detail,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }
