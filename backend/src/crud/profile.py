from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, contains_eager

from src import schemas as sch
from src.config.config import CFG
from src.config.enums import SearchAllowedStatus
from src.crud import sql
from src.db.core import Attitude
from src.db.translations import AttitudeTranslation
from src.db.user_and_profile import Profile, UserDynamic
from src.exceptions.exceptions import ServerError


async def create_profile(
    *,
    user_id: UUID,
    asession: AsyncSession,
) -> None:
    asession.add(Profile(user_id=user_id))


async def read_profile_by_user_id(
    *,
    user_id: UUID,
    user_language: str = CFG.DEFAULT_LANGUAGE,
    asession: AsyncSession,
) -> Profile:
    stmt = (
        select(Profile)
        .outerjoin(Profile.attitude)
        .where(Profile.user_id == user_id)
    )
    if user_language in CFG.TRANSLATE_TO:
        stmt = (
            stmt.outerjoin(Attitude.translations)
            .where(
                (AttitudeTranslation.language_code == user_language)
                | (AttitudeTranslation.language_code.is_(None))
            )
            .where(
                (AttitudeTranslation.attitude_id == Attitude.id)
                | (Attitude.id.is_(None))
            )
            .options(
                contains_eager(Profile.attitude).contains_eager(
                    Attitude.translations
                )
            )
        )
    else:
        stmt = stmt.options(contains_eager(Profile.attitude))

    profile = await asession.scalar(stmt)
    if profile is None:
        raise ServerError(f'Profile not found for user_id {user_id}')
    return profile


async def update_profile(
    *,
    user_id: UUID,
    data: dict,
    asession: AsyncSession,
) -> None:
    stmt = update(Profile).where(Profile.user_id == user_id).values(**data)
    await asession.execute(stmt)


async def create_user_dynamic(
    *,
    user_id: UUID,
    search_allowed_status: str = SearchAllowedStatus.OK.value,
    asession: AsyncSession,
) -> None:
    asession.add(
        UserDynamic(
            user_id=user_id, search_allowed_status=search_allowed_status
        )
    )


async def read_user_dynamics(
    *,
    user_id: UUID,
    asession: AsyncSession,
) -> UserDynamic:
    ud = await asession.scalar(
        select(UserDynamic).where(UserDynamic.user_id == user_id)
    )
    if ud is None:
        raise ServerError('UserDynamic not found')
    return ud


async def reset_match_notifications_counter(
    *, user_id: UUID, asession: AsyncSession
) -> None:
    await asession.execute(
        update(UserDynamic)
        .where(UserDynamic.user_id == user_id)
        .values(match_notified=0)
    )


async def set_to_cooldown(*, user_ids: list[UUID], asession: AsyncSession):
    stmt = (
        update(UserDynamic)
        .where(UserDynamic.user_id.in_(user_ids))
        .values(
            search_allowed_status=SearchAllowedStatus.COOLDOWN,
            last_cooldown_start=datetime.now(),
        )
        .returning(UserDynamic)
    )
    return list(await asession.execute(stmt))


async def unsuspend(*, user_id: UUID, asession: AsyncSession):
    await asession.execute(
        update(UserDynamic)
        .where(UserDynamic.user_id == user_id)
        .where(
            UserDynamic.search_allowed_status
            == SearchAllowedStatus.SUSPENDED.value
        )
        .values({'search_allowed_status': SearchAllowedStatus.OK.value})
    )


def read_users_to_notify_of_match(
    *,
    ssession: Session,
) -> list[sch.UserToNotifyOfMatchRead]:
    results = ssession.execute(sql.users_to_notify_of_match)
    return [
        sch.UserToNotifyOfMatchRead(user_id=r.match_user_id, email=r.email)
        for r in results
    ]


def increment_match_notification_counters(
    *, users_ids: list[UUID], ssession: Session
):
    ssession.execute(
        update(UserDynamic)
        .where(UserDynamic.user_id.in_(users_ids))
        .values(match_notified=UserDynamic.match_notified + 1)
    )


def end_cooldowns(*, update_after: datetime, ssession: Session):
    ssession.execute(
        update(UserDynamic)
        .where(
            UserDynamic.search_allowed_status
            == SearchAllowedStatus.COOLDOWN.value
        )
        .where(UserDynamic.last_cooldown_start < update_after)
        .values({'search_allowed_status': SearchAllowedStatus.OK.value})
    )


def suspend(*, session: Session):
    session.execute(
        update(UserDynamic)
        .where(
            UserDynamic.match_notified
            > CFG.IGNORED_MATCH_NOTIFICATIONS_BEFORE_SUSPEND
        )
        .where(UserDynamic.search_allowed_status == SearchAllowedStatus.OK)
        .values(search_allowed_status=SearchAllowedStatus.SUSPENDED)
        .returning(UserDynamic.user_id)
    )
