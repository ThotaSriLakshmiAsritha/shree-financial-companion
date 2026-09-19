import time
from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.metrics import metrics
from app.core.time import APPLICATION_TIMEZONE_NAME


def build_engine() -> Engine:
    database_url = get_settings().database_url
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


engine = build_engine()


@event.listens_for(engine, "connect")
def _set_application_timezone(dbapi_connection, _connection_record) -> None:
    if engine.url.drivername.startswith("sqlite"):
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute(f"SET TIME ZONE '{APPLICATION_TIMEZONE_NAME}'")
    finally:
        cursor.close()


@event.listens_for(engine, "before_cursor_execute")
def _start_query_timer(_connection, _cursor, _statement, _parameters, context, _executemany) -> None:
    context._sahachari_query_started = time.perf_counter()


@event.listens_for(engine, "after_cursor_execute")
def _record_query_timer(_connection, _cursor, _statement, _parameters, context, _executemany) -> None:
    started = getattr(context, "_sahachari_query_started", None)
    if started is not None:
        metrics.observe("database.query", (time.perf_counter() - started) * 1000)


@event.listens_for(engine, "handle_error")
def _record_query_error(_exception_context) -> None:
    metrics.observe("database.query", 0, ok=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
