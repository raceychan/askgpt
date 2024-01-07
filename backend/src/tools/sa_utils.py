import typing as ty
from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio


def asyncengine(engine: sa.Engine) -> sa_aio.AsyncEngine:
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
    extra = dict()

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


def sqlcli():
    import sys
    from argparse import ArgumentParser

    from src.domain.config import get_setting
    from src.infra.factory import get_sqldbg

    parser = ArgumentParser()
    parser.add_argument("sql", nargs="?")
    parser.add_argument("-i", "--interactive", action="store_true")
    ns = parser.parse_args()
    if not ns.sql and not ns.interactive:
        print(f"sql or interactive mode required")
        sys.exit(0)

    sql = get_sqldbg(get_setting())
    with sql.lifespan() as sql:
        if ns.interactive:
            sql.interactive()
            sys.exit(0)
        sql_caluse = ns.sql

        if sql.confirm(sql_caluse):
            result = sql.execute(sql_caluse)
            print(result)
        sys.exit(0)


if __name__ == "__main__":
    sqlcli()
