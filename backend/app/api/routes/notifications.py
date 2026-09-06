import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message, Notification, NotificationPublic, NotificationsPublic

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationsPublic)
def read_notifications(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve the current user's notifications, newest first.
    """
    count_statement = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current_user.id)
    )
    count = session.exec(count_statement).one()
    statement = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(col(Notification.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    notifications = session.exec(statement).all()
    data = [NotificationPublic.model_validate(n) for n in notifications]
    return NotificationsPublic(data=data, count=count)


@router.post("/{id}/read", response_model=NotificationPublic)
def mark_notification_read(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Mark a single notification as read.
    """
    notification = session.get(Notification, id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    notification.is_read = True
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


@router.delete("/{id}")
def delete_notification(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a notification.
    """
    notification = session.get(Notification, id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(notification)
    session.commit()
    return Message(message="Notification deleted successfully")
