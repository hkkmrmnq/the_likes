from sqlalchemy.ext.asyncio import AsyncSession

from src.db.user_and_profile import User
from src.models.update import FullUpdate, UpdateRead
from src.services import _utils as _utils
from src.services import contact as cnct
from src.services import message as msg
from src.services.profile import get_profile


async def get_update(
    *, my_user: User, asession: AsyncSession
) -> tuple[UpdateRead, str]:
    """
    Returns simple update as Update schema:
    recommendations, contact_requests and unread messsages counts.
    """
    recommendations = await _utils.get_recommendations(
        my_user_id=my_user.id, asession=asession
    )
    contact_requests, _ = await cnct.get_contact_requests(
        my_user=my_user, asession=asession
    )
    unread_msg_count, _ = await msg.count_unread_messages(
        my_user=my_user, asession=asession
    )
    return UpdateRead(
        recommendations=recommendations,
        contact_requests=contact_requests,
        unread_message_counts=unread_msg_count,
    ), 'This is basic update.'


async def get_full_update(
    *, my_user, asession: AsyncSession
) -> tuple[FullUpdate, str]:
    """
    Returns full update as FullUpdate schema:
    recommendations, contacts, contact_requests,
    unread messsages counts and ('my') profile.
    """
    recommendations = await _utils.get_recommendations(
        my_user_id=my_user.id, asession=asession
    )
    contacts, _ = await cnct.get_ongoing_contacts(
        my_user=my_user,
        asession=asession,
    )
    contact_requests, _ = await cnct.get_contact_requests(
        my_user=my_user, asession=asession
    )
    unread_msg_count, _ = await msg.count_unread_messages(
        my_user=my_user, asession=asession
    )
    profile, _ = await get_profile(my_user=my_user, asession=asession)
    return FullUpdate(
        recommendations=recommendations,
        contacts=contacts,
        contact_requests=contact_requests,
        unread_message_counts=unread_msg_count,
        my_profile=profile,
    ), 'This is full update.'
