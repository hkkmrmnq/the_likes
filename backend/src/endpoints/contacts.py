from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src.db.user_and_profile import User
from src.models.contact_n_message import (
    ContactRead,
    ContactRequestRead,
    OtherProfileRead,
    TargetUser,
)
from src.models.core import ApiResponse
from src.services import contact as contact_srv
from src.services.user_manager import UserManager

router = APIRouter()


@router.get(
    '/check-for-alike',
    responses=dp.with_common_responses(
        common_response_codes=[401],
        extra_responses_to_iclude={
            403: 'Temporarily unavailable.',
            404: ('Profile values have not yet been set.'),
            500: (
                'Profile not found. / '
                'Contact not found right after creation. / '
                'To many contacts found.'
            ),
        },
    ),
)
async def check_for_alike(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[OtherProfileRead]]:
    results, message = await contact_srv.check_for_alike(
        my_user=my_user, asession=asession
    )
    return ApiResponse(data=results, message=message)


@router.post(
    '/agree-to-start',
    responses=dp.with_common_responses(
        common_response_codes=[400, 401, 403],
        extra_responses_to_iclude={404: 'Requested user not found.'},
    ),
)
async def agree_to_start(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    model: TargetUser,
    user_manager: UserManager = Depends(dp.get_user_manager),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[ContactRead | None]:
    results, message = await contact_srv.agree_to_start(
        my_user=my_user,
        other_user_id=model.id,
        user_manager=user_manager,
        asession=asession,
    )
    return ApiResponse(data=results, message=message)


@router.get(
    '/contact-requests',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def read_contact_requests(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[ContactRequestRead] | None]:
    results, message = await contact_srv.get_contact_requests(
        my_user=my_user, asession=asession
    )
    return ApiResponse(data=results, message=message)


@router.get(
    '/contacts',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def contacts(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[ContactRead]]:
    results, message = await contact_srv.get_ongoing_contacts(
        my_user=my_user,
        asession=asession,
    )
    return ApiResponse(data=results, message=message)


@router.post(
    '/cancel',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={404: 'Contact request not found.'},
    ),
)
async def cancel_contact_request(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    target_user: TargetUser,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[ContactRequestRead]]:
    results, messgae = await contact_srv.cancel_contact_request(
        my_user=my_user,
        other_user_id=target_user.id,
        asession=asession,
    )
    return ApiResponse(data=results, message=messgae)


@router.post(
    '/reject',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={404: 'Contact request not found.'},
    ),
)
async def reject_contact_request(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    target_user: TargetUser,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[ContactRequestRead] | None]:
    result, message = await contact_srv.reject_contact_request(
        my_user=my_user,
        other_user_id=target_user.id,
        asession=asession,
    )
    return ApiResponse(data=result, message=message)


@router.post(
    '/block',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={404: 'Contact not found.'},
    ),
)
async def block_contact(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    target_user: TargetUser,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[ContactRead]]:
    results, message = await contact_srv.block_contact(
        my_user=my_user,
        other_user_id=target_user.id,
        asession=asession,
    )
    return ApiResponse(data=results, message=message)


@router.get(
    '/rejected-requests',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def get_rejected_requests(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[ContactRead]]:
    results, message = await contact_srv.get_rejected_requests(
        my_user=my_user,
        asession=asession,
    )
    return ApiResponse(data=results, message=message)


@router.get(
    '/cancelled-requests',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def get_cancelled_requests(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[ContactRead]]:
    results, message = await contact_srv.get_cancelled_requests(
        my_user=my_user,
        asession=asession,
    )
    return ApiResponse(data=results, message=message)


@router.get(
    '/blocked-contacts',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def get_blocked_contacts(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[ContactRead]]:
    results, message = await contact_srv.get_blocked_contacts(
        my_user=my_user,
        asession=asession,
    )
    return ApiResponse(data=results, message=message)


@router.post(
    '/unblock',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={404: 'Contact not found.'},
    ),
)
async def unblock_contact(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    target_user: TargetUser,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[list[ContactRead]]:
    results, message = await contact_srv.unblock_contact(
        my_user=my_user,
        other_user_id=target_user.id,
        asession=asession,
    )
    return ApiResponse(data=results, message=message)


@router.get(
    '/contact-profile/{user_id}',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={404: 'Contact not found.'},
    ),
)
async def get_contact_profile(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    user_id: UUID,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> ApiResponse[OtherProfileRead]:
    profile_model, message = await contact_srv.get_contact_profile(
        my_user=my_user, other_user_id=user_id, asession=asession
    )
    return ApiResponse(data=profile_model, message=message)
