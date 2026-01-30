from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src import schemas as sch
from src import services as srv
from src.config import ENM
from src.services.utils import other as other


async def bootstrap(
    *, my_user, asession: AsyncSession
) -> tuple[sch.Bootstrap, str]:
    """
    Returns UpdateRead schema:
    current user profile, contacts with unread messages counts,
    contacts requests, recommendations.
    """
    profile, _ = await srv.get_profile(current_user=my_user, asession=asession)
    recommendations = await other.get_recommendations(
        my_user_id=my_user.id, asession=asession
    )
    (
        active_contacts_and_requests,
        _,
    ) = await srv.get_contacts_and_requests(
        current_user=my_user,
        asession=asession,
    )
    filtered_recoms = []
    ud = await crud.read_user_dynamics(user_id=my_user.id, asession=asession)
    if ud.search_allowed_status != ENM.SearchAllowedStatus.COOLDOWN:
        contacts_user_ids = [
            req.user_id
            for req in [
                *active_contacts_and_requests.contact_requests,
                *active_contacts_and_requests.active_contacts,
            ]
        ]
        filtered_recoms = [
            rec
            for rec in recommendations
            if rec.user_id not in contacts_user_ids
        ]
    return sch.Bootstrap(
        profile=profile,
        active_contacts=active_contacts_and_requests.active_contacts,
        contact_requests=active_contacts_and_requests.contact_requests,
        recommendations=filtered_recoms,
    ), 'Bootstrap data.'
