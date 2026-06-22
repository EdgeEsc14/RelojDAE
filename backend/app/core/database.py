from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    future=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """
    Abre una sesión de base de datos por request.

    FastAPI usará esta función como dependencia para endpoints que necesiten
    consultar PostgreSQL.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def probar_conexion_db() -> dict:
    """
    Prueba la conexión real contra PostgreSQL.

    Valida:
    - Base conectada.
    - Usuario actual.
    - Hora del servidor PostgreSQL.
    """
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        current_database() AS database_name,
                        current_user AS current_user,
                        now() AS server_time
                    """
                )
            ).mappings().one()

            return dict(row)

    except SQLAlchemyError as exc:
        raise RuntimeError(f"No se pudo conectar a PostgreSQL: {exc}") from exc