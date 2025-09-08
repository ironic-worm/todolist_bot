from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, create_engine

from settings import settings

engine = create_engine(settings["DB_STRING"])
meta = MetaData()

tasks = Table(
    "tasks",
    meta,
    Column("id", Integer, primary_key=True),
    Column("text", String, nullable=False),
    Column("is_done", Boolean, nullable=False, default=False),
    Column("parent_id", Integer, nullable=False),
)


def init_db():
    with engine.connect():
        meta.create_all(engine)
