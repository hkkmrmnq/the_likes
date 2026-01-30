import asyncio

import typer

from src.dependencies import asession_factory
from src.services import _prepare_db as prep_srv
from src.services.utils.other import generate_random_personal_values

app = typer.Typer()


@app.command()
def clear():
    """Deletes Aspects, Values. Leaves Users."""
    asyncio.run(prep_srv.clear_db())


@app.command()
def data():
    """
    Adds required data from 'Basic data.xlsxx':
    Values, Aspects, Translations.
    """
    asyncio.run(prep_srv.prepare_db())


@app.command()
def superuser():
    """Command to create superuser."""
    asyncio.run(prep_srv.add_superuser())


async def gen_randval_with_asession():
    async with asession_factory() as asession:
        await generate_random_personal_values(asession=asession)


@app.command()
def randval():
    """Command to display random personal values input."""
    asyncio.run(gen_randval_with_asession())


if __name__ == '__main__':
    app()
