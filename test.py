import sqlalchemy as sa
from rich import print
from askeda import EventStore, AskAnswered, Ask, AskHistory, Envelope, uuid_factory


def test_db():
    db_url = "./eventstore.db"
    engine = sa.create_engine(f"sqlite+aiosqlite:///{db_url}:", echo=True)
    es = EventStore(engine)


def test_event():
    ask = Ask(question="what is your name?")
    e = AskAnswered(ask=ask, entity_id=uuid_factory())
    print(e)


def test_model():
    history = AskHistory()
    ask = Ask(question="what is your name?")
    e = AskAnswered(ask=ask, entity_id=history.history_id)
    env = Envelope(payload=e)
    data = env.model_dump()
    print(data)


def test_table():
    table = Envelope.table_clause()
    fields = Envelope.model_all_fields()
    print(fields)


test_table()
