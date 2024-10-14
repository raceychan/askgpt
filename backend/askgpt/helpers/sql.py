import typing as ty
from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy import MetaData
from sqlalchemy import orm as sa_orm
from sqlalchemy.ext import asyncio as sa_aio
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import FromClause, func

from askgpt.helpers.string import str_to_snake


# Reference: https://docs.sqlalchemy.org/en/14/orm/declarative_mixins.html
def declarative(cls: type) -> type[DeclarativeBase]:
    """
    A more pythonic way to declare a sqlalchemy table
    """

    return sa_orm.declarative_base(cls=cls)


def async_engine(engine: sa.Engine) -> sa_aio.AsyncEngine:
    return sa_aio.AsyncEngine(engine)


def engine_factory(
    db_url: str,
    *,
    connect_args: dict[str, ty.Any] | None = None,
    echo: bool | ty.Literal["debug"] = False,
    hide_parameters: bool = False,
    pool_pre_ping: bool = True,
    pool_recycle: int = 3600,
    poolclass: type[sa.Pool] | None = None,
    execution_options: dict[str, ty.Any] | None = None,
    isolation_level: sa.engine.interfaces.IsolationLevel = "READ COMMITTED",
):
    extra: dict[str, ty.Any] = dict()

    if execution_options:
        extra.update(execution_options=execution_options)
    if connect_args:
        extra.update(connect_args=connect_args)

    engine = sa.create_engine(
        db_url,
        echo=echo,
        hide_parameters=hide_parameters,
        pool_pre_ping=pool_pre_ping,
        pool_recycle=pool_recycle,
        poolclass=poolclass,
        isolation_level=isolation_level,
        **extra,
    )
    return engine


@declarative
class TableBase:
    """
    Representation of actual tables in database,
    used for DDL and data migrations only
    """

    __table__: ty.ClassVar[FromClause]

    metadata: ty.ClassVar[MetaData]

    gmt_modified = sa.Column(
        "gmt_modified", sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    gmt_created = sa.Column("gmt_created", sa.DateTime, server_default=func.now())

    @sa_orm.declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return str_to_snake(cls.__name__)

    @classmethod
    def create_table(cls, engine: sa.Engine) -> None:
        cls.metadata.create_all(engine)

    @classmethod
    async def create_table_async(cls, async_engine: sa_aio.AsyncEngine) -> None:
        async with async_engine.begin() as conn:
            await conn.run_sync(cls.metadata.create_all)

    @classmethod
    def generate_tableclause(cls) -> sa.TableClause:
        clause = sa.table(
            cls.__tablename__,
            *[sa.column(c.name, c.type) for c in cls.__table__.columns],
        )
        return clause


class SQLDebugger:
    def __init__(self, engine: sa.Engine, echo: bool = True):
        from rich.console import Console

        self.engine = engine
        self.inspector = sa.inspect(engine)
        self._console = Console(color_system="truecolor")
        self._echo = echo

    def __str__(self):
        return f"{self.__class__.__name__}({self.engine.url})"

    def __call__(self, sql: str) -> list[dict[str, ty.Any]]:
        return self.execute(sql)

    @property
    def tables(self):
        return self.inspector.get_table_names()

    @property
    def console(self):
        return self._console

    def show_sql(self, sql: str) -> None:
        from rich.syntax import Syntax

        sql_ = Syntax(sql, "sql", theme="nord-darker", line_numbers=True)
        self._console.print(sql_)

    def show_result(
        self, cols: sa.engine.result.RMKeyView, result: list[dict[str, ty.Any]]
    ) -> None:
        from rich.style import Style
        from rich.table import Table

        table = Table(expand=True, show_lines=True)
        column_style = Style(color="green")

        for col in cols:
            table.add_column(col, style=column_style)

        for row in result:
            table.add_row(*[str(row[col]) for col in cols])

        self._console.print(table)

    def execute(self, sql: str) -> list[dict[str, ty.Any]]:
        with self.engine.begin() as conn:
            res = conn.execute(sa.text(sql))
            cols = res.keys()
            rows = res.all()

        results = [dict(row._mapping) for row in rows]  # type: ignore

        if self._echo:
            self.console.print(f"\n[bold green]success[/bold green]")
            self.show_result(cols, results)
        return results

    def interactive(self) -> None:
        while True:
            sql_caluse = input("sql> ")
            self.show_sql(sql_caluse)
            if sql_caluse == "exit":
                break
            self.execute(sql_caluse)

    def close(self) -> None:
        self.engine.dispose()
        self.console.print(f"\n[bold green]connection released[/]")

    def confirm(self, sql: str) -> bool:
        self.show_sql(sql)
        self.console.print("\n[bold red]Are you sure to execute? \\[yes/N][/]")
        return input() == "yes"

    @contextmanager
    def lifespan(self):
        try:
            yield self
        except KeyboardInterrupt:
            self.console.print(f"\n[bold red]canceled[/bold red]")
        finally:
            self.close()

    @classmethod
    def from_url(cls, db_url: str):
        engine = engine_factory(db_url, isolation_level="SERIALIZABLE", echo=True)
        return cls(engine)

    @classmethod
    def from_async_engine(cls, async_engine: sa_aio.AsyncEngine):
        url = str(async_engine.url).replace("+aiosqlite", "")
        return cls.from_url(url)


def parser():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("sql", nargs="?")
    parser.add_argument("-i", "--interactive", action="store_true")
    ns = parser.parse_args()
    return ns


def sqlcli():
    import os
    import sys

    ns = parser()
    if not ns.sql and not ns.interactive:
        print(f"sql or interactive mode required")
        sys.exit(0)

    url = os.environ["db_url"]

    engine = engine_factory(url)
    sqldbg = SQLDebugger(engine)
    with sqldbg.lifespan() as sqldbg:
        if ns.interactive:
            sqldbg.interactive()
            sys.exit(0)
        sql_query = ns.sql

        if sqldbg.confirm(sql_query):
            result = sqldbg.execute(sql_query)
            print(result)
        sys.exit(0)


if __name__ == "__main__":
    sqlcli()
