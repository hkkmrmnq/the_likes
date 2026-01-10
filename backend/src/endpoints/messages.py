from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src import dependencies as dp
from src import schemas as sch
from src.db.user_and_profile import User
from src.services import message as msg_srv

router = APIRouter()


@router.get(
    '/messages/unread-count',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def count_unread_messages(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.UnreadMessagesCount]:
    result, message = await msg_srv.count_unread_messages(
        my_user=my_user, asession=asession
    )
    return sch.ApiResponse(data=result, message=message)


@router.get(
    '/messages',
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def get_messages(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    contact_user_id: UUID,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[list[sch.MessageRead]]:
    results, message = await msg_srv.read_messages(
        my_user=my_user, contact_user_id=contact_user_id, asession=asession
    )
    return sch.ApiResponse(data=results, message=message)


@router.post(
    '/messages',
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={
            404: 'Contact not found.',
        },
    ),
)
async def send_message(
    *,
    my_user: User = Depends(dp.current_active_verified_user),
    model: sch.MessageCreate,
    asession: AsyncSession = Depends(dp.get_async_session),
) -> sch.ApiResponse[sch.MessageRead]:
    result, message = await msg_srv.send_message(
        my_user=my_user, create_model=model, asession=asession
    )
    return sch.ApiResponse(data=result, message=message)
