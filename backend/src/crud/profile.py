from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, contains_eager

from src import db
from src import schemas as sch
from src.config import CFG, ENM
from src.crud import sql
from src.exceptions import exc


def create_profile(
    *,
    user: db.User,
    asession: AsyncSession,
) -> None:
    asession.add(db.Profile(user=user))


async def read_profile_by_user_id(
    *,
    user_id: UUID,
    user_language: str = CFG.DEFAULT_LANGUAGE,
    asession: AsyncSession,
) -> db.Profile:
    stmt = (
        select(db.Profile)
        .outerjoin(db.Profile.attitude)
        .where(db.Profile.user_id == user_id)
    )
    if user_language in CFG.TRANSLATE_TO:
        stmt = (
            stmt.outerjoin(db.Attitude.translations)
            .where(
                (db.AttitudeTranslation.language_code == user_language)
                | (db.AttitudeTranslation.language_code.is_(None))
            )
            .where(
                (db.AttitudeTranslation.attitude_id == db.Attitude.id)
                | (db.Attitude.id.is_(None))
            )
            .options(
                contains_eager(db.Profile.attitude).contains_eager(
                    db.Attitude.translations
                )
            )
        )
    else:
        stmt = stmt.options(contains_eager(db.Profile.attitude))

    profile = await asession.scalar(stmt)
    if profile is None:
        raise exc.ServerError(f'Profile not found for user_id {user_id}')
    return profile


async def update_profile(
    *,
    user_id: UUID,
    data: dict,
    asession: AsyncSession,
) -> None:
    stmt = (
        update(db.Profile).where(db.Profile.user_id == user_id).values(**data)
    )
    await asession.execute(stmt)


async def create_user_dynamic(
    *,
    user_id: UUID,
    search_allowed_status: str = ENM.SearchAllowedStatus.OK.value,
    asession: AsyncSession,
) -> None:
    asession.add(
        db.UserDynamic(
            user_id=user_id, search_allowed_status=search_allowed_status
        )
    )


async def read_user_dynamics(
    *,
    user_id: UUID,
    asession: AsyncSession,
) -> db.UserDynamic:
    ud = await asession.scalar(
        select(db.UserDynamic).where(db.UserDynamic.user_id == user_id)
    )
    if ud is None:
        raise exc.ServerError('UserDynamic not found')
    return ud


async def reset_match_notifications_counter(
    *, user_id: UUID, asession: AsyncSession
) -> None:
    await asession.execute(
        update(db.UserDynamic)
        .where(db.UserDynamic.user_id == user_id)
        .values(match_notified=0)
    )


async def set_to_cooldown(*, user_ids: list[UUID], asession: AsyncSession):
    stmt = (
        update(db.UserDynamic)
        .where(db.UserDynamic.user_id.in_(user_ids))
        .values(
            search_allowed_status=ENM.SearchAllowedStatus.COOLDOWN,
            last_cooldown_start=datetime.now(),
        )
        .returning(db.UserDynamic)
    )
    return list(await asession.execute(stmt))


async def unsuspend(*, user_id: UUID, asession: AsyncSession):
    await asession.execute(
        update(db.UserDynamic)
        .where(db.UserDynamic.user_id == user_id)
        .where(
            db.UserDynamic.search_allowed_status
            == ENM.SearchAllowedStatus.SUSPENDED.value
        )
        .values({'search_allowed_status': ENM.SearchAllowedStatus.OK.value})
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
        update(db.UserDynamic)
        .where(db.UserDynamic.user_id.in_(users_ids))
        .values(match_notified=db.UserDynamic.match_notified + 1)
    )


def end_cooldowns(*, update_after: datetime, ssession: Session):
    ssession.execute(
        update(db.UserDynamic)
        .where(
            db.UserDynamic.search_allowed_status
            == ENM.SearchAllowedStatus.COOLDOWN.value
        )
        .where(db.UserDynamic.last_cooldown_start < update_after)
        .values({'search_allowed_status': ENM.SearchAllowedStatus.OK.value})
    )


def suspend(*, session: Session):
    session.execute(
        update(db.UserDynamic)
        .where(
            db.UserDynamic.match_notified
            > CFG.IGNORED_MATCH_NOTIFICATIONS_BEFORE_SUSPEND
        )
        .where(
            db.UserDynamic.search_allowed_status == ENM.SearchAllowedStatus.OK
        )
        .values(search_allowed_status=ENM.SearchAllowedStatus.SUSPENDED)
        .returning(db.UserDynamic.user_id)
    )
