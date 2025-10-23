from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, db
from .. import models as md
from ..config.enums import ContactStatus
from ..exceptions import exceptions as exc


async def count_unread_messages(
    *, my_user: db.User, a_session: AsyncSession
) -> tuple[md.UnreadMessagesCount, str]:
    results = await crud.count_uread_messages(
        my_user_id=my_user.id, a_session=a_session
    )
    combined = md.UnreadMessagesCount(total=0, contacts=[])
    for result in results:
        combined.total += result['count']
        combined.contacts.append(
            md.UnreadMessagesCountByContact.model_validate(result)
        )
    message = 'You have unread messages.' if results else 'No new messages.'
    return combined, message


async def get_messages(
    *, my_user: db.User, contact_user_id: UUID, a_session: AsyncSession
) -> tuple[list[md.MessageRead,], str]:
    results = await crud.read_messages(
        my_user_id=my_user.id,
        other_user_id=contact_user_id,
        a_session=a_session,
    )
    message = (
        'Messages found.' if results else 'No messages with this contact.'
    )
    await a_session.commit()
    return results, message


async def send_message(
    *,
    my_user: db.User,
    create_model: md.MessageCreate,
    a_session: AsyncSession,
) -> tuple[md.MessageRead, str]:
    contact = await crud.read_user_contacts(
        my_user_id=my_user.id,
        other_user_id=create_model.receiver_id,
        statuses=[ContactStatus.ONGOING],
        a_session=a_session,
    )
    if not contact:
        raise exc.NotFound(
            (
                f'Contact not found for my_user_id={my_user.id},'
                f' other_user_id={create_model.receiver_id}'
            )
        )
    await crud.create_message(
        my_user_id=my_user.id,
        data=create_model.model_dump(),
        a_session=a_session,
    )
    await a_session.commit()
    message = await crud.read_message(
        sender_id=my_user.id,
        receiver_id=create_model.receiver_id,
        a_session=a_session,
    )
    if message is None:
        raise exc.ServerError(
            (
                'Message not found after creation.'
                f'sender_id={my_user.id}, '
                f'receiver_id={create_model.receiver_id}.'
            )
        )
    return message, 'Message sent.'
