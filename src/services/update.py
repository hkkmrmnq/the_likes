from sqlalchemy.ext.asyncio import AsyncSession

from .. import db
from .. import models as md
from . import _utils as utl
from . import contact as cnct
from . import message as msg
from .profile import get_profile


async def get_update(
    *, my_user: db.User, a_session: AsyncSession
) -> tuple[md.Update, str]:
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
