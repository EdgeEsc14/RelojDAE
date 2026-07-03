from pathlib import Path
import sys

from sqlalchemy import text


# Permite importar app.core.database cuando ejecutamos desde backend/scripts
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


from app.core.database import SessionLocal  # noqa: E402


def main():
    db = SessionLocal()

    try:
        rows = db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'personal'
                  AND table_name = 'empleados'
                ORDER BY ordinal_position
                """
            )
        ).fetchall()

        print("Columnas de personal.empleados:")

        for row in rows:
            print("-", row[0])

    finally:
        db.close()


if __name__ == "__main__":
    main()