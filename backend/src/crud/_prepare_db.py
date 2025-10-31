from itertools import combinations

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio.session import AsyncSession

from src import db
from src import exceptions as exc
from src.config import CFG
from src.crud import sql
from src.crud.core import read_attitudes, read_definitions


async def read_first_user(a_session: AsyncSession):
    return await a_session.scalar(select(db.User).limit(1))


async def clear_db(a_session: AsyncSession) -> None:
    await a_session.execute(delete(db.User))
    await a_session.execute(delete(db.Value))
    await a_session.execute(delete(db.Attitude))


async def create_attitudes(
    *,
    attitudes_data: dict,
    a_session: AsyncSession,
) -> list[db.Attitude]:
    attitudes = [
        db.Attitude(statement_default=data_statement)
        for data_statement in attitudes_data
    ]
    a_session.add_all(attitudes)
    return attitudes


async def create_definitions(
    definitions_data: dict, a_session: AsyncSession
) -> list[db.Value]:
    definitions = []
    for value_name in definitions_data:
        db_value = db.Value(name_default=value_name)
        aspects_input_data = definitions_data[value_name]['aspects']
        for asp_stmt_dflt in aspects_input_data:
            db_aspect = db.Aspect(
                statement_default=asp_stmt_dflt,
                key_phrase_default=aspects_input_data[asp_stmt_dflt][
                    f'key_phrase_{CFG.DEFAULT_LANGUAGE}'
                ],
            )
            db_value.aspects.append(db_aspect)
        definitions.append(db_value)
    a_session.add_all(definitions)
    return definitions


async def create_unique_values(
    a_session: AsyncSession,
) -> list[db.UniqueValue]:
    definitions = await read_definitions(a_session=a_session)
    if not definitions:
        raise exc.ServerError('Definitions not found.')
    unique_values = []
    for vt in definitions:
        aspect_ids = [s.id for s in vt.aspects]
        aspect_id_combinations = []
        for r in range(len(vt.aspects) + 1):
            aspect_id_combinations.extend(combinations(aspect_ids, r))
        for a_id_combination in aspect_id_combinations:
            new_uv = db.UniqueValue(
                value=vt,
                aspect_ids=a_id_combination,
            )
            new_uv.aspect_links = [
                db.UniqueValueAspectLink(unique_value=new_uv, aspect_id=a_id)
                for a_id in new_uv.aspect_ids
            ]
            unique_values.append(new_uv)
    a_session.add_all(unique_values)
    return unique_values


async def create_attitude_translations(
    attitudes_data: dict, a_session: AsyncSession
) -> list[db.AttitudeTranslation]:
    db_attitudes = await read_attitudes(a_session=a_session)
    translations = [
        db.AttitudeTranslation(
            attitude=db_attitude,
            language_code=lan,
            statement=attitudes_data[db_attitude.statement_default][lan],
        )
        for lan in CFG.TRANSLATE_TO
        for db_attitude in db_attitudes
    ]
    a_session.add_all(translations)
    return translations


async def create_definitions_translations(
    definitions_data: dict,
    a_session: AsyncSession,
) -> tuple[list[db.ValueTranslation], list[db.AspectTranslation]]:
    db_definitions = await read_definitions(a_session=a_session)
    value_translations = []
    aspect_translations = []
    for value in db_definitions:
        for lan in CFG.TRANSLATE_TO:
            translated_name = definitions_data[value.name_default][lan]
            value_translations.append(
                db.ValueTranslation(
                    value=value, language_code=lan, name=translated_name
                )
            )
            input_aspects = definitions_data[value.name_default]['aspects']
            for db_aspect in value.aspects:
                aspect_translations.append(
                    db.AspectTranslation(
                        aspect=db_aspect,
                        language_code=lan,
                        key_phrase=input_aspects[db_aspect.statement_default][
                            f'key_phrase_{lan}'
                        ],
                        statement=input_aspects[db_aspect.statement_default][
                            f'statement_{lan}'
                        ],
                    )
                )
    a_session.add_all(value_translations)
    a_session.add_all(aspect_translations)
    return value_translations, aspect_translations


async def prepare_funcs_and_matviews(a_session: AsyncSession):
    for query in sql.prepare_funcs_and_matviews_commands:
        await a_session.execute(text(query))
