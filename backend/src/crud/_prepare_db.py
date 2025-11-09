from itertools import combinations

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.config.config import CFG
from src.crud import sql
from src.crud.core import read_attitudes, read_definitions
from src.db.core import (
    Aspect,
    Attitude,
    UniqueValue,
    Value,
)
from src.db.personal_values import UniqueValueAspectLink
from src.db.translations import (
    AspectTranslation,
    AttitudeTranslation,
    ValueTranslation,
)
from src.db.user_and_profile import User
from src.exceptions.exceptions import ServerError


async def read_first_user(asession: AsyncSession):
    return await asession.scalar(select(User).limit(1))


async def clear_db(asession: AsyncSession) -> None:
    await asession.execute(delete(User))
    await asession.execute(delete(Value))
    await asession.execute(delete(Attitude))


async def create_attitudes(
    *,
    attitudes_data: dict,
    asession: AsyncSession,
) -> list[Attitude]:
    attitudes = [
        Attitude(statement_default=data_statement)
        for data_statement in attitudes_data
    ]
    asession.add_all(attitudes)
    return attitudes


async def create_definitions(
    definitions_data: dict, asession: AsyncSession
) -> list[Value]:
    definitions = []
    for value_name in definitions_data:
        db_value = Value(name_default=value_name)
        aspects_input_data = definitions_data[value_name]['aspects']
        for asp_stmt_dflt in aspects_input_data:
            db_aspect = Aspect(
                statement_default=asp_stmt_dflt,
                key_phrase_default=aspects_input_data[asp_stmt_dflt][
                    f'key_phrase_{CFG.DEFAULT_LANGUAGE}'
                ],
            )
            db_value.aspects.append(db_aspect)
        definitions.append(db_value)
    asession.add_all(definitions)
    return definitions


async def create_unique_values(
    asession: AsyncSession,
) -> list[UniqueValue]:
    definitions = await read_definitions(asession=asession)
    if not definitions:
        raise ServerError('Definitions not found.')
    unique_values = []
    for vt in definitions:
        aspect_ids = [s.id for s in vt.aspects]
        aspect_id_combinations = []
        for r in range(len(vt.aspects) + 1):
            aspect_id_combinations.extend(combinations(aspect_ids, r))
        for a_id_combination in aspect_id_combinations:
            new_uv = UniqueValue(
                value=vt,
                aspect_ids=a_id_combination,
            )
            new_uv.aspect_links = [
                UniqueValueAspectLink(unique_value=new_uv, aspect_id=a_id)
                for a_id in new_uv.aspect_ids
            ]
            unique_values.append(new_uv)
    asession.add_all(unique_values)
    return unique_values


async def create_attitude_translations(
    attitudes_data: dict, asession: AsyncSession
) -> list[AttitudeTranslation]:
    db_attitudes = await read_attitudes(asession=asession)
    translations = [
        AttitudeTranslation(
            attitude=db_attitude,
            language_code=lan,
            statement=attitudes_data[db_attitude.statement_default][lan],
        )
        for lan in CFG.TRANSLATE_TO
        for db_attitude in db_attitudes
    ]
    asession.add_all(translations)
    return translations


async def create_definitions_translations(
    definitions_data: dict,
    asession: AsyncSession,
) -> tuple[list[ValueTranslation], list[AspectTranslation]]:
    db_definitions = await read_definitions(asession=asession)
    value_translations = []
    aspect_translations = []
    for value in db_definitions:
        for lan in CFG.TRANSLATE_TO:
            translated_name = definitions_data[value.name_default][lan]
            value_translations.append(
                ValueTranslation(
                    value=value, language_code=lan, name=translated_name
                )
            )
            input_aspects = definitions_data[value.name_default]['aspects']
            for db_aspect in value.aspects:
                aspect_translations.append(
                    AspectTranslation(
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
    asession.add_all(value_translations)
    asession.add_all(aspect_translations)
    return value_translations, aspect_translations


async def prepare_funcs_and_matviews(asession: AsyncSession):
    for query in sql.prepare_funcs_and_matviews_commands:
        await asession.execute(text(query))
