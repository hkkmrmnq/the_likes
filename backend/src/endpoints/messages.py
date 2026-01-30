from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src import containers as cnt
from src import db
from src import dependencies as dp
from src import schemas as sch
from src import services as srv
from src.config import CFG

router = APIRouter()


@router.get(
    CFG.PATHS.PRIVATE.UNREAD_MESSAGES_COUNT,
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def count_unread_messages(
    *,
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
) -> sch.ApiResponse[sch.UnreadMessagesCount]:
    current_user, asession = user_and_asession
    result, message = await srv.count_unread_messages(
        current_user=current_user, asession=asession
    )
    return sch.ApiResponse(data=result, message=message)


@router.get(
    CFG.PATHS.PRIVATE.MESSAGES,
    responses=dp.with_common_responses(common_response_codes=[401, 403]),
)
async def get_messages(
    *,
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    contact_user_id: UUID,
) -> sch.ApiResponse[list[sch.MessageRead]]:
    current_user, asession = user_and_asession
    results, message = await srv.read_messages(
        current_user_id=current_user.id,
        contact_user_id=contact_user_id,
        asession=asession,
    )
    return sch.ApiResponse(data=results, message=message)


@router.post(
    CFG.PATHS.PRIVATE.MESSAGES,
    responses=dp.with_common_responses(
        common_response_codes=[401, 403],
        extra_responses_to_iclude={
            404: 'Contact not found.',
        },
    ),
)
async def send_message(
    *,
    user_and_asession: tuple[db.User, AsyncSession] = Depends(
        dp.get_current_active_and_virified_user_with_asession
    ),
    payload: sch.MessageCreate,
) -> sch.ApiResponse[sch.MessageRead]:
    current_user, asession = user_and_asession
    result, message = await srv.add_message(
        current_user_id=current_user.id,
        data=cnt.MessageCreate(
            sender_id=current_user.id,
            receiver_id=payload.receiver_id,
            text=payload.text,
            client_id=payload.client_id,
        ),
        asession=asession,
    )
    return sch.ApiResponse(
        data=sch.MessageRead.model_validate(result), message=message
    )
