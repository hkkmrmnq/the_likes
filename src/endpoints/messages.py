from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .. import dependencies as dp
from .. import models as md
from .. import services as srv
from ..db import User

router = APIRouter()


@router.get(
    '/messages/unread-count',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def count_unread_messages(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.UnreadMessagesCount]:
    result, message = await srv.count_unread_messages(
        my_user=my_user, a_session=a_session
    )
    return md.ApiResponse(data=result, message=message)


@router.get(
    '/messages',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def get_messages(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    contact_user_id: UUID,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[list[md.MessageRead]]:
    results, message = await srv.get_messages(
        my_user=my_user, contact_user_id=contact_user_id, a_session=a_session
    )
    return md.ApiResponse(data=results, message=message)


@router.post(
    '/messages',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses={
            404: {'description': 'Contact not found.'},
        },
    ),
)
async def send_message(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    model: md.MessageCreate,
    a_session: AsyncSession = Depends(dp.get_async_session),
) -> md.ApiResponse[md.MessageRead]:
    result, message = await srv.send_message(
        my_user=my_user, create_model=model, a_session=a_session
    )
    return md.ApiResponse(data=result, message=message)
