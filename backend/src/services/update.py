from sqlalchemy.ext.asyncio import AsyncSession

from src import db
from src import models as md
from src.services import _utils as utl
from src.services import contact as cnct
from src.services import message as msg
from src.services.profile import get_profile


async def get_update(
    *, my_user: db.User, a_session: AsyncSession
) -> tuple[md.Update, str]:
    """
    Returns simple update as Update schema:
    recommendations, contact_requests and unread messsages counts.
    """
    recommendations = await utl.get_recommendations(
        my_user_id=my_user.id, a_session=a_session
    )
    contact_requests, _ = await cnct.get_contact_requests(
        my_user=my_user, a_session=a_session
    )
    unread_msg_count, _ = await msg.count_unread_messages(
        my_user=my_user, a_session=a_session
    )
    return md.Update(
        recommendations=recommendations,
        contact_requests=contact_requests,
        unread_message_counts=unread_msg_count,
    ), 'This is basic update.'


async def get_full_update(
    *, my_user, a_session: AsyncSession
) -> tuple[md.FullUpdate, str]:
    """
    Returns full update as FullUpdate schema:
    recommendations, contacts, contact_requests,
    unread messsages counts and ('my') profile.
    """
    recommendations = await utl.get_recommendations(
        my_user_id=my_user.id, a_session=a_session
    )
    contacts, _ = await cnct.get_ongoing_contacts(
        my_user=my_user,
        a_session=a_session,
    )
    contact_requests, _ = await cnct.get_contact_requests(
        my_user=my_user, a_session=a_session
    )
    unread_msg_count, _ = await msg.count_unread_messages(
        my_user=my_user, a_session=a_session
    )
    profile, _ = await get_profile(my_user=my_user, a_session=a_session)
    return md.FullUpdate(
        recommendations=recommendations,
        contacts=contacts,
        contact_requests=contact_requests,
        unread_message_counts=unread_msg_count,
        my_profile=profile,
    ), 'This is full update.'
