from uuid import UUID

from sqlalchemy import func, not_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import constants as cnst
from .. import models as md
from .. import schemas as sch
from ..exceptions import exceptions as exc
from . import sql


async def check_recommendations(
    *,
    profile_id: int,
    distance_limit: int | None = None,
    limit: int = 20,
    session: AsyncSession,
) -> list[sch.RecomendationRead]:
    """
    Read 'recommendations' mat. view for a specific profile.
    Profile already in contacts are not included.
    """
    results = await session.execute(
        sql.read_recommendations_for_user,
        {
            'profile_id': profile_id,
            'distance_limit': distance_limit,
            'limit': limit,
        },
    )
    return [sch.RecomendationRead.model_validate(row) for row in results.all()]


async def read_contacts(
    *, me_user_id: UUID, status: str | None = None, session: AsyncSession
) -> sch.ContactsRead:
    """
    Read contacts of a particular user.
    status: optional, to filter by status.
    """
    query = (
        select(md.Contact)
        .options(joinedload(md.Contact.target_profile))
        .where(md.Contact.me_user_id == me_user_id)
    )
    if status is not None:
        query = query.where(md.Contact.status == status)
    results = await session.execute(query)
    contacts = list(results.scalars().all())
    schema = sch.ContactsRead(found=False)
    if len(contacts) == 0:
        return schema
    schema.found = True
    for contact in contacts:
        contact_data = {
            'name': contact.target_profile.name,
            'me_ready_to_start': contact.me_ready_to_start,
            'status': contact.status,
            'created_at': contact.created_at,
            'user_id': contact.target_user_id,
            'similarity_score': contact.similarity_score,
            'distance': contact.distance,
        }
        schema.contacts.append(sch.ContactRead.model_validate(contact_data))
    return schema


def create_contact_pair(
    me_profile: md.Profile,
    target_profile: md.Profile,
    recommendation: sch.RecomendationRead,
    session: AsyncSession,
) -> None:
    new_pair = [
        md.Contact(
            me_user_id=me_profile.user_id,
            target_user_id=target_profile.user_id,
            me_profile_id=me_profile.id,
            target_profile_id=target_profile.id,
            distance=recommendation.distance_meters,
            similarity_score=recommendation.similarity_score,
            status='awaits',
        ),
        md.Contact(
            me_user_id=target_profile.user_id,
            target_user_id=me_profile.user_id,
            me_profile_id=target_profile.id,
            target_profile_id=me_profile.id,
            distance=recommendation.distance_meters,
            similarity_score=recommendation.similarity_score,
            status='awaits',
        ),
    ]
    session.add_all(new_pair)


async def read_contact_pair(
    *,
    me_user_id: UUID,
    target_user_id: UUID,
    status: str | None = None,
    session: AsyncSession,
) -> tuple[md.Contact, md.Contact]:
    """
    If there is a contact pair with the given pair or user IDs,
    this contact pair will be returned - sender's first;
    otherwise - NotFound exception raised.
    status: optional - to filter by status.
    """
    query = select(md.Contact).where(
        (
            (
                (md.Contact.me_user_id == me_user_id)
                & (md.Contact.target_user_id == target_user_id)
            )
            | (
                (md.Contact.me_user_id == target_user_id)
                & (md.Contact.target_user_id == me_user_id)
            )
        )
    )
    if status is not None:
        query = query.where(md.Contact.status == status)
    results = await session.execute(query)
    pair = list(results.scalars().all())
    number_of_results = len(pair)
    if number_of_results == 2:
        if pair[0].me_user_id == me_user_id:
            return pair[0], pair[1]
        return pair[1], pair[0]
    if number_of_results == 0:
        raise exc.NotFound(
            (
                'Contact not found for:\n'
                f'{me_user_id},\n{target_user_id},\n{status=}.'
            )
        )
    all_found = [str((c.me_user_id, c.status, c.target_user_id)) for c in pair]
    raise exc.ServerError(
        (
            f'Expected a pair of conatcs - found {number_of_results}: '
            f'{"\n".join(all_found[:10])}'
        )
    )


# async def delete_contact_pair(
#     me_user_id: UUID,
#     target_user_id: UUID,
#     session: AsyncSession,
# ) -> None:
#     stmt = delete(md.Contact).where(
#         (md.Contact.me_user_id == me_user_id)
#         & (md.Contact.target_user_id == target_user_id)
#     )
#     await session.execute(stmt)


def create_message(
    *,
    sender_id: UUID,
    sender_profile_id: int,
    data: sch.MessageCreate,
    receiver_profile_id: int,
    session: AsyncSession,
):
    new_message = md.Message(
        sender_id=sender_id,
        sender_profile_id=sender_profile_id,
        receiver_id=data.receiver_id,
        receiver_profile_id=receiver_profile_id,
        content=data.content,
    )
    session.add(new_message)
    return new_message


async def count_uread_messages(
    user: md.User, session: AsyncSession
) -> sch.UnreadMessagesTotalCount:
    stmt = (
        select(md.Message.sender_id, func.count(md.Message.id).label('count'))
        .where(md.Message.receiver_id == user.id, not_(md.Message.is_read))
        .group_by(md.Message.sender_id)
    )

    results = await session.execute(stmt)
    data = sch.UnreadMessagesTotalCount(total=0, contacts=[])
    for row in results:
        sender_id, count = row
        data.total += count
        data.contacts.append(
            sch.ContactUnreadMessagesCount(sender_id=sender_id, number=count)
        )
    return data


async def get_messages(
    *,
    me_user: md.User,
    contact_user_id: UUID,
    limit: int | None = cnst.MESSAGES_HISTORY_LENGTH_DEFAULT,
    session: AsyncSession,
) -> list[sch.MessageRead]:
    await session.execute(
        update(md.Message)
        .where(
            md.Message.receiver_id == me_user.id,
            md.Message.sender_id == contact_user_id,
            not_(md.Message.is_read),
        )
        .values(is_read=True)  # TODO 1. transaction? 2. parts?
    )
    select_stmt = (
        select(md.Message)
        .options(
            joinedload(md.Message.sender_profile),
            joinedload(md.Message.receiver_profile),
        )
        .where(
            (
                (md.Message.sender_id == contact_user_id)
                & (md.Message.receiver_id == me_user.id)
            )
            | (
                (md.Message.sender_id == me_user.id)
                & (md.Message.receiver_id == contact_user_id)
            )
        )
        .order_by(md.Message.created_at.desc())
    )
    if limit is not None:
        select_stmt = select_stmt.limit(limit)
    results = await session.execute(select_stmt)
    schemas = []
    for msg in results.scalars():
        schemas.append(
            sch.MessageRead(
                id=msg.id,
                sender_id=msg.sender_id,
                sender_name=msg.sender_profile.name,
                receiver_id=msg.receiver_id,
                receiver_name=msg.receiver_profile.name,
                content=msg.content,
                created_at=msg.created_at,
            )
        )
    return schemas
