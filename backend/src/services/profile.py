from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.context import get_current_language
from src.db.user_and_profile import User
from src.exceptions import exceptions as exc
from src.models.user_and_profile import ProfileRead, ProfileUpdate
from src.services._utils import personal_values_already_set


async def get_profile(
    *,
    my_user: User,
    asession: AsyncSession,
) -> tuple[ProfileRead, str]:
    """Gets Profile with user_id. Returns as ProfileRead."""
    # user_language = get_current_language()
    profile = await crud.read_profile_by_user_id(
        user_id=my_user.id,
        user_language=get_current_language(),
        asession=asession,
    )
    return ProfileRead.model_validate(profile), 'found'


async def edit_profile(
    *,
    my_user: User,
    update_model: ProfileUpdate,
    asession: AsyncSession,
) -> tuple[ProfileRead, str]:
    """
    Updates ('my') Profile.
    Raises BadRequest if distance_limit set without location.
    """
    profile = await crud.read_profile_by_user_id(
        user_id=my_user.id,
        user_language=get_current_language(),
        asession=asession,
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
    await crud.update_profile(user_id=my_user.id, data=data, asession=asession)
    await asession.commit()
    await asession.refresh(profile)
    message = 'Profile updated.'
    if profile.recommend_me and not await personal_values_already_set(
        my_user=my_user, asession=asession
    ):
        message += ' Personal Values not yet defined - choose them to proceed.'
    return ProfileRead.model_validate(profile), message
