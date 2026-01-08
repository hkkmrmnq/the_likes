from uuid import UUID

from sqlalchemy import RowMapping, func, not_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload

from src.config import constants as CNST
from src.db.contact_n_message import Message
from src.db.user_and_profile import Profile, User


async def create_message(
    *,
    my_user_id: UUID,
    data: dict,
    asession: AsyncSession,
) -> Message:
    new_message = Message(
        sender_id=my_user_id,
        receiver_id=data['receiver_id'],
        text=data['text'],
    )
    asession.add(new_message)
    return new_message


async def read_message(
    *, sender_id: UUID, receiver_id: UUID, asession: AsyncSession
) -> Message | None:
    stmt = (
        select(Message)
        .options(
            joinedload(Message.sender).options(
                defer('*'),
                joinedload(User.profile).load_only(Profile.name),
            ),
            joinedload(Message.receiver).options(
                defer('*'),
                joinedload(User.profile).load_only(Profile.name),
            ),
        )
        .where(
            Message.sender_id == sender_id,
            Message.receiver_id == receiver_id,
        )
    )
    return await asession.scalar(stmt)


async def count_uread_messages(
    *, my_user_id: UUID, asession: AsyncSession
) -> list[RowMapping]:
    stmt = (
        select(Message.sender_id, func.count(Message.id).label('count'))
        .where(Message.receiver_id == my_user_id, not_(Message.is_read))
        .group_by(Message.sender_id)
    )

    results = await asession.execute(stmt)
    return list(results.mappings())


async def read_messages(
    *,
    my_user_id: UUID,
    other_user_id: UUID,
    limit: int | None = CNST.MESSAGES_HISTORY_LENGTH_DEFAULT,
    asession: AsyncSession,
) -> list[Message]:
    await asession.execute(
        update(Message)
        .where(
            Message.receiver_id == my_user_id,
            Message.sender_id == other_user_id,
            not_(Message.is_read),
        )
        .values(is_read=True)
    )
    select_stmt = (
        select(Message)
        .options(
            joinedload(Message.sender).options(
                defer('*'),
                joinedload(User.profile).load_only(Profile.name),
            ),
            joinedload(Message.receiver).options(
                defer('*'),
                joinedload(User.profile).load_only(Profile.name),
            ),
        )
        .where(
            (
                (Message.sender_id == other_user_id)
                & (Message.receiver_id == my_user_id)
            )
            | (
                (Message.sender_id == my_user_id)
                & (Message.receiver_id == other_user_id)
            )
        )
        .order_by(Message.created_at)
    )
    if limit is not None:
        select_stmt = select_stmt.limit(limit)
    results = await asession.execute(select_stmt)
    return list(results.scalars())
