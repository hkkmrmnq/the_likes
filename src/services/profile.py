from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, db
from .. import models as md
from ..exceptions import exceptions as exc
from ._utils import personal_values_already_set


async def get_profile(
    *,
    my_user: db.User,
    a_session: AsyncSession,
) -> tuple[md.ProfileRead, str]:
    profile = await crud.read_profile_by_user_id(
        user_id=my_user.id, a_session=a_session
    )
    return md.ProfileRead.model_validate(profile), 'found'


async def edit_profile(
    *,
    my_user: db.User,
    update_model: md.ProfileUpdate,
    a_session: AsyncSession,
) -> tuple[md.ProfileRead, str]:
    profile = await crud.read_profile_by_user_id(
        user_id=my_user.id, a_session=a_session
    )
    data = update_model.model_dump(exclude={'longitude', 'latitude'})
    if all(
        (
            'distance_limit' in data,
            'location' not in data,
            profile.location is None,
        )
    ):
        raise exc.BadRequest(
            'Location unset - it is required for distance_limit.'
        )
    await crud.update_profile(
        user_id=my_user.id, data=data, a_session=a_session
    )
    await a_session.commit()
    await a_session.refresh(profile)
    message = 'Profile updated.'
    if profile.recommend_me and not await personal_values_already_set(
        my_user=my_user, a_session=a_session
    ):
        message += ' Personal Values not yet defined - choose them to proceed.'
    return md.ProfileRead.model_validate(profile), message
