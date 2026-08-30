from uuid import UUID

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import bindparam, update
from sqlalchemy.dialects.postgresql import ARRAY, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src import containers as cnt
from src import crud, db
from src.config import ENM


async def read_user_recommendations(
    *,
    my_user_id: UUID,
    other_user_id: UUID | None = None,
    asession: AsyncSession,
) -> list[cnt.ContactBase]:
    results = await asession.execute(
        crud.sql.read_user_recommendations.bindparams(
            bindparam('my_user_id', value=my_user_id, type_=SA_UUID),
            bindparam('other_user_id', value=other_user_id, type_=SA_UUID),
        )
    )
    recommendations = [
        cnt.ContactBase(
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
) -> list[cnt.ContactRead]:
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
        cnt.ContactRead(
            user_id=r.other_user_id,
            name=r.other_profile_name,
            alias=r.alias,
            status=r.status,
            distance=r.distance,
            similarity=r.similarity,
            unread_messages=r.unread_messages,
            created_at=r.created_at,
        )
        for r in results.all()
    ]


async def update_contact_status(
    my_user_id: UUID,
    target_user_id: UUID,
    new_status: ENM.ContactStatus,
    asession: AsyncSession,
) -> None:
    await asession.execute(
        update(db.Contact)
        .where(db.Contact.my_user_id == my_user_id)
        .where(db.Contact.other_user_id == target_user_id)
        .values(status=new_status)
    )


async def update_contact_alias(
    my_user_id: UUID,
    target_user_id: UUID,
    new_alias: str | None,
    asession: AsyncSession,
) -> None:
    await asession.execute(
        update(db.Contact)
        .where(db.Contact.my_user_id == my_user_id)
        .where(db.Contact.other_user_id == target_user_id)
        .values(alias=new_alias)
    )
