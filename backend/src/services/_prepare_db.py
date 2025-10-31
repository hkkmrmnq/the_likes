from getpass import getpass

from pandas import DataFrame, read_excel
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from src import crud, db
from src import models as md
from src.config import CFG
from src.logger import logger
from src.services.user_manager import FixedSQLAlchemyUserDatabase, UserManager


def check_file_data_consistency(
    *, all_sheets: dict[str, DataFrame]
) -> tuple[DataFrame, DataFrame, DataFrame]:
    attitudes_sheet = all_sheets['Attitudes']
    values_sheet = all_sheets['Values']
    aspects_sheet = all_sheets['Aspects']
    assert set(CFG.SUPPORTED_LANGUAGES) == set(values_sheet.columns), (
        'Settings.SUPPORTED_LANGUAGES does not match file languages.'
    )
    assert values_sheet.shape[0] == CFG.PERSONAL_VALUE_MAX_ORDER, (
        'CFG.PERSONAL_VALUE_MAX_ORDER does not match provided data.'
    )
    value_names = getattr(values_sheet, CFG.DEFAULT_LANGUAGE)
    aspect_values = getattr(aspects_sheet, f'value_{CFG.DEFAULT_LANGUAGE}')
    assert value_names.shape[0] == aspect_values.unique().shape[0], (
        'File Values list does not match file Aspects.'
    )
    for lan in CFG.SUPPORTED_LANGUAGES:
        assert not getattr(attitudes_sheet, lan).duplicated().any(), (
            f'Duplicates in file Attitudes {lan}.'
        )
        assert not getattr(values_sheet, lan).duplicated().any(), (
            f'Duplicates in {lan} file Values.'
        )
        assert (
            not getattr(aspects_sheet, f'statement_{lan}').duplicated().any()
        ), f'Duplicates in Aspects statement_{lan}.'
    for vname, group in aspects_sheet.groupby(f'value_{CFG.DEFAULT_LANGUAGE}'):
        for lan in CFG.SUPPORTED_LANGUAGES:
            key_phrases = group[f'key_phrase_{lan}']
            assert not key_phrases.duplicated().any(), (
                f'Duplicated {vname} key_phrase_{lan}.'
            )
    return attitudes_sheet, values_sheet, aspects_sheet


def read_basic_data_from_file(*, path: str = CFG.BASIC_DATA_PATH) -> dict:
    all_sheets = read_excel(path, sheet_name=None)
    attitudes_sheet, values_sheet, aspects_sheet = check_file_data_consistency(
        all_sheets=all_sheets
    )
    input_data = {}
    input_data['languages'] = sorted(values_sheet.columns.to_list())

    merged_df = aspects_sheet.merge(
        values_sheet,
        left_on=f'value_{CFG.DEFAULT_LANGUAGE}',
        right_on=CFG.DEFAULT_LANGUAGE,
        how='left',
    )
    definitions_data = {}
    for value_def_lan, group in merged_df.groupby(
        f'value_{CFG.DEFAULT_LANGUAGE}'
    ):
        value_data = {}
        aspects_data = {}
        for _, row in group.iterrows():
            aspect_data = {
                f'key_phrase_{CFG.DEFAULT_LANGUAGE}': row[
                    f'key_phrase_{CFG.DEFAULT_LANGUAGE}'
                ],
            }
            for lan in CFG.TRANSLATE_TO:
                aspect_data[f'statement_{lan}'] = row[f'statement_{lan}']
                aspect_data[f'key_phrase_{lan}'] = row[f'key_phrase_{lan}']
                value_data[lan] = row[lan]
            aspects_data[row[f'statement_{CFG.DEFAULT_LANGUAGE}']] = (
                aspect_data
            )
            value_data['aspects'] = aspects_data
        definitions_data[value_def_lan] = value_data
    attitudes_data = {}
    for row in attitudes_sheet.to_dict(orient='records'):
        translations = {}
        for lan in CFG.TRANSLATE_TO:
            translations[lan] = row[lan]
        attitudes_data[row[CFG.DEFAULT_LANGUAGE]] = translations
    return {'attitudes': attitudes_data, 'definitions': definitions_data}


async def clear_db(*, a_session_factory: async_sessionmaker) -> None:
    async with a_session_factory() as a_session:
        some_user = await crud.read_first_user(a_session=a_session)
        if some_user is not None:
            answer = 'dunno'
            while answer.lower() not in ('y', 'n'):
                answer = input(
                    'There are users in database. Delete everything? (y/n): '
                )
            if answer == 'n':
                return
        await crud.clear_db(a_session=a_session)
        await a_session.commit()
        logger.info('Database cleared.')


async def add_basic_data_to_db(
    *,
    input_data: dict,
    a_session_factory: async_sessionmaker,
) -> None:
    async with a_session_factory() as a_session:
        async with a_session.begin():
            await crud.create_attitudes(
                attitudes_data=input_data['attitudes'], a_session=a_session
            )
            await crud.create_definitions(
                definitions_data=input_data['definitions'], a_session=a_session
            )
            await a_session.flush()

            await crud.create_unique_values(a_session=a_session)
            await a_session.flush()

            await crud.create_attitude_translations(
                attitudes_data=input_data['attitudes'], a_session=a_session
            )
            await crud.create_definitions_translations(
                definitions_data=input_data['definitions'], a_session=a_session
            )
            await a_session.flush()

        logger.info('Basic data added to db.')


def compare_db_to_file_data(
    *,
    db_definitions: list[db.Value],
    db_attitudes: list[db.Attitude],
    db_u_v_s: list[db.UniqueValue],
    input_data: dict,
):
    assert len(db_attitudes) == len(input_data['attitudes']), (
        'Number of Attitudes in database does not match provided data.'
    )
    assert len(db_definitions) == len(input_data['definitions']), (
        'Number of Values in database does not match provided data.'
    )
    assert len(db_definitions) == CFG.PERSONAL_VALUE_MAX_ORDER, (
        'Number of Values in db does not match CFG.PERSONAL_VALUE_MAX_ORDER.'
    )
    db_aspects_number = sum([len(v.aspects) for v in db_definitions])
    input_aspects_number = 0
    for value in input_data['definitions']:
        input_aspects_number += len(
            input_data['definitions'][value]['aspects']
        )
    assert db_aspects_number == input_aspects_number, (
        f'{db_aspects_number} Aspects in database, '
        f'{input_aspects_number} Aspects in input data.'
    )
    count = 0
    for value_name in input_data['definitions']:
        count += 2 ** len(input_data['definitions'][value_name]['aspects'])
    assert len(db_u_v_s) == count, (
        'Number of UniqueValues in database does not match provided data.'
        f'UVs in DB: {len(db_u_v_s)}, expected from input: {count}'
    )
    logger.info('Data in DB matches input.')


@logger.catch
async def prepare_db(*, a_session_factory: async_sessionmaker):
    """
    Manages basic data needed for app t work:
    reads data from file, checks consistency;
    if no basic data in db - populates db,
    else - compares file data to db.
    """
    input_data = read_basic_data_from_file()
    async with a_session_factory() as a_session:
        definitions = await crud.read_definitions(a_session=a_session)
        attitudes = await crud.read_attitudes(a_session=a_session)
        u_v_s = await crud.read_unique_values(a_session=a_session)
    if all((not definitions, not attitudes, not u_v_s)):
        await add_basic_data_to_db(
            input_data=input_data, a_session_factory=a_session_factory
        )
    else:
        compare_db_to_file_data(
            db_definitions=definitions,
            db_attitudes=attitudes,
            db_u_v_s=u_v_s,
            input_data=input_data,
        )
    async with a_session_factory() as a_session:
        await crud.prepare_funcs_and_matviews(a_session=a_session)
        await a_session.commit()
    logger.info('DB prepared.')


async def add_superuser(*, a_session_factory: async_sessionmaker):
    email = input('Email: ')
    password1 = getpass('Password: ')
    password2 = getpass('Repeat password: ')
    assert password1 == password2, 'Typo in password?'
    async with a_session_factory() as session:
        user_db = FixedSQLAlchemyUserDatabase(session, db.User)
        user_manager = UserManager(user_db)
        user_data = md.UserCreate(
            email=email,
            password=password1,
            is_superuser=True,
            is_active=True,
            is_verified=True,
        )
        user = await user_manager.create(user_create=user_data, safe=False)
        session.add(user)
        await session.commit()
    logger.info('Superuser created.')
