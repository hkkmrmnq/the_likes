from uuid import UUID

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import Integer, Row, bindparam, func, not_, select
from sqlalchemy.dialects.postgresql import ARRAY, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.config import constants as CNST
from src.config.config import CFG
from src.config.enums import ContactStatus, ContactStatusPG
from src.containers import RichContact
from src.crud import sql
from src.db.contact_n_message import Contact, Message
from src.db.user_and_profile import User
from src.exceptions.exceptions import ServerError


async def read_user_recommendations(
    *,
    my_user_id: UUID,
    other_user_id: UUID | None = None,
    limit: int | None = CFG.RECOMMENDATIONS_AT_A_TIME,
    asession: AsyncSession,
) -> list[Row]:
    results = await asession.execute(
        sql.read_user_recommendations.bindparams(
            bindparam('my_user_id', value=my_user_id, type_=SA_UUID),
            bindparam('other_user_id', value=other_user_id, type_=SA_UUID),
            bindparam('limit_param', value=limit, type_=Integer),
        )
    )
    recommendations = list(results.all())
    return recommendations


async def read_contacts(
    *,
    my_user_id: UUID | None = None,
    other_user_id: UUID | None = None,
    statuses: list[str] | None = None,
    asession: AsyncSession,
) -> list[tuple[Contact, int]]:
    """
    Read contacts with joined profiles and unread message counts.
    my_user_id: optional, to filter by my_user_id;
    other_user_id: optional, to filter by other_user_id;
    status: optional, to filter by status.
    Returns list of tuples of Contact and unread msg count integer.
    """
    unread_count_subquery = (
        select(
            Message.sender_id.label('other_user_id'),
            func.count(Message.id).label('unread_count'),
        )
        .where(Message.receiver_id == my_user_id, not_(Message.is_read))
        .group_by(Message.sender_id)
        .subquery()
    )

    query = (
        select(
            Contact,
            func.coalesce(unread_count_subquery.c.unread_count, 0).label(
                'unread_count'
            ),
        )
        .options(
            joinedload(Contact.other_user).joinedload(User.profile),
            joinedload(Contact.my_user).joinedload(User.profile),
        )
        .outerjoin(
            unread_count_subquery,
            unread_count_subquery.c.other_user_id == Contact.other_user_id,
        )
    )

    if my_user_id is not None:
        query = query.where(Contact.my_user_id == my_user_id)
    if other_user_id is not None:
        query = query.where(Contact.other_user_id == other_user_id)
    if statuses is not None:
        query = query.where(Contact.status.in_(statuses))

    results = await asession.execute(query)

    return [(row[0], int(row[1])) for row in results.all()]


async def read_contacts_rich(
    *,
    my_user_id: UUID | None = None,
    other_user_id: UUID | None = None,
    statuses: list[str] | None = None,
    asession: AsyncSession,
) -> list[RichContact]:
    results = await asession.execute(
        sql.read_contacts.bindparams(
            bindparam('my_user_id', value=my_user_id, type_=SA_UUID),
            bindparam('other_user_id', value=other_user_id, type_=SA_UUID),
            bindparam(
                'statuses', value=statuses, type_=ARRAY(ContactStatusPG)
            ),
        )
    )
    return [
        RichContact(
            my_user_id=r.my_user_id,
            other_user_id=r.other_user_id,
            my_name=r.my_profile_name,
            other_name=r.other_profile_name,
            status=r.status,
            distance=r.distance,
            similarity=r.similarity_score,
            unread_msg=r.unread_messages,
            created_at=r.created_at,
        )
        for r in results.all()
    ]


async def read_contact_pair(
    *,
    my_user_id: UUID,
    other_user_id: UUID,
    asession: AsyncSession,
) -> list[Contact]:
    """
    Returns a pair of 'mirrored' contacts, 'my' first.
    Returns empty list if no contacts found.
    Exception raised if 1 or >2 contacts found.
    """
    query = (
        select(Contact)
        .options(
            joinedload(Contact.other_user).joinedload(User.profile),
            joinedload(Contact.my_user).joinedload(User.profile),
        )
        .where(
            (
                (Contact.my_user_id == my_user_id)
                & (Contact.other_user_id == other_user_id)
            )
            | (
                (Contact.my_user_id == other_user_id)
                & (Contact.other_user_id == my_user_id)
            )
        )
    )
    results = await asession.execute(query)
    contacts = list(results.scalars().all())
    if not contacts:
        return []
    number_of_contacts = len(contacts)
    if number_of_contacts == 2:
        return (
            contacts
            if contacts[0].my_user_id == my_user_id
            else [contacts[1], contacts[0]]
        )
    raise ServerError(
        (
            'Inconsistent number of contacts found for '
            f'{my_user_id=}, {other_user_id=}.'
            f'Expectes a pair, found {number_of_contacts}.'
        )
    )


async def create_or_read_contact_pair(
    *,
    my_user_id: UUID,
    other_user_id: UUID,
    my_contact_status: str = ContactStatus.REQUESTED_BY_ME,
    other_user_contact_status: str = ContactStatus.REQUESTED_BY_OTHER,
    asession: AsyncSession,
) -> tuple[list[Contact], bool]:
    contacts_data = [
        {
            'my_user_id': my_user_id,
            'other_user_id': other_user_id,
            'status': my_contact_status,
        },
        {
            'my_user_id': other_user_id,
            'other_user_id': my_user_id,
            'status': other_user_contact_status,
        },
    ]
    stmt = (
        insert(Contact)
        .values(contacts_data)
        .on_conflict_do_nothing(
            constraint=CNST.UQ_CNSTR_CONTACT_MY_USER_ID_TARGET_USER_ID
        )
        .returning(Contact)
    )
    created = list((await asession.execute(stmt)).scalars().all())
    contact_pair = await read_contact_pair(
        my_user_id=my_user_id,
        other_user_id=other_user_id,
        asession=asession,
    )
    total_created = len(created)
    if total_created == 0:
        return contact_pair, False
    elif total_created == 2:
        return contact_pair, True
    raise ServerError(f'{total_created} instead of 2 contacts created.')


async def read_other_profile(
    *,
    my_user_id: UUID,
    other_user_id: UUID,
    asession: AsyncSession,
) -> Row | None:
    """
    Compare current and other user's data
    by quereing Profile and moral_profiles materialized view.
    Returns user_id, name, similarity and distance.
    """
    result = await asession.execute(
        sql.read_contact_profile,
        {'my_user_id': my_user_id, 'other_user_id': other_user_id},
    )
    return result.one_or_none()
