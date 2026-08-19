"""
Repositorio para gestión de usuarios del sistema.

Accede a seguridad.usuarios y seguridad.roles.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import hash_password


# ============================================================
# Listar usuarios
# ============================================================


def listar_usuarios(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 50,
    rol_id: int | None = None,
    estatus: str | None = None,
    busqueda: str | None = None,
) -> dict[str, Any]:
    """
    Lista usuarios del sistema con filtros opcionales y paginación.
    """
    conditions = []
    params: dict[str, Any] = {}

    if rol_id is not None:
        conditions.append("u.rol_id = :rol_id")
        params["rol_id"] = rol_id

    if estatus is not None:
        estatus_upper = estatus.strip().upper()
        if estatus_upper in ("ACTIVO", "INACTIVO", "BLOQUEADO"):
            conditions.append("u.estatus = :estatus")
            params["estatus"] = estatus_upper

    if busqueda:
        busqueda_like = f"%{busqueda.strip().lower()}%"
        conditions.append(
            """
            (
                LOWER(u.correo_electronico) LIKE :busqueda
                OR LOWER(u.nombre_usuario) LIKE :busqueda
                OR LOWER(COALESCE(e.nombre_completo, '')) LIKE :busqueda
            )
            """
        )
        params["busqueda"] = busqueda_like

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Count total
    count_query = text(
        f"""
        SELECT COUNT(*) AS total
        FROM seguridad.usuarios u
        LEFT JOIN personal.empleados e ON e.id = u.empleado_id
        {where_clause}
        """
    )
    total = db.execute(count_query, params).scalar_one()

    # Fetch page
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    data_query = text(
        f"""
        SELECT
            u.id,
            u.correo_electronico,
            u.nombre_usuario,
            u.rol_id,
            r.codigo AS rol_codigo,
            r.nombre AS rol_nombre,
            u.empleado_id,
            e.codigo_empleado,
            e.nombre_completo AS nombre_empleado,
            u.estatus,
            u.activo,
            u.requiere_cambio_password,
            u.ultimo_login,
            u.fecha_creacion,
            u.fecha_modificacion
        FROM seguridad.usuarios u
        LEFT JOIN seguridad.roles r ON r.id = u.rol_id
        LEFT JOIN personal.empleados e ON e.id = u.empleado_id
        {where_clause}
        ORDER BY u.fecha_creacion DESC
        LIMIT :limit OFFSET :offset
        """
    )

    rows = db.execute(data_query, params).mappings().all()

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============================================================
# Obtener usuario por ID
# ============================================================


def obtener_usuario_por_id(
    db: Session,
    usuario_id: int,
) -> dict[str, Any] | None:
    """Obtiene un usuario por ID con información de rol y empleado."""

    query = text(
        """
        SELECT
            u.id,
            u.correo_electronico,
            u.nombre_usuario,
            u.rol_id,
            r.codigo AS rol_codigo,
            r.nombre AS rol_nombre,
            u.empleado_id,
            e.codigo_empleado,
            e.nombre_completo AS nombre_empleado,
            u.estatus,
            u.activo,
            u.requiere_cambio_password,
            u.ultimo_login,
            u.fecha_creacion,
            u.fecha_modificacion
        FROM seguridad.usuarios u
        LEFT JOIN seguridad.roles r ON r.id = u.rol_id
        LEFT JOIN personal.empleados e ON e.id = u.empleado_id
        WHERE u.id = :usuario_id
        """
    )

    row = db.execute(query, {"usuario_id": usuario_id}).mappings().first()

    if row is None:
        return None

    return dict(row)


# ============================================================
# Crear usuario
# ============================================================


def crear_usuario(
    db: Session,
    *,
    correo_electronico: str,
    password: str,
    rol_id: int,
    nombre_usuario: str | None = None,
    empleado_id: int | None = None,
    requiere_cambio_password: bool = True,
) -> dict[str, Any]:
    """
    Crea un nuevo usuario del sistema.

    Valida:
    - Rol activo existe
    - Correo no duplicado
    - Nombre de usuario no duplicado
    - Empleado no ya vinculado (si se envía)
    """

    # Validar que el rol existe y está activo
    rol = db.execute(
        text(
            """
            SELECT id, codigo, nombre
            FROM seguridad.roles
            WHERE id = :rol_id AND activo = TRUE
            """
        ),
        {"rol_id": rol_id},
    ).mappings().first()

    if rol is None:
        raise ValueError(f"No existe un rol activo con id {rol_id}.")

    # Validar correo único
    correo_normalizado = correo_electronico.strip().lower()
    existe_correo = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1 FROM seguridad.usuarios
                WHERE LOWER(BTRIM(correo_electronico)) = :correo
            )
            """
        ),
        {"correo": correo_normalizado},
    ).scalar_one()

    if existe_correo:
        raise ValueError(f"Ya existe un usuario con correo {correo_normalizado}.")

    # Generar nombre_usuario si no se proporcionó
    if nombre_usuario is None:
        nombre_usuario = correo_normalizado.split("@")[0]

    nombre_usuario_normalizado = nombre_usuario.strip().lower()

    # Validar nombre_usuario único
    existe_nombre = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1 FROM seguridad.usuarios
                WHERE LOWER(BTRIM(nombre_usuario)) = :nombre_usuario
                  AND nombre_usuario IS NOT NULL
            )
            """
        ),
        {"nombre_usuario": nombre_usuario_normalizado},
    ).scalar_one()

    if existe_nombre:
        raise ValueError(f"Ya existe un usuario con nombre '{nombre_usuario_normalizado}'.")

    # Validar empleado no vinculado (si se envía)
    if empleado_id is not None:
        # Verificar que el empleado existe
        empleado_existe = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM personal.empleados
                    WHERE id = :empleado_id
                )
                """
            ),
            {"empleado_id": empleado_id},
        ).scalar_one()

        if not empleado_existe:
            raise ValueError(f"No existe un empleado con id {empleado_id}.")

        # Verificar que no tiene usuario ya
        empleado_con_usuario = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM seguridad.usuarios
                    WHERE empleado_id = :empleado_id
                      AND estatus IN ('ACTIVO', 'PENDIENTE_VERIFICACION', 'PENDIENTE_APROBACION')
                )
                """
            ),
            {"empleado_id": empleado_id},
        ).scalar_one()

        if empleado_con_usuario:
            raise ValueError("Este empleado ya tiene un usuario activo vinculado.")

    # Hash de password
    password_hash = hash_password(password)

    # Rol en texto para columna legacy
    rol_texto = str(rol["codigo"]).lower()

    try:
        row = db.execute(
            text(
                """
                INSERT INTO seguridad.usuarios (
                    empleado_id,
                    rol_id,
                    correo_electronico,
                    correo,
                    password_hash,
                    nombre_usuario,
                    rol,
                    estatus,
                    activo,
                    correo_verificado,
                    requiere_cambio_password,
                    fecha_creacion,
                    fecha_modificacion
                )
                VALUES (
                    :empleado_id,
                    :rol_id,
                    :correo_electronico,
                    :correo,
                    :password_hash,
                    :nombre_usuario,
                    :rol,
                    'ACTIVO',
                    TRUE,
                    TRUE,
                    :requiere_cambio_password,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                RETURNING id
                """
            ),
            {
                "empleado_id": empleado_id,
                "rol_id": rol_id,
                "correo_electronico": correo_normalizado,
                "correo": correo_normalizado,
                "password_hash": password_hash,
                "nombre_usuario": nombre_usuario_normalizado,
                "rol": rol_texto,
                "requiere_cambio_password": requiere_cambio_password,
            },
        ).mappings().one()

        usuario_id = row["id"]
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_usuario_por_id(db, usuario_id)


# ============================================================
# Actualizar usuario
# ============================================================


def actualizar_usuario(
    db: Session,
    usuario_id: int,
    *,
    correo_electronico: str | None = None,
    rol_id: int | None = None,
    nombre_usuario: str | None = None,
    empleado_id: int | None = None,
    estatus: str | None = None,
    requiere_cambio_password: bool | None = None,
    nueva_password: str | None = None,
) -> dict[str, Any] | None:
    """
    Actualiza campos de un usuario existente.
    Solo modifica los campos que se envían (no None).
    """

    # Verificar que el usuario existe
    usuario_actual = obtener_usuario_por_id(db, usuario_id)
    if usuario_actual is None:
        return None

    sets: list[str] = []
    params: dict[str, Any] = {"usuario_id": usuario_id}

    if correo_electronico is not None:
        correo_normalizado = correo_electronico.strip().lower()
        # Validar que no esté duplicado
        existe = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM seguridad.usuarios
                    WHERE LOWER(BTRIM(correo_electronico)) = :correo
                      AND id != :usuario_id
                )
                """
            ),
            {"correo": correo_normalizado, "usuario_id": usuario_id},
        ).scalar_one()

        if existe:
            raise ValueError(f"Ya existe otro usuario con correo {correo_normalizado}.")

        sets.append("correo_electronico = :correo_electronico")
        sets.append("correo = :correo")
        params["correo_electronico"] = correo_normalizado
        params["correo"] = correo_normalizado

    if rol_id is not None:
        # Validar rol
        rol = db.execute(
            text(
                "SELECT codigo FROM seguridad.roles WHERE id = :rol_id AND activo = TRUE"
            ),
            {"rol_id": rol_id},
        ).mappings().first()

        if rol is None:
            raise ValueError(f"No existe un rol activo con id {rol_id}.")

        sets.append("rol_id = :rol_id")
        sets.append("rol = :rol_texto")
        params["rol_id"] = rol_id
        params["rol_texto"] = str(rol["codigo"]).lower()

    if nombre_usuario is not None:
        nombre_normalizado = nombre_usuario.strip().lower()
        existe = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM seguridad.usuarios
                    WHERE LOWER(BTRIM(nombre_usuario)) = :nombre_usuario
                      AND nombre_usuario IS NOT NULL
                      AND id != :usuario_id
                )
                """
            ),
            {"nombre_usuario": nombre_normalizado, "usuario_id": usuario_id},
        ).scalar_one()

        if existe:
            raise ValueError(f"Ya existe otro usuario con nombre '{nombre_normalizado}'.")

        sets.append("nombre_usuario = :nombre_usuario")
        params["nombre_usuario"] = nombre_normalizado

    if empleado_id is not None:
        # Verificar empleado existe
        empleado_existe = db.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM personal.empleados WHERE id = :empleado_id)"
            ),
            {"empleado_id": empleado_id},
        ).scalar_one()

        if not empleado_existe:
            raise ValueError(f"No existe un empleado con id {empleado_id}.")

        # Verificar que no esté vinculado a otro usuario
        vinculado = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM seguridad.usuarios
                    WHERE empleado_id = :empleado_id
                      AND id != :usuario_id
                      AND estatus IN ('ACTIVO', 'PENDIENTE_VERIFICACION', 'PENDIENTE_APROBACION')
                )
                """
            ),
            {"empleado_id": empleado_id, "usuario_id": usuario_id},
        ).scalar_one()

        if vinculado:
            raise ValueError("Este empleado ya está vinculado a otro usuario activo.")

        sets.append("empleado_id = :empleado_id")
        params["empleado_id"] = empleado_id

    if estatus is not None:
        estatus_upper = estatus.strip().upper()
        sets.append("estatus = :estatus")
        sets.append("activo = :activo")
        params["estatus"] = estatus_upper
        params["activo"] = estatus_upper == "ACTIVO"

    if requiere_cambio_password is not None:
        sets.append("requiere_cambio_password = :requiere_cambio_password")
        params["requiere_cambio_password"] = requiere_cambio_password

    if nueva_password is not None:
        sets.append("password_hash = :password_hash")
        params["password_hash"] = hash_password(nueva_password)

    if not sets:
        return usuario_actual

    sets.append("fecha_modificacion = CURRENT_TIMESTAMP")

    set_clause = ", ".join(sets)

    try:
        db.execute(
            text(
                f"""
                UPDATE seguridad.usuarios
                SET {set_clause}
                WHERE id = :usuario_id
                """
            ),
            params,
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_usuario_por_id(db, usuario_id)


# ============================================================
# Desactivar usuario
# ============================================================


def desactivar_usuario(
    db: Session,
    usuario_id: int,
) -> dict[str, Any] | None:
    """Desactiva un usuario (no lo elimina)."""

    usuario = obtener_usuario_por_id(db, usuario_id)
    if usuario is None:
        return None

    try:
        db.execute(
            text(
                """
                UPDATE seguridad.usuarios
                SET
                    estatus = 'INACTIVO',
                    activo = FALSE,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :usuario_id
                """
            ),
            {"usuario_id": usuario_id},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_usuario_por_id(db, usuario_id)


# ============================================================
# Listar roles (catálogo)
# ============================================================


def listar_roles(db: Session) -> list[dict[str, Any]]:
    """Retorna los roles activos del sistema."""

    rows = db.execute(
        text(
            """
            SELECT
                id,
                codigo,
                nombre,
                descripcion,
                es_sistema,
                activo
            FROM seguridad.roles
            WHERE activo = TRUE
            ORDER BY orden_visual ASC
            """
        )
    ).mappings().all()

    return [dict(row) for row in rows]
