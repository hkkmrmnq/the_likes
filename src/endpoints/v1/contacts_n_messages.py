from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ... import dependencies as dp
from ... import schemas as sch
from ... import services as srv
from ...models import User

router = APIRouter()


@router.get(
    '/check_for_alike',
    response_model=sch.ContactsRead,
    responses=dp.with_common_responses(
        [401, 403],
        {
            404: {'description': 'Profile values have not yet been set.'},
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
    user: User = Depends(dp.current_user),
    lan_code: str = Depends(dp.get_language),
    session: AsyncSession = Depends(dp.get_db),
):
    return await srv.check_for_alike(user, lan_code, session)


@router.post(
    '/agree_to_start',
    response_model=sch.InfoMessage,
    responses=dp.with_common_responses(
        [401, 403],
        {
            404: {
                'description': (
                    'Contact not found. / '
                    'Inconsistent number of contacts found.'
                )
            }
        },
    ),
)
async def agree_to_start(
    *,
    user: User = Depends(dp.current_user),
    data: sch.AgreeSchema,
    session: AsyncSession = Depends(dp.get_db),
):
    msg = await srv.agree_to_start(user, data.user_id, session)
    return {'message': msg}


@router.get(
    '/contacts',
    response_model=sch.ContactsRead,
    responses=dp.with_common_responses([401, 403]),
)
async def contacts(
    user: User = Depends(dp.current_user),
    session: AsyncSession = Depends(dp.get_db),
):
    return await srv.get_contacts(user, session)


@router.get(
    '/messages/unread_count',
    response_model=sch.UnreadMessagesTotalCount,
    responses=dp.with_common_responses([401, 403]),
)
async def count_unread_messages(
    user: User = Depends(dp.current_user),
    session: AsyncSession = Depends(dp.get_db),
):
    return await srv.count_unread_messages(user=user, session=session)


@router.get(
    '/messages',
    response_model=list[sch.MessageRead],
    responses=dp.with_common_responses([401, 403]),
)
async def get_messages(
    *,
    me_user: User = Depends(dp.current_user),
    sender_id: UUID,
    session: AsyncSession = Depends(dp.get_db),
):
    return await srv.get_messages(me_user, sender_id, session)


@router.post(
    '/messages',
    response_model=sch.MessageCreate,
    responses=dp.with_common_responses(
        [401, 403],
        {
            404: {'description': 'Contact not found.'},
        },
    ),
)
async def send_message(
    *,
    sender: User = Depends(dp.current_user),
    data: sch.MessageCreate,
    session: AsyncSession = Depends(dp.get_db),
):
    return await srv.send_message(sender, data, session)
