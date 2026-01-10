from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src import schemas as sch
from src.db.user_and_profile import User
from src.services import contact as contact_srv

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
) -> sch.ApiResponse[list[sch.RecommendationRead]]:
    results, message = await contact_srv.check_for_alike(
        my_user=my_user, asession=asession
    )
    return sch.ApiResponse(data=results, message=message)


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
    model: sch.TargetUser,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    results, message = await contact_srv.agree_to_start(
        my_user=my_user,
        other_user_id=model.id,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


@router.get(
    '/active-contacts-and-requests',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def contacts(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    results, message = await contact_srv.get_contacts_and_requests(
        my_user=my_user,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


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
    target_user: sch.TargetUser,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    results, messgae = await contact_srv.cancel_contact_request(
        my_user=my_user,
        other_user_id=target_user.id,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=messgae)


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
    target_user: sch.TargetUser,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    result, message = await contact_srv.reject_contact_request(
        my_user=my_user,
        other_user_id=target_user.id,
        asession=asession,
    )
    return sch.ApiResponse(data=result, message=message)


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
    target_user: sch.TargetUser,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    results, message = await contact_srv.block_contact(
        my_user=my_user,
        other_user_id=target_user.id,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


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
) -> sch.ApiResponse[list[sch.ContactRead]]:
    results, message = await contact_srv.get_rejected_requests(
        my_user=my_user,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


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
) -> sch.ApiResponse[list[sch.ContactRead]]:
    results, message = await contact_srv.get_cancelled_requests(
        my_user=my_user,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


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
) -> sch.ApiResponse[list[sch.ContactRead]]:
    results, message = await contact_srv.get_blocked_contacts(
        my_user=my_user,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


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
    target_user: sch.TargetUser,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    results, message = await contact_srv.unblock_contact(
        my_user=my_user,
        other_user_id=target_user.id,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


@router.get(
    '/other-profile/{user_id}',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={
            404: 'Requested user not found in contacts/recommendations.'
        },
    ),
)
async def get_contact_profile(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    user_id: UUID,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.RecommendationRead]:
    profile_model, message = await contact_srv.get_other_profile(
        my_user=my_user, other_user_id=user_id, asession=asession
    )
    return sch.ApiResponse(data=profile_model, message=message)
