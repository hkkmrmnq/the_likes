from sqlalchemy import delete, func, orm, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models as md
from .. import schemas as sch
from ..config import constants as CNST
from .core_n_profile import get_unique_value_id_by_vt_id_and_aspect_ids


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
    if lan_code != CNST.LANGUAGE_DEFAULT:
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


async def create_profile_value_links(
    profile: md.Profile,
    data: sch.ProfileValuesCreateUpdate,
    session: AsyncSession,
) -> list[md.ProfileValueLink]:
    new_value_links = []
    for vl_schema in data.value_links:
        new_value_link_model = md.ProfileValueLink(
            profile_id=profile.id,
            value_title_id=vl_schema.value_title_id,
            polarity=vl_schema.polarity,
            user_order=vl_schema.user_order,
        )
        new_aspect_link_models = []
        for aspect_schema in vl_schema.aspects:
            new_aspect_link_model = md.ProfileAspectLink(
                profile_id=profile.id,
                aspect_id=aspect_schema.aspect_id,
                included=aspect_schema.included,
            )
            new_aspect_link_models.append(new_aspect_link_model)
        new_value_link_model.profile_aspect_links = new_aspect_link_models
        new_value_link_model.unique_value_id = (
            await get_unique_value_id_by_vt_id_and_aspect_ids(
                vl_schema, session
            )
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
