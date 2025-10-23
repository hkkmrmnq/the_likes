from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, contains_eager

from src import db
from src import exceptions as exc
from src import models as md
from src.config import constants as CNST
from src.config.enums import SearchAllowedStatus
from src.context import get_current_language
from src.crud import sql


async def create_profile(
    *,
    user_id: UUID,
    a_session: AsyncSession,
) -> None:
    a_session.add(db.Profile(user_id=user_id))


async def read_profile_by_user_id(
    *,
    user_id: UUID,
    a_session: AsyncSession,
) -> db.Profile:
    user_language = get_current_language()

    stmt = (
        select(db.Profile)
        .join(db.Profile.attitude)
        .where(db.Profile.user_id == user_id)
    )

    if user_language == CNST.LANGUAGE_DEFAULT:
        stmt = stmt.options(contains_eager(db.Profile.attitude))
    else:
        stmt = (
            stmt.join(db.Attitude.translations)
            .options(
                contains_eager(db.Profile.attitude).contains_eager(
                    db.Attitude.translations
                )
            )
            .where(db.AttitudeTranslation.language_code == user_language)
        )
    profile = await a_session.scalar(stmt)
    if profile is None:
        raise exc.ServerError(f'Profile not found for user_id {user_id}')
    return profile


async def update_profile(
    *,
    user_id: UUID,
    data: dict,
    a_session: AsyncSession,
) -> None:
    stmt = (
        update(db.Profile).where(db.Profile.user_id == user_id).values(**data)
    )
    await a_session.execute(stmt)


async def create_user_dynamic(
    *,
    user_id: UUID,
    search_allowed_status: str = SearchAllowedStatus.OK.value,
    a_session: AsyncSession,
) -> None:
    a_session.add(
        db.UserDynamic(
            user_id=user_id, search_allowed_status=search_allowed_status
        )
    )


async def read_user_dynamics(
    *,
    user_id: UUID,
    a_session: AsyncSession,
) -> db.UserDynamic:
    ud = await a_session.scalar(
        select(db.UserDynamic).where(db.UserDynamic.user_id == user_id)
    )
    if ud is None:
        raise exc.ServerError('UserDynamic not found')
    return ud


async def reset_match_notifications_counter(
    *, user_id: UUID, a_session: AsyncSession
) -> None:
    await a_session.execute(
        update(db.UserDynamic)
        .where(db.UserDynamic.user_id == user_id)
        .values(match_notified=0)
    )


async def set_to_cooldown(*, user_ids: list[UUID], a_session: AsyncSession):
    stmt = (
        update(db.UserDynamic)
        .where(db.UserDynamic.user_id.in_(user_ids))
        .values(
            search_allowed_status=SearchAllowedStatus.COOLDOWN,
            last_cooldown_start=datetime.now(),
        )
        .returning(db.UserDynamic)
    )
    return list(await a_session.execute(stmt))


async def unsuspend(*, user_id: UUID, a_session: AsyncSession):
    await a_session.execute(
        update(db.UserDynamic)
        .where(db.UserDynamic.user_id == user_id)
        .where(
            db.UserDynamic.search_allowed_status
            == SearchAllowedStatus.SUSPENDED.value
        )
        .values({'search_allowed_status': SearchAllowedStatus.OK.value})
    )


def read_users_to_notify_of_match(
    *,
    s_session: Session,
) -> list[md.UserToNotifyOfMatchRead]:
    results = s_session.execute(sql.users_to_notify_of_match)
    return [
        md.UserToNotifyOfMatchRead(user_id=r.match_user_id, email=r.email)
        for r in results
    ]


def update_match_notification_counters(
    *, users_ids: list[UUID], s_session: Session
):
    s_session.execute(
        update(db.UserDynamic)
        .where(db.UserDynamic.user_id.in_(users_ids))
        .values(match_notified=db.UserDynamic.match_notified + 1)
    )


def end_cooldowns(*, update_after: datetime, s_session: Session):
    s_session.execute(
        update(db.UserDynamic)
        .where(
            db.UserDynamic.search_allowed_status
            == SearchAllowedStatus.COOLDOWN.value
        )
        .where(db.UserDynamic.last_cooldown_start < update_after)
        .values({'search_allowed_status': SearchAllowedStatus.OK.value})
    )


def suspend(*, s_session: Session):
    s_session.execute(
        update(db.UserDynamic)
        .where(
            db.UserDynamic.match_notified
            > CNST.IGNORED_MATCH_NOTIFICATIONS_BEFORE_SUSPEND
        )
        .where(db.UserDynamic.search_allowed_status == SearchAllowedStatus.OK)
        .values(search_allowed_status=SearchAllowedStatus.SUSPENDED)
        .returning(db.UserDynamic.user_id)
    )
