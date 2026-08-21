"""
Repositorio de Auditoría.

Fuentes reales, sin mocks:
- auditoria.bitacora (migración 035): trigger genérico de
  INSERT/UPDATE/DELETE sobre organizacion/personal/asistencia/
  seguridad/dispositivos. Captura automáticamente cualquier cambio
  administrativo (usuarios, roles, permisos, empleados, horarios,
  dispositivos, etc.) sin que cada endpoint tenga que registrarlo a mano.
- seguridad.login_auditoria (migración 055): bitácora de intentos de
  login del sistema web, ya poblada por POST /auth/login.

No existe una tercera fuente inventada: esta pantalla no fabrica
eventos que no estén respaldados por estas dos tablas.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


# ============================================================
# Bitácora de cambios (auditoria.bitacora)
# ============================================================


def listar_bitacora(
    db: Session,
    *,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    esquema: str | None = None,
    tabla: str | None = None,
    operacion: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    conditions = ["1 = 1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if fecha_inicio is not None:
        conditions.append("fecha_evento::date >= :fecha_inicio")
        params["fecha_inicio"] = fecha_inicio

    if fecha_fin is not None:
        conditions.append("fecha_evento::date <= :fecha_fin")
        params["fecha_fin"] = fecha_fin

    if esquema:
        conditions.append("esquema = :esquema")
        params["esquema"] = esquema

    if tabla:
        conditions.append("tabla = :tabla")
        params["tabla"] = tabla

    if operacion:
        conditions.append("operacion = :operacion")
        params["operacion"] = operacion

    if q:
        conditions.append(
            """
            (
                esquema ILIKE :q
                OR tabla ILIKE :q
                OR COALESCE(usuario_app_correo, '') ILIKE :q
                OR COALESCE(registro_id, '') ILIKE :q
                OR COALESCE(accion_app, '') ILIKE :q
                OR COALESCE(modulo, '') ILIKE :q
            )
            """
        )
        params["q"] = f"%{q.strip()}%"

    where_sql = " AND ".join(conditions)

    total = db.execute(
        text(f"SELECT COUNT(*) FROM auditoria.bitacora WHERE {where_sql}"),
        params,
    ).scalar_one()

    # Se consulta la tabla base directamente (no la vista
    # vw_bitacora_resumen): la vista de la migración 035 no expone
    # ip_origen, y esta pantalla sí lo necesita para el listado.
    rows = db.execute(
        text(
            f"""
            SELECT
                id,
                fecha_evento,
                esquema,
                tabla,
                esquema || '.' || tabla AS objeto,
                operacion,
                registro_id,
                usuario_app_id,
                usuario_app_correo,
                usuario_bd,
                ip_origen,
                modulo,
                accion_app,
                cambios
            FROM auditoria.bitacora
            WHERE {where_sql}
            ORDER BY fecha_evento DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    return {
        "total": total,
        "items": [dict(row) for row in rows],
    }


def obtener_evento_bitacora(
    db: Session,
    evento_id: int,
) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT
                id,
                fecha_evento,
                esquema,
                tabla,
                operacion,
                registro_id,
                usuario_app_id,
                usuario_app_correo,
                usuario_bd,
                ip_origen,
                modulo,
                accion_app,
                datos_anteriores,
                datos_nuevos,
                cambios
            FROM auditoria.bitacora
            WHERE id = :evento_id
            """
        ),
        {"evento_id": evento_id},
    ).mappings().first()

    return dict(row) if row is not None else None


def obtener_valores_distintos_bitacora(db: Session) -> dict[str, list[str]]:
    """Valores reales disponibles para poblar los selectores de filtro."""
    esquemas = db.execute(
        text("SELECT DISTINCT esquema FROM auditoria.bitacora ORDER BY esquema")
    ).scalars().all()

    tablas = db.execute(
        text("SELECT DISTINCT tabla FROM auditoria.bitacora ORDER BY tabla")
    ).scalars().all()

    return {
        "esquemas": list(esquemas),
        "tablas": list(tablas),
    }


# ============================================================
# Bitácora de accesos (seguridad.login_auditoria)
# ============================================================


def listar_login_auditoria(
    db: Session,
    *,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    resultado: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    conditions = ["1 = 1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if fecha_inicio is not None:
        conditions.append("la.fecha_evento::date >= :fecha_inicio")
        params["fecha_inicio"] = fecha_inicio

    if fecha_fin is not None:
        conditions.append("la.fecha_evento::date <= :fecha_fin")
        params["fecha_fin"] = fecha_fin

    if resultado:
        conditions.append("la.resultado = :resultado")
        params["resultado"] = resultado

    if q:
        conditions.append(
            """
            (
                COALESCE(la.correo_intentado, '') ILIKE :q
                OR COALESCE(la.ip_origen_raw, '') ILIKE :q
                OR COALESCE(la.motivo, '') ILIKE :q
            )
            """
        )
        params["q"] = f"%{q.strip()}%"

    where_sql = " AND ".join(conditions)

    total = db.execute(
        text(f"SELECT COUNT(*) FROM seguridad.login_auditoria la WHERE {where_sql}"),
        params,
    ).scalar_one()

    rows = db.execute(
        text(
            f"""
            SELECT
                la.id,
                la.fecha_evento,
                la.usuario_id,
                u.correo_electronico AS usuario_correo,
                r.nombre AS usuario_rol,
                la.correo_intentado,
                la.resultado,
                la.motivo,
                la.ip_origen_raw,
                la.user_agent
            FROM seguridad.login_auditoria la
            LEFT JOIN seguridad.usuarios u ON u.id = la.usuario_id
            LEFT JOIN seguridad.roles r ON r.id = u.rol_id
            WHERE {where_sql}
            ORDER BY la.fecha_evento DESC, la.id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    return {
        "total": total,
        "items": [dict(row) for row in rows],
    }


# ============================================================
# Resumen para las tarjetas de Auditoría
# ============================================================


def obtener_resumen_auditoria(
    db: Session,
    *,
    fecha_inicio: date,
    fecha_fin: date,
) -> dict[str, Any]:
    bitacora_row = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE operacion = 'INSERT') AS inserts,
                COUNT(*) FILTER (WHERE operacion = 'UPDATE') AS updates,
                COUNT(*) FILTER (WHERE operacion = 'DELETE') AS deletes,
                COUNT(*) FILTER (WHERE esquema = 'seguridad') AS cambios_seguridad
            FROM auditoria.bitacora
            WHERE fecha_evento::date BETWEEN :fecha_inicio AND :fecha_fin
            """
        ),
        {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    ).mappings().one()

    login_row = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE resultado = 'EXITOSO') AS exitosos,
                COUNT(*) FILTER (WHERE resultado = 'FALLIDO') AS fallidos,
                COUNT(*) FILTER (WHERE resultado = 'BLOQUEADO') AS bloqueados
            FROM seguridad.login_auditoria
            WHERE fecha_evento::date BETWEEN :fecha_inicio AND :fecha_fin
            """
        ),
        {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    ).mappings().one()

    return {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "bitacora": dict(bitacora_row),
        "login": dict(login_row),
    }
