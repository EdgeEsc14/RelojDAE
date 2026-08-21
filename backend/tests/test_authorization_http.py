"""
Tests HTTP de autorización para el módulo de asistencia (Contrato §16).

Ejercen la autorización real de extremo a extremo — TestClient + JWT real
(create_access_token/decode_access_token) + require_module_access /
build_access_scope reales contra PostgreSQL — para demostrar que el
backend aplica los alcances TOTAL/AREA/PROPIO y la restricción LECTURA
sin depender de ningún filtro de frontend.
"""

from datetime import date

import pytest
from sqlalchemy import text

from app.core.security import create_access_token


FECHA_TEST = date(2026, 8, 18)


# ============================================================
# Helpers de seed (seguridad + organización + empleados)
# ============================================================


def _crear_modulo(db, codigo="ASISTENCIA"):
    db.execute(text(
        "INSERT INTO seguridad.modulos (codigo, nombre, activo) "
        "VALUES (:codigo, :codigo, TRUE) "
        "ON CONFLICT (codigo) DO NOTHING"
    ), {"codigo": codigo})
    return db.execute(text(
        "SELECT id FROM seguridad.modulos WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_rol(
    db,
    *,
    codigo,
    modulo_codigo="ASISTENCIA",
    alcance_datos,
    puede_consultar=True,
    puede_crear=False,
    puede_editar=False,
    puede_eliminar=False,
    puede_aprobar=False,
    puede_exportar=False,
):
    db.execute(text(
        "INSERT INTO seguridad.roles (codigo, nombre, activo) "
        "VALUES (:codigo, :codigo, TRUE)"
    ), {"codigo": codigo})
    rol_id = db.execute(text(
        "SELECT id FROM seguridad.roles WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()

    modulo_id = _crear_modulo(db, modulo_codigo)

    db.execute(text(
        "INSERT INTO seguridad.permisos_rol "
        "(rol_id, modulo_id, alcance_datos, puede_consultar, puede_crear, "
        "puede_editar, puede_eliminar, puede_aprobar, puede_exportar) "
        "VALUES (:rol_id, :modulo_id, :alcance, :consultar, :crear, "
        ":editar, :eliminar, :aprobar, :exportar)"
    ), {
        "rol_id": rol_id,
        "modulo_id": modulo_id,
        "alcance": alcance_datos,
        "consultar": puede_consultar,
        "crear": puede_crear,
        "editar": puede_editar,
        "eliminar": puede_eliminar,
        "aprobar": puede_aprobar,
        "exportar": puede_exportar,
    })
    return rol_id


def _crear_unidad(db, codigo, padre_id=None):
    db.execute(text(
        "INSERT INTO organizacion.unidades_organizacionales "
        "(codigo, nombre, unidad_padre_id, activo) "
        "VALUES (:codigo, :codigo, :padre_id, TRUE)"
    ), {"codigo": codigo, "padre_id": padre_id})
    return db.execute(text(
        "SELECT id FROM organizacion.unidades_organizacionales WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_puesto(db, codigo="PUESTO_AUTH"):
    db.execute(text(
        "INSERT INTO organizacion.puestos (codigo, nombre, nivel_jerarquico, activo) "
        "VALUES (:codigo, :codigo, 1, TRUE) "
        "ON CONFLICT (codigo) DO NOTHING"
    ), {"codigo": codigo})
    return db.execute(text(
        "SELECT id FROM organizacion.puestos WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_empleado(db, codigo, unidad_id, puesto_id):
    db.execute(text(
        "INSERT INTO personal.empleados "
        "(codigo_empleado, nombres, apellido_paterno, correo, "
        "unidad_organizacional_id, puesto_id, estatus) "
        "VALUES (:codigo, 'TEST', 'AUTH', :correo, :unidad_id, :puesto_id, 'ACTIVO')"
    ), {
        "codigo": codigo,
        "correo": f"{codigo.lower()}@dae.test",
        "unidad_id": unidad_id,
        "puesto_id": puesto_id,
    })
    return db.execute(text(
        "SELECT id FROM personal.empleados WHERE codigo_empleado = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_usuario(db, *, rol_id, correo, empleado_id=None, estatus="ACTIVO"):
    db.execute(text(
        "INSERT INTO seguridad.usuarios "
        "(empleado_id, rol_id, correo, correo_electronico, estatus) "
        "VALUES (:empleado_id, :rol_id, :correo, :correo, :estatus)"
    ), {
        "empleado_id": empleado_id,
        "rol_id": rol_id,
        "correo": correo,
        "estatus": estatus,
    })
    return db.execute(text(
        "SELECT id FROM seguridad.usuarios WHERE correo_electronico = :correo"
    ), {"correo": correo}).scalar_one()


def _asignar_unidad(db, usuario_id, unidad_id, incluye_descendientes=True):
    db.execute(text(
        "INSERT INTO seguridad.usuarios_unidades "
        "(usuario_id, unidad_organizacional_id, incluye_descendientes, activo) "
        "VALUES (:usuario_id, :unidad_id, :incluye, TRUE)"
    ), {
        "usuario_id": usuario_id,
        "unidad_id": unidad_id,
        "incluye": incluye_descendientes,
    })


def _seed_catalogo_asistencia(db):
    """Catálogo mínimo (tipo_turno + horario + política) para poder
    insertar filas válidas en asistencia.asistencias_diarias."""
    db.execute(text(
        "INSERT INTO asistencia.tipos_turno "
        "(codigo, nombre, duracion_jornada_minutos, modalidad_tiempo_extra, hora_entrada_desde) "
        "VALUES ('AUTH_TURNO', 'Auth Turno', 420, 'NO_APLICA', '06:00')"
    ))
    tipo_turno_id = db.execute(text(
        "SELECT id FROM asistencia.tipos_turno WHERE codigo = 'AUTH_TURNO'"
    )).scalar_one()

    db.execute(text(
        "INSERT INTO asistencia.horarios "
        "(codigo, nombre, tipo_turno_id, hora_entrada, hora_salida, tolerancia_entrada_minutos) "
        "VALUES ('AUTH_HORARIO', 'Auth Horario', :tid, '08:00', '15:00', 10)"
    ), {"tid": tipo_turno_id})
    horario_id = db.execute(text(
        "SELECT id FROM asistencia.horarios WHERE codigo = 'AUTH_HORARIO'"
    )).scalar_one()

    db.execute(text(
        "INSERT INTO asistencia.politicas_asistencia "
        "(codigo, version, nombre, tipo_periodo, limite_tolerancia_segundos, "
        "limite_retardo_menor_segundos, limite_retardo_mayor_segundos, "
        "puntos_retardo_menor, puntos_retardo_mayor, puntos_para_descanso, "
        "max_dias_justificables_periodo, max_puntos_descontables_por_dia, "
        "descansos_para_revision_baja, faltas_consecutivas_revision_baja, "
        "vigencia_desde, activo) "
        "VALUES ('AUTH_POLITICA', 1, 'Auth Politica', 'QUINCENAL', 659, 1259, "
        "1859, 1, 2, 10, 2, 2, 7, 3, '2026-01-01', TRUE)"
    ))
    politica_id = db.execute(text(
        "SELECT id FROM asistencia.politicas_asistencia WHERE codigo = 'AUTH_POLITICA'"
    )).scalar_one()

    return horario_id, politica_id


def _crear_asistencia_diaria(db, *, empleado_id, horario_id, politica_id, fecha, estatus="COMPLETO"):
    db.execute(text(
        "INSERT INTO asistencia.asistencias_diarias "
        "(empleado_id, politica_asistencia_id, horario_id, fecha, "
        "estatus, procesada, requiere_revision, fecha_procesamiento) "
        "VALUES (:empleado_id, :politica_id, :horario_id, :fecha, "
        ":estatus, TRUE, FALSE, CURRENT_TIMESTAMP)"
    ), {
        "empleado_id": empleado_id,
        "politica_id": politica_id,
        "horario_id": horario_id,
        "fecha": fecha,
        "estatus": estatus,
    })


def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# Tests
# ============================================================


@pytest.mark.integration
class TestAutorizacionAsistenciaHTTP:
    """Contrato §16: alcances TOTAL/AREA/PROPIO y restricción LECTURA
    aplicados en backend, verificados vía HTTP real."""

    def test_lectura_puede_consultar_pero_no_modificar(self, db_motor, api_client):
        """
        1. LECTURA (alcance TOTAL + solo puede_consultar) puede hacer GET
        pero cualquier POST/PUT/PATCH/DELETE debe bloquearse con 403,
        aunque el frontend "permitiera" intentarlo.
        """
        unidad_id = _crear_unidad(db_motor, "UNIDAD_LECTURA")
        puesto_id = _crear_puesto(db_motor)
        empleado_id = _crear_empleado(db_motor, "EMP-LECTURA", unidad_id, puesto_id)

        rol_id = _crear_rol(
            db_motor,
            codigo="ROL_LECTURA",
            alcance_datos="TOTAL",
            puede_consultar=True,
            puede_editar=False,
            puede_crear=False,
        )
        usuario_id = _crear_usuario(
            db_motor, rol_id=rol_id, correo="lectura@dae.test", empleado_id=empleado_id
        )
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        resp_get = api_client.get(
            "/api/v1/asistencia/diaria",
            params={"fecha": str(FECHA_TEST)},
            headers=headers,
        )
        assert resp_get.status_code == 200, resp_get.text

        resp_post = api_client.post(
            "/api/v1/asistencia/procesar",
            json={"fecha_inicio": str(FECHA_TEST), "fecha_fin": str(FECHA_TEST)},
            headers=headers,
        )
        assert resp_post.status_code == 403, resp_post.text

    def test_propio_no_puede_consultar_otro_empleado(self, db_motor, api_client):
        """
        2. PROPIO solo puede consultar su propio resumen de asistencia;
        pedir el de otro empleado debe fallar (404, sin filtrar por scope
        en frontend: el backend no debe ni siquiera revelar que existe).
        """
        unidad_id = _crear_unidad(db_motor, "UNIDAD_PROPIO")
        puesto_id = _crear_puesto(db_motor)
        empleado_propio = _crear_empleado(db_motor, "EMP-PROPIO", unidad_id, puesto_id)
        empleado_otro = _crear_empleado(db_motor, "EMP-OTRO-PROPIO", unidad_id, puesto_id)

        rol_id = _crear_rol(
            db_motor,
            codigo="ROL_PROPIO",
            alcance_datos="PROPIO",
            puede_consultar=True,
        )
        usuario_id = _crear_usuario(
            db_motor, rol_id=rol_id, correo="propio@dae.test", empleado_id=empleado_propio
        )
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        resp_propio = api_client.get(
            "/api/v1/asistencia/empleados/EMP-PROPIO/resumen",
            headers=headers,
        )
        assert resp_propio.status_code == 200, resp_propio.text
        assert resp_propio.json()["empleado"]["codigo_empleado"] == "EMP-PROPIO"

        resp_otro = api_client.get(
            "/api/v1/asistencia/empleados/EMP-OTRO-PROPIO/resumen",
            headers=headers,
        )
        assert resp_otro.status_code == 404, resp_otro.text

    def test_area_no_puede_salir_de_su_alcance(self, db_motor, api_client):
        """
        3. AREA solo ve información de su(s) unidad(es) autorizada(s); un
        empleado de otra área no debe aparecer en el listado ni ser
        consultable, aunque comparta la misma fecha de asistencia.
        """
        unidad_propia = _crear_unidad(db_motor, "AREA_PROPIA")
        unidad_ajena = _crear_unidad(db_motor, "AREA_AJENA")
        puesto_id = _crear_puesto(db_motor)

        empleado_propio = _crear_empleado(db_motor, "EMP-AREA-PROPIA", unidad_propia, puesto_id)
        empleado_ajeno = _crear_empleado(db_motor, "EMP-AREA-AJENA", unidad_ajena, puesto_id)

        horario_id, politica_id = _seed_catalogo_asistencia(db_motor)
        _crear_asistencia_diaria(
            db_motor, empleado_id=empleado_propio, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_TEST,
        )
        _crear_asistencia_diaria(
            db_motor, empleado_id=empleado_ajeno, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_TEST,
        )

        rol_id = _crear_rol(
            db_motor,
            codigo="ROL_AREA",
            alcance_datos="AREA",
            puede_consultar=True,
        )
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="area@dae.test")
        _asignar_unidad(db_motor, usuario_id, unidad_propia)
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        resp = api_client.get(
            "/api/v1/asistencia/diaria",
            params={"fecha": str(FECHA_TEST)},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        codigos = {item["codigo_empleado"] for item in resp.json()["items"]}
        assert "EMP-AREA-PROPIA" in codigos
        assert "EMP-AREA-AJENA" not in codigos

        resp_ajeno = api_client.get(
            "/api/v1/asistencia/empleados/EMP-AREA-AJENA/resumen",
            headers=headers,
        )
        assert resp_ajeno.status_code == 404, resp_ajeno.text

    def test_total_mantiene_acceso_correcto(self, db_motor, api_client):
        """
        4. TOTAL ve todos los empleados/áreas y, si además tiene permiso
        de edición, puede ejecutar el procesamiento global.
        """
        unidad_a = _crear_unidad(db_motor, "AREA_A_TOTAL")
        unidad_b = _crear_unidad(db_motor, "AREA_B_TOTAL")
        puesto_id = _crear_puesto(db_motor)

        empleado_a = _crear_empleado(db_motor, "EMP-TOTAL-A", unidad_a, puesto_id)
        empleado_b = _crear_empleado(db_motor, "EMP-TOTAL-B", unidad_b, puesto_id)

        horario_id, politica_id = _seed_catalogo_asistencia(db_motor)
        _crear_asistencia_diaria(
            db_motor, empleado_id=empleado_a, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_TEST,
        )
        _crear_asistencia_diaria(
            db_motor, empleado_id=empleado_b, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_TEST,
        )

        rol_id = _crear_rol(
            db_motor,
            codigo="ROL_TOTAL",
            alcance_datos="TOTAL",
            puede_consultar=True,
            puede_editar=True,
        )
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="total@dae.test")
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        resp = api_client.get(
            "/api/v1/asistencia/diaria",
            params={"fecha": str(FECHA_TEST)},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        codigos = {item["codigo_empleado"] for item in resp.json()["items"]}
        assert {"EMP-TOTAL-A", "EMP-TOTAL-B"} <= codigos

        resp_procesar = api_client.post(
            "/api/v1/asistencia/procesar",
            json={"fecha_inicio": str(FECHA_TEST), "fecha_fin": str(FECHA_TEST)},
            headers=headers,
        )
        assert resp_procesar.status_code == 200, resp_procesar.text

    def test_usuario_sin_permiso_recibe_403(self, db_motor, api_client):
        """
        5. Un usuario autenticado pero sin ningún permiso configurado
        para el módulo ASISTENCIA (sin fila en permisos_rol) recibe 403,
        no una lista vacía ni un 500.
        """
        rol_id = db_motor.execute(text(
            "INSERT INTO seguridad.roles (codigo, nombre, activo) "
            "VALUES ('ROL_SIN_ACCESO', 'ROL_SIN_ACCESO', TRUE) "
            "RETURNING id"
        )).scalar_one()
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="sinacceso@dae.test")
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        resp = api_client.get(
            "/api/v1/asistencia/diaria",
            params={"fecha": str(FECHA_TEST)},
            headers=headers,
        )
        assert resp.status_code == 403, resp.text

    def test_sin_token_recibe_401(self, db_motor, api_client):
        """Complemento de (5): sin token de autenticación, 401 (no 403)."""
        resp = api_client.get(
            "/api/v1/asistencia/diaria",
            params={"fecha": str(FECHA_TEST)},
        )
        assert resp.status_code == 401, resp.text
