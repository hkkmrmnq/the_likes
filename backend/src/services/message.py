from datetime import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src import containers as cnt
from src import crud, db
from src import schemas as sch
from src.config.enums import ContactStatus
from src.exceptions import exc


async def count_unread_messages(
    *, current_user: db.User, asession: AsyncSession
) -> tuple[sch.UnreadMessagesCount, str]:
    """Counts unread messages."""
    results = await crud.count_uread_messages(
        my_user_id=current_user.id, asession=asession
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
    *, current_user_id: UUID, contact_user_id: UUID, asession: AsyncSession
) -> tuple[list[sch.MessageRead], str]:
    """
    Reads messages with the given user - both sent and received.
    Unread received messages are set to 'read'.
    """
    results = await crud.read_conversation_messages(
        sender_id=current_user_id,
        receiver_id=contact_user_id,
        asession=asession,
    )
    if not results:
        return [], 'No messages with this contact.'
    schemas = []
    for msg in results:
        time_full = msg.created_at.time()
        schemas.append(
            sch.MessageRead(
                sender_id=msg.sender_id,
                sender_name=msg.sender_name,
                receiver_id=msg.receiver_id,
                receiver_name=msg.receiver_name,
                text=msg.text,
                created_at=msg.created_at,
                time=time(time_full.hour, time_full.minute, time_full.second),
            )
        )
    await crud.mark_as_read(
        sender_id=contact_user_id,
        receiver_id=current_user_id,
        up_to=results[-1].created_at,
        asession=asession,
    )
    await asession.commit()
    return schemas, 'Messages found.'


async def add_message(
    *,
    current_user_id: UUID,
    data: cnt.MessageCreate,
    asession: AsyncSession,
) -> tuple[cnt.MessageRead, str]:
    """
    Add new message. Available only for active contacts.
    """
    if current_user_id != data.sender_id:
        raise exc.BadRequest(
            f'Current user id {current_user_id} does not match '
            f'message sender_id {data.sender_id}.'
        )
    contact = await crud.read_contacts(
        my_user_id=current_user_id,
        other_user_id=data.receiver_id,
        statuses=[ContactStatus.ONGOING],
        asession=asession,
    )
    if not contact:
        raise exc.NotFound(
            (
                f'Contact not found for my_user_id={current_user_id},'
                f' other_user_id={data.receiver_id}'
            )
        )
    await crud.create_message(data=data, asession=asession)
    await asession.commit()
    msg_cnt = await crud.read_last_message(
        sender_id=current_user_id,
        receiver_id=data.receiver_id,
        asession=asession,
    )
    if msg_cnt is None:
        raise exc.ServerError(
            (
                'Message not found after creation.'
                f'sender_id={current_user_id}, '
                f'receiver_id={data.receiver_id}.'
            )
        )
    return msg_cnt, 'Message added'
