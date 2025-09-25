from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud
from .. import models as md
from .. import schemas as sch
from ..exceptions import exceptions as exc
from .core_n_profile import is_active_verified, read_profile
from .profile_value import profile_values_exist


async def find_me_awaiting_contact(
    me_user: md.User, session: AsyncSession
) -> sch.ContactsRead:
    """
    Returns ContactsRaed schema with 1 or 0 currently awaiting contact.
    If > 1 awaiting contacts found - error raized.
    Used in context of following a general policy,
    that allows a user to have only 1 currently awaiting contact.
    """
    contacts_schema = await crud.read_contacts(
        me_user_id=me_user.id, status='awaits', session=session
    )
    number_of_contacts = len(contacts_schema.contacts)
    if number_of_contacts < 2:
        return contacts_schema
    all_found = [
        str((me_user.id, c.status, c.user_id))  # type: ignore
        for c in contacts_schema.contacts
    ]
    raise exc.ServerError(
        (
            f"Found {number_of_contacts} contacts with status 'awaits': "
            f'{"\n".join(all_found[:10])}'
        )
    )


async def check_for_alike(
    me_user: md.User, lan_code: str, session: AsyncSession
) -> sch.ContactsRead:
    await is_active_verified(me_user)
    profile = await read_profile(me_user, lan_code, session)
    if not await profile_values_exist(profile, session):
        raise exc.NotFound('Profile values have not yet been set.')
    awaiting_contacts_schema = await find_me_awaiting_contact(me_user, session)
    if not awaiting_contacts_schema.found:
        new_recommendation = await crud.read_me_recommendation(
            profile,
            session,
        )
        if new_recommendation is None:
            return sch.ContactsRead(found=False)
        target_profile = await crud.read_profile_by_id(
            new_recommendation.similar_profile_id, session
        )
        await crud.create_contact_pair(
            profile, target_profile, new_recommendation, session
        )
        await session.commit()
        awaiting_contacts_schema = await find_me_awaiting_contact(
            me_user, session
        )
        if not awaiting_contacts_schema.found:
            raise exc.ServerError('Contact not found right after creation.')
    return awaiting_contacts_schema


async def agree_to_start(
    me_user: md.User, target_user_id: UUID, session: AsyncSession
) -> str:
    await is_active_verified(me_user)
    contact_pair = await crud.read_contact_pair(
        me_user_id=me_user.id,
        target_user_id=target_user_id,
        status='awaits',
        session=session,
    )
    contact_pair[0].me_ready_to_start = True
    if contact_pair[1].me_ready_to_start:
        contact_pair[0].status = contact_pair[1].status = 'ongoing'
        message = 'Emails sent'
    else:
        message = 'Readiness confirmed. Waiting for other user to confirm.'
    await session.commit()
    return message


async def send_message(
    sender: md.User, data: sch.MessageCreate, session: AsyncSession
) -> md.Message:
    await is_active_verified(sender)
    contact_pair = await crud.read_contact_pair(
        me_user_id=sender.id,
        target_user_id=data.receiver_id,
        status='ongoing',
        session=session,
    )
    new_message = await crud.create_message(
        sender_id=sender.id,
        sender_profile_id=contact_pair[0].me_profile_id,
        data=data,
        receiver_profile_id=contact_pair[0].target_profile_id,
        session=session,
    )
    await session.commit()
    await session.refresh(new_message)
    return new_message


async def count_unread_messages(
    *, user: md.User, session: AsyncSession
) -> sch.UnreadMessagesTotalCount:
    await is_active_verified(user)
    return await crud.count_uread_messages(user, session)


async def get_messages(
    me_user: md.User, sender_id: UUID, session: AsyncSession
) -> list[sch.MessageRead]:
    results = await crud.get_messages(
        me_user=me_user, contact_user_id=sender_id, session=session
    )
    results = results
    await session.commit()
    return results


async def get_contacts(
    user: md.User,
    session: AsyncSession,
) -> sch.ContactsRead:
    await is_active_verified(user)
    return await crud.read_contacts(
        me_user_id=user.id, status='ongoing', session=session
    )
