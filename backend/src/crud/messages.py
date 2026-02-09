from datetime import datetime, time
from uuid import UUID

from sqlalchemy import RowMapping, func, not_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload

from src import containers as cnt
from src import db
from src.config import CNST


async def create_message(
    *,
    data: cnt.MessageCreate,
    asession: AsyncSession,
) -> None:
    new_message = db.Message(
        sender_id=data.sender_id,
        receiver_id=data.receiver_id,
        text=data.text,
    )
    asession.add(new_message)


async def read_last_message(
    *, sender_id: UUID, receiver_id: UUID, asession: AsyncSession
) -> cnt.MessageRead | None:
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
        .order_by(db.Message.created_at.desc())
        .limit(1)
    )
    db_message = await asession.scalar(stmt)
    if db_message is None:
        return None
    return _db_messages_to_read_cnt([db_message])[0]


async def count_uread_messages(
    *, my_user_id: UUID, asession: AsyncSession
) -> list[RowMapping]:
    stmt = (
        select(db.Message.sender_id, func.count(db.Message.id).label('count'))
        .where(db.Message.receiver_id == my_user_id, not_(db.Message.is_read))
        .group_by(db.Message.sender_id)
    )

    results = await asession.execute(stmt)
    return list(results.mappings())


async def mark_as_read(
    *,
    sender_id: UUID | None = None,
    receiver_id: UUID,
    up_to: datetime,
    asession: AsyncSession,
) -> None:
    filter = [
        db.Message.receiver_id == receiver_id,
        not_(db.Message.is_read),
        db.Message.created_at <= up_to,
    ]
    if sender_id is not None:
        filter.append(db.Message.sender_id == sender_id)
    stmt = update(db.Message).where(*filter).values(is_read=True)
    await asession.execute(stmt)


async def read_conversation_messages(
    *,
    sender_id: UUID,
    receiver_id: UUID,
    limit: int | None = CNST.MESSAGES_HISTORY_LENGTH_DEFAULT,
    asession: AsyncSession,
) -> list[cnt.MessageRead]:
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
                (db.Message.sender_id == receiver_id)
                & (db.Message.receiver_id == sender_id)
            )
            | (
                (db.Message.sender_id == sender_id)
                & (db.Message.receiver_id == receiver_id)
            )
        )
        .order_by(db.Message.created_at.desc())
    )
    if limit is not None:
        select_stmt = select_stmt.limit(limit)
    results = await asession.execute(select_stmt)
    db_messages = list(results.scalars())
    db_messages.reverse()
    return _db_messages_to_read_cnt(db_messages)


async def read_all_unread_messages_to_user(
    *,
    receiver_id: UUID,
    limit: int | None = CNST.MESSAGES_HISTORY_LENGTH_DEFAULT,
    asession: AsyncSession,
) -> list[cnt.MessageRead]:
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
            (db.Message.receiver_id == receiver_id) & not_(db.Message.is_read)
        )
        .order_by(db.Message.created_at)
    )
    if limit is not None:
        select_stmt = select_stmt.limit(limit)
    results = await asession.execute(select_stmt)
    db_messages = list(results.scalars())
    return _db_messages_to_read_cnt(db_messages)


def _db_messages_to_read_cnt(
    db_messages: list[db.Message],
) -> list[cnt.MessageRead]:
    cnt_messages = []
    for db_msg in db_messages:
        time_full = db_msg.created_at.time()
        cnt_messages.append(
            cnt.MessageRead(
                sender_id=db_msg.sender_id,
                sender_name=db_msg.sender.profile.name,
                receiver_id=db_msg.receiver_id,
                receiver_name=db_msg.receiver.profile.name,
                text=db_msg.text,
                created_at=db_msg.created_at,
                time=time(time_full.hour, time_full.minute, time_full.second),
            )
        )
    return cnt_messages
