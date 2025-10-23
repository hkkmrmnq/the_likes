from uuid import UUID

from sqlalchemy import RowMapping, func, not_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload

from .. import db
from .. import models as md
from ..config import constants as CNST


async def create_message(
    *,
    my_user_id: UUID,
    data: dict,
    a_session: AsyncSession,
) -> db.Message:
    new_message = db.Message(
        sender_id=my_user_id,
        receiver_id=data['receiver_id'],
        text=data['text'],
    )
    a_session.add(new_message)
    return new_message


async def read_message(
    *, sender_id: UUID, receiver_id: UUID, a_session: AsyncSession
) -> md.MessageRead | None:
    stmt = (
        select(db.Message)
        .options(
            joinedload(db.Message.sender).options(
                defer('*'),
                joinedload(db.User.profile).load_only(db.Profile.name),
            ),
            joinedload(db.Message.receiver).options(
                defer('*'),
                joinedload(db.User.profile).load_only(db.Profile.name),
            ),
        )
        .where(
            db.Message.sender_id == sender_id,
            db.Message.receiver_id == receiver_id,
        )
    )
    message = await a_session.scalar(stmt)
    return (
        md.MessageRead(
            sender_id=message.sender_id,
            sender_name=message.sender.profile.name,
            receiver_id=message.receiver_id,
            receiver_name=message.receiver.profile.name,
            text=message.text,
            created_at=message.created_at,
        )
        if message is not None
        else message
    )


async def count_uread_messages(
    *, my_user_id: UUID, a_session: AsyncSession
) -> list[RowMapping]:
    stmt = (
        select(db.Message.sender_id, func.count(db.Message.id).label('count'))
        .where(db.Message.receiver_id == my_user_id, not_(db.Message.is_read))
        .group_by(db.Message.sender_id)
    )

    results = await a_session.execute(stmt)
    return list(results.mappings())


async def read_messages(
    *,
    my_user_id: UUID,
    other_user_id: UUID,
    limit: int | None = CNST.MESSAGES_HISTORY_LENGTH_DEFAULT,
    a_session: AsyncSession,
) -> list[md.MessageRead]:
    await a_session.execute(
        update(db.Message)
        .where(
            db.Message.receiver_id == my_user_id,
            db.Message.sender_id == other_user_id,
            not_(db.Message.is_read),
        )
        .values(is_read=True)
    )
    select_stmt = (
        select(db.Message)
        .options(
            joinedload(db.Message.sender).options(
                defer('*'),
                joinedload(db.User.profile).load_only(db.Profile.name),
            ),
            joinedload(db.Message.receiver).options(
                defer('*'),
                joinedload(db.User.profile).load_only(db.Profile.name),
            ),
        )
        .where(
            (
                (db.Message.sender_id == other_user_id)
                & (db.Message.receiver_id == my_user_id)
            )
            | (
                (db.Message.sender_id == my_user_id)
                & (db.Message.receiver_id == other_user_id)
            )
        )
        .order_by(db.Message.created_at.desc())
    )
    if limit is not None:
        select_stmt = select_stmt.limit(limit)
    results = await a_session.execute(select_stmt)
    models = []
    for msg in results.scalars():
        models.append(
            md.MessageRead(
                sender_id=msg.sender_id,
                sender_name=msg.sender.profile.name,
                receiver_id=msg.receiver_id,
                receiver_name=msg.receiver.profile.name,
                text=msg.text,
                created_at=msg.created_at,
            )
        )
    return models
