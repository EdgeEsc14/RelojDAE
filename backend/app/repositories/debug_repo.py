from sqlalchemy import text
from sqlalchemy.orm import Session


SCHEMAS_PERMITIDOS = {
    "organizacion",
    "personal",
    "seguridad",
    "asistencia",
    "dispositivos",
    "auditoria",
}


def listar_tablas_sistema(db: Session) -> list[dict]:
    query = text(
        """
        SELECT
            table_schema,
            table_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema IN (
            'organizacion',
            'personal',
            'seguridad',
            'asistencia',
            'dispositivos',
            'auditoria'
        )
        ORDER BY
            table_schema,
            table_name
        """
    )

    rows = db.execute(query).mappings().all()

    return [dict(row) for row in rows]


def listar_columnas_tabla(
    db: Session,
    schema_name: str,
    table_name: str,
) -> list[dict]:
    if schema_name not in SCHEMAS_PERMITIDOS:
        raise ValueError(f"Schema no permitido: {schema_name}")

    query = text(
        """
        SELECT
            ordinal_position,
            column_name,
            data_type,
            udt_name,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = :schema_name
          AND table_name = :table_name
        ORDER BY ordinal_position
        """
    )

    rows = db.execute(
        query,
        {
            "schema_name": schema_name,
            "table_name": table_name,
        },
    ).mappings().all()

    return [dict(row) for row in rows]


def obtener_resumen_tablas_clave(db: Session) -> list[dict]:
    query = text(
        """
        SELECT
            c.table_schema,
            c.table_name,
            COUNT(*) AS total_columnas
        FROM information_schema.columns c
        WHERE c.table_schema IN (
            'organizacion',
            'personal',
            'seguridad',
            'asistencia',
            'dispositivos',
            'auditoria'
        )
        GROUP BY
            c.table_schema,
            c.table_name
        ORDER BY
            c.table_schema,
            c.table_name
        """
    )

    rows = db.execute(query).mappings().all()

    return [dict(row) for row in rows]