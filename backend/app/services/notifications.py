"""
Notification service: small, focused wrapper around creating a
Notification row for a user. Kept separate from the route handlers so
other parts of the app (item creation today, more triggers later) can
fire a notification without depending on FastAPI request/response
plumbing.
"""

import uuid

from sqlmodel import Session, col, func, select

from app.models import Notification, NotificationCreate


def create_notification(
    *, session: Session, notification_in: NotificationCreate
) -> Notification:
    notification = Notification.model_validate(notification_in)
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def notify_item_created(*, session: Session, owner_id: uuid.UUID, item_title: str) -> Notification:
    """
    Fired whenever a new item is created (see api/routes/items.py) so the
    owner has a persistent record of it, independent of whatever client
    created the item.
    """
    notification_in = NotificationCreate(
        user_id=owner_id,
        message=f"Your item '{item_title}' was created.",
    )
    return create_notification(session=session, notification_in=notification_in)


def unread_count(*, session: Session, user_id: uuid.UUID) -> int:
    statement = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id)
        .where(col(Notification.is_read) == False)  # noqa: E712
    )
    return session.exec(statement).one()
