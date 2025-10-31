from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src import models as md
from src import services as srv
from src.db import User
from src.services.user_manager import UserManager

router = APIRouter()


@router.get(
    '/check-for-alike',
    responses=dp.with_common_responses(
        common_response_codes=[401],
        extra_responses={
            403: {'description': 'Temporarily unavailable.'},
            404: {'description': ('Profile values have not yet been set.')},
            500: {
                'description': (
                    'Profile not found. / '
                    'Contact not found right after creation. / '
                    'To many contacts found.'
                )
            },
        },
    ),
)
async def check_for_alike(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[list[md.OtherProfileRead]]:
    results, message = await srv.check_for_alike(
        my_user=my_user, a_session=a_session
    )
    return md.ApiResponse(data=results, message=message)


@router.post(
    '/agree-to-start',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={404: {'description': 'Requested user not found.'}},
    ),
)
async def agree_to_start(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    model: md.TargetUser,
    user_manager: UserManager = Depends(dp.get_user_manager),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.ContactRead | None]:
    results, message = await srv.agree_to_start(
        my_user=my_user,
        other_user_id=model.id,
        user_manager=user_manager,
        a_session=a_session,
    )
    return md.ApiResponse(data=results, message=message)


@router.get(
    '/contact-requests',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def read_contact_requests(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.ContactRequestsRead | None]:
    results, message = await srv.get_contact_requests(
        my_user=my_user, a_session=a_session
    )
    return md.ApiResponse(data=results, message=message)


@router.get(
    '/contacts',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def contacts(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[list[md.ContactRead]]:
    results, message = await srv.get_ongoing_contacts(
        my_user=my_user,
        a_session=a_session,
    )
    return md.ApiResponse(data=results, message=message)


@router.post(
    '/cancel',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={404: {'description': 'Contact request not found.'}},
    ),
)
async def cancel_contact_request(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    target_user: md.TargetUser,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.ContactRequestsRead]:
    results, messgae = await srv.cancel_contact_request(
        my_user=my_user,
        other_user_id=target_user.id,
        a_session=a_session,
    )
    return md.ApiResponse(data=results, message=messgae)


@router.post(
    '/reject',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={404: {'description': 'Contact request not found.'}},
    ),
)
async def reject_contact_request(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    target_user: md.TargetUser,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.ContactRequestsRead | None]:
    result, message = await srv.reject_contact_request(
        my_user=my_user,
        other_user_id=target_user.id,
        a_session=a_session,
    )
    return md.ApiResponse(data=result, message=message)


@router.post(
    '/block',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={404: {'description': 'Contact not found.'}},
    ),
)
async def block_contact(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    target_user: md.TargetUser,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[list[md.ContactRead]]:
    results, message = await srv.block_contact(
        my_user=my_user,
        other_user_id=target_user.id,
        a_session=a_session,
    )
    return md.ApiResponse(data=results, message=message)


@router.get(
    '/rejected-requests',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def get_rejected_requests(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[list[md.ContactRead]]:
    results, message = await srv.get_rejected_requests(
        my_user=my_user,
        a_session=a_session,
    )
    return md.ApiResponse(data=results, message=message)


@router.get(
    '/cancelled-requests',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def get_cancelled_requests(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[list[md.ContactRead]]:
    results, message = await srv.get_cancelled_requests(
        my_user=my_user,
        a_session=a_session,
    )
    return md.ApiResponse(data=results, message=message)


@router.get(
    '/blocked-contacts',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
    ),
)
async def get_blocked_contacts(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[list[md.ContactRead]]:
    results, message = await srv.get_blocked_contacts(
        my_user=my_user,
        a_session=a_session,
    )
    return md.ApiResponse(data=results, message=message)


@router.post(
    '/unblock',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={404: {'description': 'Contact not found.'}},
    ),
)
async def unblock_contact(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    target_user: md.TargetUser,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[list[md.ContactRead]]:
    results, message = await srv.unblock_contact(
        my_user=my_user,
        other_user_id=target_user.id,
        a_session=a_session,
    )
    return md.ApiResponse(data=results, message=message)


@router.get(
    '/contact-profile/{user_id}',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={404: {'description': 'Contact not found.'}},
    ),
)
async def get_contact_profile(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    user_id: UUID,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.OtherProfileRead]:
    profile_model, message = await srv.get_contact_profile(
        my_user=my_user, other_user_id=user_id, a_session=a_session
    )
    return md.ApiResponse(data=profile_model, message=message)
