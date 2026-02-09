from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import db
from src import dependencies as dp
from src import schemas as sch
from src import services as srv
from src.config import CFG

router = APIRouter()


@router.get(
    CFG.PATHS.PRIVATE.RECOMMENDATIONS,
    responses=dp.with_common_responses(
        common_response_codes=[401],
        extra_responses_to_iclude={
            403: 'Temporarily unavailable.',
            # 404: ('Profile values have not yet been set.'),
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[list[sch.RecommendationRead]]:
    current_user, asession = user_and_asession
    results, message = await srv.check_for_alike(
        current_user=current_user, asession=asession
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    payload: sch.TargetUser,
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    current_user, asession = user_and_asession
    results, message = await srv.agree_to_start(
        current_user=current_user,
        other_user_id=payload.id,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


@router.get(
    '/active-contacts-and-requests',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def contacts(
    *,
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    current_user, asession = user_and_asession
    results, message = await srv.get_contacts_and_requests(
        current_user=current_user,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


@router.get(
    '/contacts-and-recommendations',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def contacts_and_recommendations(
    *,
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[sch.ContsNReqstsNRecoms]:
    current_user, asession = user_and_asession
    results, message = await srv.get_conts_n_reqsts_n_recoms(
        current_user=current_user,
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    target_user: sch.TargetUser,
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    current_user, asession = user_and_asession
    results, messgae = await srv.cancel_contact_request(
        current_user=current_user,
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    target_user: sch.TargetUser,
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    current_user, asession = user_and_asession
    result, message = await srv.reject_contact_request(
        current_user=current_user,
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    target_user: sch.TargetUser,
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    current_user, asession = user_and_asession
    results, message = await srv.block_contact(
        current_user=current_user,
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[list[sch.ContactRead]]:
    current_user, asession = user_and_asession
    results, message = await srv.get_rejected_requests(
        current_user=current_user,
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[list[sch.ContactRead]]:
    current_user, asession = user_and_asession
    results, message = await srv.get_cancelled_requests(
        current_user=current_user,
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[list[sch.ContactRead]]:
    current_user, asession = user_and_asession
    results, message = await srv.get_blocked_contacts(
        current_user=current_user,
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    target_user: sch.TargetUser,
) -> sch.ApiResponse[sch.ActiveContactsAndRequests]:
    current_user, asession = user_and_asession
    results, message = await srv.unblock_contact(
        current_user=current_user,
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
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    target_user: sch.TargetUser,
) -> sch.ApiResponse[sch.RecommendationRead]:
    current_user, asession = user_and_asession
    profile_model, message = await srv.get_other_profile(
        current_user=current_user,
        other_user_id=target_user.id,
        asession=asession,
    )
    return sch.ApiResponse(data=profile_model, message=message)


@router.get(
    '/contacts-options',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def get_additional_contacts_options(
    *,
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[sch.AdditionalContactsOptions]:
    current_user, asession = user_and_asession
    results, message = await srv.get_additional_contacts_options(
        current_user=current_user, asession=asession
    )
    return sch.ApiResponse(data=results, message=message)
