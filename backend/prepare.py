import asyncio

import typer

from src import services as srv
from src.sessions import a_session_factory

app = typer.Typer()


@app.command()
def clear():
    """Deletes Aspects, Values. Leaves Users."""
    asyncio.run(srv.clear_db(a_session_factory=a_session_factory))


@app.command()
def data():
    """
    Adds required data from 'Basic data.xlsxx':
    Values, Aspects, Translations.
    """
    asyncio.run(srv.prepare_db(a_session_factory=a_session_factory))


@app.command()
def superuser():
    asyncio.run(srv.add_superuser(a_session_factory=a_session_factory))


if __name__ == '__main__':
    app()
