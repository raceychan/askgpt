from sqlalchemy import create_engine, text, TextClause
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, text
from sqlalchemy.orm import registry


from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


def create_table(db_url: str, *, meta: MetaData):
    engine = create_engine(db_url)
    meta.create_all(engine)


meta = MetaData()

progress_table = Table(
    "scraper_progress",
    meta,
    Column("progress_id", Integer, primary_key=True, autoincrement=True),
    Column("current_url", String, nullable=False),
    Column("current_page", Integer, nullable=False),
    Column("created_at", DateTime, server_default=text("CURRENT_TIMESTAMP")),
    Column("modified_at", DateTime, server_default=text("CURRENT_TIMESTAMP")),
)


mapper_registry = registry()
mapper_registry.map_imperatively()


def sa_options(
    cls,
    primary_key: bool = False,
    index: bool = False,
    unique: bool = False,
    server_defualt: TextClause = "",
    nullable: bool = False,
) -> dict:
    return dict(
        primary_key=primary_key,
        index=index,
        unique=unique,
        nullable=nullable,
        server_defualt=server_defualt,
    )


from pydantic import BaseModel, Field
from uuid import uuid4


class DomainEvent(BaseModel):
    nane: str = Field(default_factory=uuid4, **sa_options(primary_key=True))


class DomainMeta(MetaData):
    def from_pydantic(self, model: BaseModel):
        tablename = model.__class__.__name__.lower()
        columns = []
        for field_name, field_info in model.model_fields.items():
            attrs = getattr(field_info, "json_schema_extra", {}).get("sa_attrs", {})
            if not attrs:
                continue

            col = Column(field_name, **attrs)
            columns.append(col)
        return Table(tablename, self, *columns)


if __name__ == "__main__":
    create_table("sqlite:///test.db", meta=meta)
