from uuid import UUID

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import (
    Integer,
    Row,
    bindparam,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import db
from .. import exceptions as exc
from ..config import constants as CNST
from ..config.enums import ContactStatus
from . import sql


async def read_user_recommendations(
    *,
    my_user_id: UUID,
    other_user_id: UUID | None = None,
    limit: int | None = CNST.RECOMMENDATIONS_AT_A_TIME,
    a_session: AsyncSession,
) -> list[Row]:
    results = await a_session.execute(
        sql.read_user_recommendations.bindparams(
            bindparam('my_user_id', value=my_user_id, type_=SA_UUID),
            bindparam('other_user_id', value=other_user_id, type_=SA_UUID),
            bindparam('limit_param', value=limit, type_=Integer),
        )
    )
    recommendations = list(results.all())
    return recommendations


async def read_user_contacts(
    *,
    my_user_id: UUID | None = None,
    other_user_id: UUID | None = None,
    statuses: list[str] | None = None,
    a_session: AsyncSession,
) -> list[db.Contact]:
    """
    Read contacts with joined profiles.
    my_user_id: optional, to filter by my_user_id;
    other_user_id: optional, to filter by other_user_id;
    status: optional, to filter by status.
    """
    query = select(db.Contact).options(
        joinedload(db.Contact.other_user).joinedload(db.User.profile),
        joinedload(db.Contact.my_user).joinedload(db.User.profile),
    )
    if my_user_id is not None:
        query = query.where(db.Contact.my_user_id == my_user_id)
    if other_user_id is not None:
        query = query.where(db.Contact.other_user_id == other_user_id)
    if statuses is not None:
        query = query.where(db.Contact.status.in_(statuses))
    results = await a_session.execute(query)
    return list(results.scalars())


async def read_contact_pair(
    *,
    my_user_id: UUID,
    other_user_id: UUID,
    a_session: AsyncSession,
) -> list[db.Contact]:
    """
    Returns a pair of 'mirrored' contacts, 'my' first.
    Returns empty list if no contacts found.
    Exception raised if 1 or >2 contacts found.
    """
    query = (
        select(db.Contact)
        .options(
            joinedload(db.Contact.other_user).joinedload(db.User.profile),
            joinedload(db.Contact.my_user).joinedload(db.User.profile),
        )
        .where(
            (
                (db.Contact.my_user_id == my_user_id)
                & (db.Contact.other_user_id == other_user_id)
            )
            | (
                (db.Contact.my_user_id == other_user_id)
                & (db.Contact.other_user_id == my_user_id)
            )
        )
    )
    results = await a_session.execute(query)
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
    raise exc.ServerError(
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
    a_session: AsyncSession,
) -> tuple[list[db.Contact], bool]:
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
        insert(db.Contact)
        .values(contacts_data)
        .on_conflict_do_nothing(
            constraint=CNST.UNIQUE_CONTACT_MY_USER_ID_TARGET_USER_ID
        )
        .returning(db.Contact)
    )
    created = list((await a_session.execute(stmt)).scalars().all())
    contact_pair = await read_contact_pair(
        my_user_id=my_user_id,
        other_user_id=other_user_id,
        a_session=a_session,
    )
    total_created = len(created)
    if total_created == 0:
        return contact_pair, False
    elif total_created == 2:
        return contact_pair, True
    raise exc.ServerError(f'{total_created} instead of 2 contacts created.')


async def read_other_profile(
    *,
    my_user_id: UUID,
    other_user_id: UUID,
    a_session: AsyncSession,
) -> Row | None:
    """
    Compare current and other user's data
    by quereing Profile and moral_profiles materialized view.
    Returns user_id, name, similarity_score and distance_meters.
    """
    result = await a_session.execute(
        sql.read_contact_profile,
        {'my_user_id': my_user_id, 'other_user_id': other_user_id},
    )
    return result.one_or_none()
