import asyncio
from getpass import getpass
from itertools import combinations

import typer
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from pandas import DataFrame, Series, read_excel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from src import constants as cnst
from src import models as md
from src import schemas as sch
from src.config import get_settings
from src.services.user_manager import UserManager

DATABASE_URL = get_settings().database_url
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def _clear() -> None:
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(delete(md.User))
            await session.execute(delete(md.ValueTitle))
            await session.execute(delete(md.Attitude))


def _create_aspect_objects(
    value_title: md.ValueTitle, sheet: DataFrame
) -> list[md.Aspect]:
    aspects = []
    aspects_df = sheet[sheet.value_title == value_title.name_default]
    for row in aspects_df.itertuples():
        aspects.append(
            md.Aspect(
                value_title=value_title,
                key_phrase_default=row.key_phrase,
                statement_default=row.statement,
            )
        )
    return aspects


async def _create_value_objects(
    all_sheets: dict[str, DataFrame],
) -> list[md.ValueTitle]:
    value_titles_sheet = all_sheets['Values']
    aspects_sheet = all_sheets['Aspects']
    assert not value_titles_sheet.en.duplicated().any(), (
        'Duplicates in value names'
    )
    value_titles = [
        md.ValueTitle(name_default=name) for name in value_titles_sheet.en
    ]
    for vt in value_titles:
        vt.aspects = _create_aspect_objects(vt, aspects_sheet)
    return value_titles


async def _create_attitude_objects(
    statements: Series,
) -> list[md.Attitude]:
    attitudes = []
    for statement in statements:
        attitudes.append(md.Attitude(statement_default=statement))
    return attitudes


async def _create_unique_value_objects(
    value_titles: list[md.ValueTitle],
) -> tuple[list[md.UniqueValue], list[md.UniqueValueAspectLink]]:
    unique_values = []
    uv_aspect_links = []
    for vt in value_titles:
        aspect_ids = [s.id for s in vt.aspects]
        aspect_id_combinations = []
        for r in range(len(vt.aspects) + 1):
            aspect_id_combinations.extend(combinations(aspect_ids, r))
        for a_id_combination in aspect_id_combinations:
            new_uv = md.UniqueValue(
                value_title=vt,
                aspect_ids=a_id_combination,
            )
            uv_aspect_links += [
                md.UniqueValueAspectLink(unique_value=new_uv, aspect_id=a_id)
                for a_id in new_uv.aspect_ids
            ]
            unique_values.append(new_uv)
    return unique_values, uv_aspect_links


async def _create_value_translation_objects(
    sheet: DataFrame, lan_codes: list[str], session: AsyncSession
) -> list[md.ValueTitleTranslation]:
    for lan_code in lan_codes:
        translations = []
        result = await session.scalars(select(md.ValueTitle))
        vn_mapped = {vn.name: vn.id for vn in result.all()}
        for row in sheet.itertuples():
            name_en = getattr(row, cnst.LANGUAGE_DEFAULT)
            translation = md.ValueTitleTranslation(
                language_code=lan_code,
                name=getattr(row, lan_code),
                value_title_id=vn_mapped[name_en],
            )
            translations.append(translation)
    return translations


async def _create_aspect_translation_objects(
    sheet: DataFrame, lan_codes: list[str], session: AsyncSession
) -> list[md.AspectTranslation]:
    for lan_code in lan_codes:
        translations = []
        result = await session.scalars(select(md.Aspect))
        aspect_ids = {a.statement: a.id for a in result.all()}
        for row in sheet.itertuples():
            statement_en = getattr(row, 'statement')
            translation = md.AspectTranslation(
                language_code=lan_code,
                key_phrase=getattr(row, f'key_phrase_{lan_code}'),
                statement=getattr(row, f'statement_{lan_code}'),
                aspect_id=aspect_ids[statement_en],
            )
            translations.append(translation)
    return translations


async def _create_attitude_translation_objects(
    attitudes: list[md.Attitude], sheet: DataFrame, lan_codes: list[str]
) -> list[md.AspectTranslation]:
    translations = []
    attitude_ids = {a.statement: a.id for a in attitudes}
    for lan_code in lan_codes:
        for row in sheet.itertuples():
            statement_en = getattr(row, cnst.LANGUAGE_DEFAULT)
            translations.append(
                md.AttitudeTranslation(
                    attitude_id=attitude_ids[statement_en],
                    language_code=lan_code,
                    statement=getattr(row, f'{lan_code}'),
                )
            )
    return translations


# TODO check data consistency IncorrectBasicData
async def _add_data_to_db() -> None:
    all_sheets = read_excel(get_settings().basic_data_path, sheet_name=None)
    async with async_session_maker() as session:
        result = await session.scalar(select(md.ValueTitle).limit(1))
        assert result is None, (
            'Values table is not empty. To clear DB use `clear` command.'
        )
        values_names = await _create_value_objects(all_sheets)
        session.add_all(values_names)
        attitudes = await _create_attitude_objects(all_sheets['Attitudes'].en)
        session.add_all(attitudes)
        await session.commit()
        result = await session.scalars(
            select(md.ValueTitle).options(selectinload(md.ValueTitle.aspects))
        )
        values_names = list(result.all())
        uvs, uvsls = await _create_unique_value_objects(values_names)
        session.add_all(uvsls)
        session.add_all(uvs)
        lan_codes = [
            c for c in cnst.SUPPORTED_LANGUAGES if c != cnst.LANGUAGE_DEFAULT
        ]
        vn_translations = await _create_value_translation_objects(
            all_sheets['Values'], lan_codes, session
        )
        session.add_all(vn_translations)
        aspect_translations = await _create_aspect_translation_objects(
            all_sheets['Aspects'], lan_codes, session
        )
        session.add_all(aspect_translations)
        result = await session.scalars(select(md.Attitude))
        attitude_translations = await _create_attitude_translation_objects(
            list(result), all_sheets['Attitudes'], lan_codes
        )
        session.add_all(attitude_translations)
        await session.commit()
        print('Data added.')


async def _superuser():
    email = input('Email: ')
    password1 = getpass('Password: ')
    password2 = getpass('Repeat password: ')
    assert password1 == password2, 'Typo in password?'
    async with async_session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, md.User)
        user_manager = UserManager(user_db)
        user_data = sch.UserCreate(
            email=email,
            password=password1,
            is_superuser=True,
            is_active=True,
            is_verified=True,
        )
        user = await user_manager.create(user_create=user_data, safe=False)
        session.add(user)
        await session.commit()
    print('Superuser created.')


app = typer.Typer()


@app.command()
def clear():
    """Deletes Aspects, Values. Leaves Users."""
    asyncio.run(_clear())


@app.command()
def data():
    """
    Adds required data from 'Basic data.xlsx':
    Values, Aspects, Translations.
    """
    asyncio.run(_add_data_to_db())


@app.command()
def superuser():
    asyncio.run(_superuser())


if __name__ == '__main__':
    app()
