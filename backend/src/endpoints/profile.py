from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import db
from src import dependencies as dp
from src import schemas as sch
from src import services as srv
from src.config import CFG

router = APIRouter()


@router.get(
    CFG.PATHS.PRIVATE.PROFILE,
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={500: 'Profile not found.'},
    ),
)
async def get_profile(
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[sch.ProfileRead]:
    current_user, asession = user_and_asession
    profile_model, message = await srv.get_profile(
        current_user=current_user, asession=asession
    )
    return sch.ApiResponse(data=profile_model, message=message)


@router.put(
    CFG.PATHS.PRIVATE.PROFILE,
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={
            400: "Can't set distance_limit without location.",
            500: 'Profile not found.',
        },
    ),
)
async def edit_profile(
    *,
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    payload: sch.ProfileUpdate,
) -> sch.ApiResponse[sch.ProfileRead]:
    current_user, asession = user_and_asession
    profile_model_read, message = await srv.edit_profile(
        current_user=current_user,
        update_model=payload,
        asession=asession,
    )
    return sch.ApiResponse(data=profile_model_read, message=message)
