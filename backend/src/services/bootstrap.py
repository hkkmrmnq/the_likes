from sqlalchemy.ext.asyncio import AsyncSession

from src.models.bootstrap import Bootstrap
from src.services import _utils as _utils
from src.services import contact as srv_cnct
from src.services.profile import get_profile


async def bootstrap(
    *, my_user, asession: AsyncSession
) -> tuple[Bootstrap, str]:
    """
    Returns UpdateRead schema:
    current user profile, contacts with unread messages counts,
    contacts requests, recommendations.
    """
    profile, _ = await get_profile(my_user=my_user, asession=asession)
    recommendations = await _utils.get_recommendations(
        my_user_id=my_user.id, asession=asession
    )
    (
        contacts,
        contact_requests,
        _,
    ) = await srv_cnct.get_contacts_and_requests(
        my_user=my_user,
        asession=asession,
    )

    return Bootstrap(
        profile=profile,
        active_contacts=contacts,
        contact_requests=contact_requests,
        recommendations=recommendations,
    ), 'Bootstrap data.'
