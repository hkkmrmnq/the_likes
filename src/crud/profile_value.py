from sqlalchemy import delete, func, orm, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import constants as cnst
from .. import models as md
from .. import schemas as sch
from . import sql
from .core_n_profile import get_unique_value_id_by_aspect_ids


async def read_profile_value_links(
    profile: md.Profile, lan_code: str, session: AsyncSession
) -> sch.ProfileValuesRead:
    stmt = (
        select(md.ProfileValueLink)
        .join(md.ValueTitle)
        .outerjoin(md.ProfileAspectLink)
        .outerjoin(md.Aspect)
        .where(md.ProfileValueLink.profile_id == profile.id)
        .options(
            orm.joinedload(md.ProfileValueLink.value_title),
            orm.joinedload(
                md.ProfileValueLink.profile_aspect_links
            ).joinedload(md.ProfileAspectLink.aspect),
        )
    )
    if lan_code != cnst.LANGUAGE_DEFAULT:
        stmt = stmt.options(
            orm.joinedload(md.ProfileValueLink.value_title).joinedload(
                md.ValueTitle.translations
            ),
            orm.joinedload(md.ProfileValueLink.profile_aspect_links)
            .joinedload(md.ProfileAspectLink.aspect)
            .joinedload(md.Aspect.translations),
        )
    result = await session.scalars(stmt)
    profile_value_links = result.unique().all()
    for pvl in profile_value_links:
        setattr(pvl, 'value_title_name', pvl.value_title.name)
        setattr(pvl, 'aspects', pvl.profile_aspect_links)
        for usl in pvl.profile_aspect_links:
            setattr(usl, 'aspect_key_phrase', usl.aspect.key_phrase)
            setattr(usl, 'aspect_statement', usl.aspect.statement)

    return sch.ProfileValuesRead.model_validate(
        {
            'attitude_id': profile.attitude_id,
            'attitude_statement': profile.attitude.statement,
            'value_links': profile_value_links,
        }
    )


async def count_profile_value_links(
    profile: md.Profile, session: AsyncSession
) -> int:
    result = await session.scalar(
        select(func.count())
        .select_from(md.ProfileValueLink)
        .where(md.ProfileValueLink.profile_id == profile.id)
    )
    return result if result is not None else 0


async def count_pv_onelines(profile: md.Profile, session: AsyncSession) -> int:
    result = await session.scalar(
        select(func.count())
        .select_from(md.PVOneLine)
        .where(md.PVOneLine.profile_id == profile.id)
    )
    return result if result is not None else 0


async def create_profile_value_links(
    profile: md.Profile,
    data: sch.ProfileValuesCreateUpdate,
    session: AsyncSession,
) -> list[md.ProfileValueLink]:
    new_value_links = []
    for value_link_schema in data.value_links:
        new_value_link_model = md.ProfileValueLink(
            profile_id=profile.id,
            value_title_id=value_link_schema.value_title_id,
            polarity=value_link_schema.polarity,
            user_order=value_link_schema.user_order,
        )
        new_aspect_link_models = []
        for aspect_schema in value_link_schema.aspects:
            new_aspect_link_model = md.ProfileAspectLink(
                profile_id=profile.id,
                aspect_id=aspect_schema.aspect_id,
                included=aspect_schema.included,
            )
            new_aspect_link_models.append(new_aspect_link_model)
        new_value_link_model.profile_aspect_links = new_aspect_link_models
        aspect_ids = [
            s.aspect_id for s in value_link_schema.aspects if s.included
        ]
        new_value_link_model.unique_value_id = (
            await get_unique_value_id_by_aspect_ids(aspect_ids, session)
        )
        new_value_links.append(new_value_link_model)
    session.add_all(new_value_links)
    return new_value_links


async def delete_profile_value_links(
    profile: md.Profile,
    session: AsyncSession,
) -> None:
    await session.execute(
        delete(md.ProfileValueLink).where(
            md.ProfileValueLink.profile_id == profile.id
        )
    )


async def add_pv_oneline(
    *,
    attitude_id: int,
    distance_limit: int | None = None,
    profile_values_links: list[md.ProfileValueLink],
    session: AsyncSession,
) -> None:
    profile_values_links.sort(key=lambda x: x.user_order)
    att_n_best, good, neutral, bad, worst = [attitude_id], [], [], [], []
    for vl in profile_values_links:
        if vl.polarity == 'positive':
            if vl.user_order <= cnst.NUMBER_OF_BEST_UVS:
                att_n_best.append(vl.unique_value_id)
            else:
                good.append(vl.unique_value_id)
        elif vl.polarity == 'negative':
            if (
                vl.user_order
                > cnst.UNIQUE_VALUE_MAX_ORDER - cnst.NUMBER_OF_WORST_UVS
            ):
                worst.append(vl.unique_value_id)
            else:
                bad.append(vl.unique_value_id)
        else:
            neutral.append(vl.unique_value_id)
    session.add(
        md.PVOneLine(
            profile_id=profile_values_links[0].profile_id,
            attitude_id_and_best_uv_ids=att_n_best,
            distance_limit=distance_limit,
            neutral_uv_ids=neutral,
            good_uv_ids=good,
            worst_uv_ids=worst,
            bad_uv_ids=bad,
        )
    )


async def delete_pv_oneline(
    profile_id: int,
    session: AsyncSession,
) -> None:
    await session.execute(
        delete(md.PVOneLine).where(md.PVOneLine.profile_id == profile_id)
    )


async def recommendations_mat_view_exists(session: AsyncSession) -> bool:
    """Check if materialized view exists - returns True or False"""
    result = await session.execute(sql.recommendations_exists)
    return bool(result.scalar())


async def create_recommendations_mat_view(session: AsyncSession) -> None:
    await session.execute(sql.create_array_intersect_func)
    await session.execute(sql.create_array_jaccard_similarity_func)
    await session.execute(sql.create_recommendations_mat_view)
    await session.execute(sql.create_unique_idx_recommendations)
    await session.execute(sql.create_idx_recommendations_profile1)
    await session.execute(sql.create_idx_recommendations_profile2)
