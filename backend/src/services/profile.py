from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src import schemas as sch
from src.context import get_current_language
from src.db.user_and_profile import User
from src.services._utils import (
    personal_values_already_set,
    profile_model_to_write_data,
    profile_to_read_model,
)


async def get_profile(
    *,
    my_user: User,
    asession: AsyncSession,
) -> tuple[sch.ProfileRead, str]:
    """Gets Profile with user_id. Returns as ProfileRead."""
    profile = await crud.read_profile_by_user_id(
        user_id=my_user.id,
        user_language=get_current_language(),
        asession=asession,
    )
    return profile_to_read_model(profile), 'Profile.'


async def edit_profile(
    *,
    my_user: User,
    update_model: sch.ProfileUpdate,
    asession: AsyncSession,
) -> tuple[sch.ProfileRead, str]:
    """
    Updates ('my') Profile.
    Raises BadRequest if distance_limit set without location.
    """
    data = profile_model_to_write_data(update_model)
    await crud.update_profile(user_id=my_user.id, data=data, asession=asession)
    await asession.commit()
    profile = await crud.read_profile_by_user_id(
        user_id=my_user.id,
        user_language=get_current_language(),
        asession=asession,
    )
    message = 'Profile updated.'
    if profile.recommend_me and not await personal_values_already_set(
        my_user=my_user, asession=asession
    ):
        message += ' Personal Values not yet defined - choose them to proceed.'
    return profile_to_read_model(profile), message
