from uuid import UUID

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import Integer, bindparam, update
from sqlalchemy.dialects.postgresql import ARRAY, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src import containers as cnt
from src import crud, db
from src.config import CFG, ENM


async def read_user_recommendations(
    *,
    my_user_id: UUID,
    other_user_id: UUID | None = None,
    limit: int | None = CFG.RECOMMENDATIONS_AT_A_TIME,
    asession: AsyncSession,
) -> list[cnt.ContactRead]:
    results = await asession.execute(
        crud.sql.read_user_recommendations.bindparams(
            bindparam('my_user_id', value=my_user_id, type_=SA_UUID),
            bindparam('other_user_id', value=other_user_id, type_=SA_UUID),
            bindparam('limit_param', value=limit, type_=Integer),
        )
    )
    recommendations = [
        cnt.ContactRead(
            user_id=r.user_id,
            name=r.name,
            similarity=r.similarity,
            distance=r.distance,
        )
        for r in list(results.all())
    ]
    return recommendations


async def create_contact_pair(
    *,
    my_user_id: UUID,
    other_user_id: UUID,
    my_contact_status: str,
    other_user_contact_status: str,
    asession: AsyncSession,
):
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
    stmt = insert(db.Contact).values(contacts_data)
    await asession.execute(stmt)


async def read_contacts(
    *,
    my_user_id: UUID | None = None,
    other_user_id: UUID | None = None,
    statuses: list[str] | None = None,
    asession: AsyncSession,
) -> list[cnt.RichContactRead]:
    """
    Reads contacts with added other user's profile data.
    my_user_id: optional, if only one subject ('me') needed;
    other_user_id: optional, if only one target (other user) needed;
    statuses: optional, if to filter by status.
    """
    results = await asession.execute(
        crud.sql.read_contacts.bindparams(
            bindparam('my_user_id', value=my_user_id, type_=SA_UUID),
            bindparam('other_user_id', value=other_user_id, type_=SA_UUID),
            bindparam(
                'statuses', value=statuses, type_=ARRAY(ENM.ContactStatusPG)
            ),
        )
    )
    return [
        cnt.RichContactRead(
            my_user_id=r.my_user_id,
            other_user_id=r.other_user_id,
            my_name=r.my_profile_name,
            other_name=r.other_profile_name,
            status=r.status,
            distance=r.distance,
            similarity=r.similarity,
            unread_msg=r.unread_messages,
            created_at=r.created_at,
        )
        for r in results.all()
    ]


async def update_contact(
    contact: cnt.ContactWrite, asession: AsyncSession
) -> None:
    await asession.execute(
        update(db.Contact)
        .where(db.Contact.my_user_id == contact.my_user_id)
        .where(db.Contact.other_user_id == contact.other_user_id)
        .values(status=contact.status)
        .returning(db.Contact)
    )


async def read_other_profile(
    *,
    my_user_id: UUID,
    other_user_id: UUID,
    asession: AsyncSession,
) -> cnt.ContactRead | None:
    """
    Compare current and other user's data
    by quereing Profile and moral_profiles materialized view.
    Returns user_id, name, similarity and distance.
    """
    result = await asession.execute(
        crud.sql.read_other_profile,
        {'my_user_id': my_user_id, 'other_user_id': other_user_id},
    )
    r = result.one_or_none()
    if r is None:
        return None
    return cnt.ContactRead(
        user_id=r.user_id,
        name=r.name,
        similarity=r.similarity,
        distance=r.distance,
    )
