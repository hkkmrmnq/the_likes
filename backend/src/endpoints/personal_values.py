from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src import db
from src import dependencies as dp
from src import schemas as sch
from src import services as srv
from src.config import CFG

router = APIRouter()


@router.get(
    CFG.PATHS.PRIVATE.VALUES,
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def get_my_values(
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[sch.PersonalValuesRead]:
    current_user, asession = user_and_asession
    user_values, message = await srv.get_personal_values(
        current_user=current_user, asession=asession
    )
    return sch.ApiResponse(data=user_values, message=message)


@router.post(
    CFG.PATHS.PRIVATE.VALUES,
    status_code=status.HTTP_201_CREATED,
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={
            400: (
                'Inconsistent polarity/user_order. / '
                'Incorrect attitude_id. / '
                'Missing/extra values/aspects.'
            ),
            409: 'Personal values are already set.',
            500: (
                'Profile not found. / '
                'Personal values not found after creation.'
            ),
        },
    ),
)
async def post_my_values(
    *,
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    payload: sch.PersonalValuesCreateUpdate,
) -> sch.ApiResponse[sch.PersonalValuesRead]:
    current_user, asession = user_and_asession
    pv_read_model, message = await srv.create_personal_values(
        current_user=current_user, p_v_model=payload, asession=asession
    )
    return sch.ApiResponse(data=pv_read_model, message=message)


@router.put(
    CFG.PATHS.PRIVATE.VALUES,
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={
            400: (
                'Inconsistent polarity/user_order. / '
                'Incorrect attitude_id. / '
                'Missing/extra values/aspects.'
            ),
            404: 'Personal values have not yet been set.',
            500: (
                'Profile not found. / Personal values not found after update.'
            ),
        },
    ),
)
async def edit_my_values(
    *,
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    payload: sch.PersonalValuesCreateUpdate,
) -> sch.ApiResponse[sch.PersonalValuesRead]:
    current_user, asession = user_and_asession
    pv_read_model, message = await srv.update_personal_values(
        current_user=current_user, p_v_model=payload, asession=asession
    )
    return sch.ApiResponse(data=pv_read_model, message=message)
