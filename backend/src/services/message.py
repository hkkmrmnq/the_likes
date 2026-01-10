from datetime import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src import schemas as sch
from src.config.enums import ContactStatus
from src.db.user_and_profile import User
from src.exceptions import exceptions as exc


async def count_unread_messages(
    *, my_user: User, asession: AsyncSession
) -> tuple[sch.UnreadMessagesCount, str]:
    """Counts unread messages."""
    results = await crud.count_uread_messages(
        my_user_id=my_user.id, asession=asession
    )
    combined = sch.UnreadMessagesCount(total=0, contacts=[])
    for result in results:
        combined.total += result['count']
        combined.contacts.append(
            sch.UnreadMessagesCountByContact.model_validate(result)
        )
    message = 'You have unread messages.' if results else 'No new messages.'
    return combined, message


async def read_messages(
    *, my_user: User, contact_user_id: UUID, asession: AsyncSession
) -> tuple[list[sch.MessageRead], str]:
    """
    Reads messages with the given user.
    Unread messages are set to 'read'.
    """
    results = await crud.read_messages(
        my_user_id=my_user.id,
        other_user_id=contact_user_id,
        asession=asession,
    )
    message = (
        'Messages found.' if results else 'No messages with this contact.'
    )
    models = []
    for msg in results:
        time_full = msg.created_at.time()
        models.append(
            sch.MessageRead(
                sender_id=msg.sender_id,
                sender_name=msg.sender.profile.name,
                receiver_id=msg.receiver_id,
                receiver_name=msg.receiver.profile.name,
                text=msg.text,
                created_at=msg.created_at,
                time=time(time_full.hour, time_full.minute, time_full.second),
            )
        )
    return models, message


async def send_message(
    *,
    my_user: User,
    create_model: sch.MessageCreate,
    asession: AsyncSession,
) -> tuple[sch.MessageRead, str]:
    """
    Sends message to contact.
    Available only for ongoing contacts.
    """
    contact = await crud.read_contacts(
        my_user_id=my_user.id,
        other_user_id=create_model.receiver_id,
        statuses=[ContactStatus.ONGOING],
        asession=asession,
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
        asession=asession,
    )
    await asession.commit()
    message = await crud.read_message(
        sender_id=my_user.id,
        receiver_id=create_model.receiver_id,
        asession=asession,
    )
    if message is None:
        raise exc.ServerError(
            (
                'Message not found after creation.'
                f'sender_id={my_user.id}, '
                f'receiver_id={create_model.receiver_id}.'
            )
        )
    time_full = message.created_at.time()
    return sch.MessageRead(
        sender_id=message.sender_id,
        sender_name=message.sender.profile.name,
        receiver_id=message.receiver_id,
        receiver_name=message.receiver.profile.name,
        text=message.text,
        created_at=message.created_at,
        time=time(time_full.hour, time_full.minute, time_full.second),
    ), 'Message sent.'
