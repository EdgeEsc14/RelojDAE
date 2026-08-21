"""
Tests del Dashboard:

- "Departamentos con más incidencias" no mezcla Dirección/División con
  Departamento (respeta jerarquía organizacional real);
- asistencia_hoy cubre todos los estatus del contrato;
- DIA_NO_LABORAL no contamina denominadores de puntualidad/asistencia;
- scopes TOTAL/AREA/PROPIO aplicados vía HTTP real.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app.core.security import create_access_token


HOY = date.today()


def _crear_tipo_unidad_ids(db) -> dict[str, int]:
    rows = db.execute(text("SELECT codigo, id FROM organizacion.tipos_unidad")).all()
    return {codigo: tid for codigo, tid in rows}


def _crear_unidad(db, *, codigo, tipo_id, padre_id=None):
    db.execute(text(
        "INSERT INTO organizacion.unidades_organizacionales "
        "(codigo, nombre, tipo_unidad_id, unidad_padre_id, activo) "
        "VALUES (:codigo, :codigo, :tipo_id, :padre_id, TRUE)"
    ), {"codigo": codigo, "tipo_id": tipo_id, "padre_id": padre_id})
    return db.execute(text(
        "SELECT id FROM organizacion.unidades_organizacionales WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_puesto(db, codigo="PUESTO_DASH"):
    db.execute(text(
        "INSERT INTO organizacion.puestos (codigo, nombre, nivel_jerarquico, activo) "
        "VALUES (:codigo, :codigo, 1, TRUE) ON CONFLICT (codigo) DO NOTHING"
    ), {"codigo": codigo})
    return db.execute(text(
        "SELECT id FROM organizacion.puestos WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_empleado(db, *, codigo, unidad_id, puesto_id):
    db.execute(text(
        "INSERT INTO personal.empleados "
        "(codigo_empleado, nombres, apellido_paterno, correo, "
        "unidad_organizacional_id, puesto_id, estatus) "
        "VALUES (:codigo, 'TEST', :codigo, :correo, :unidad_id, :puesto_id, 'ACTIVO')"
    ), {
        "codigo": codigo,
        "correo": f"{codigo.lower()}@dae.test",
        "unidad_id": unidad_id,
        "puesto_id": puesto_id,
    })
    return db.execute(text(
        "SELECT id FROM personal.empleados WHERE codigo_empleado = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _seed_horario_politica(db, *, sufijo="DASH"):
    db.execute(text(
        "INSERT INTO asistencia.tipos_turno "
        "(codigo, nombre, duracion_jornada_minutos, modalidad_tiempo_extra, hora_entrada_desde) "
        f"VALUES ('TURNO_{sufijo}', 'Turno', 420, 'NO_APLICA', '06:00')"
    ))
    tipo_turno_id = db.execute(text(
        "SELECT id FROM asistencia.tipos_turno WHERE codigo = :c"
    ), {"c": f"TURNO_{sufijo}"}).scalar_one()

    db.execute(text(
        "INSERT INTO asistencia.horarios "
        "(codigo, nombre, tipo_turno_id, hora_entrada, hora_salida, tolerancia_entrada_minutos) "
        f"VALUES ('HORARIO_{sufijo}', 'Horario', :tid, '08:00', '15:00', 10)"
    ), {"tid": tipo_turno_id})
    horario_id = db.execute(text(
        "SELECT id FROM asistencia.horarios WHERE codigo = :c"
    ), {"c": f"HORARIO_{sufijo}"}).scalar_one()

    db.execute(text(
        "INSERT INTO asistencia.politicas_asistencia "
        "(codigo, version, nombre, tipo_periodo, limite_tolerancia_segundos, "
        "limite_retardo_menor_segundos, limite_retardo_mayor_segundos, "
        "puntos_retardo_menor, puntos_retardo_mayor, puntos_para_descanso, "
        "max_dias_justificables_periodo, max_puntos_descontables_por_dia, "
        "descansos_para_revision_baja, faltas_consecutivas_revision_baja, "
        "vigencia_desde, activo) "
        f"VALUES ('POLITICA_{sufijo}', 1, 'Politica', 'QUINCENAL', 659, 1259, "
        "1859, 1, 2, 10, 2, 2, 7, 3, '2026-01-01', TRUE)"
    ))
    politica_id = db.execute(text(
        "SELECT id FROM asistencia.politicas_asistencia WHERE codigo = :c"
    ), {"c": f"POLITICA_{sufijo}"}).scalar_one()

    return horario_id, politica_id


def _crear_asistencia_diaria(
    db, *, empleado_id, horario_id, politica_id, fecha,
    estatus="COMPLETO", requiere_revision=False,
):
    db.execute(text(
        "INSERT INTO asistencia.asistencias_diarias "
        "(empleado_id, politica_asistencia_id, horario_id, fecha, "
        "estatus, procesada, requiere_revision, fecha_procesamiento) "
        "VALUES (:empleado_id, :politica_id, :horario_id, :fecha, "
        ":estatus, TRUE, :requiere_revision, CURRENT_TIMESTAMP)"
    ), {
        "empleado_id": empleado_id,
        "politica_id": politica_id,
        "horario_id": horario_id,
        "fecha": fecha,
        "estatus": estatus,
        "requiere_revision": requiere_revision,
    })


def _crear_modulo(db, codigo):
    db.execute(text(
        "INSERT INTO seguridad.modulos (codigo, nombre, activo) "
        "VALUES (:codigo, :codigo, TRUE) ON CONFLICT (codigo) DO NOTHING"
    ), {"codigo": codigo})
    return db.execute(text(
        "SELECT id FROM seguridad.modulos WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_rol_dashboard(db, *, codigo, alcance):
    db.execute(text(
        "INSERT INTO seguridad.roles (codigo, nombre, activo) VALUES (:codigo, :codigo, TRUE)"
    ), {"codigo": codigo})
    rol_id = db.execute(text(
        "SELECT id FROM seguridad.roles WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()
    modulo_id = _crear_modulo(db, "DASHBOARD")
    db.execute(text(
        "INSERT INTO seguridad.permisos_rol "
        "(rol_id, modulo_id, alcance_datos, puede_consultar, puede_crear, "
        "puede_editar, puede_eliminar, puede_aprobar, puede_exportar) "
        "VALUES (:rol_id, :modulo_id, :alcance, TRUE, FALSE, FALSE, FALSE, FALSE, TRUE)"
    ), {"rol_id": rol_id, "modulo_id": modulo_id, "alcance": alcance})
    return rol_id


def _crear_usuario_http(db, *, rol_id, correo, empleado_id=None):
    db.execute(text(
        "INSERT INTO seguridad.usuarios "
        "(empleado_id, rol_id, correo, correo_electronico, estatus) "
        "VALUES (:empleado_id, :rol_id, :correo, :correo, 'ACTIVO')"
    ), {"empleado_id": empleado_id, "rol_id": rol_id, "correo": correo})
    return db.execute(text(
        "SELECT id FROM seguridad.usuarios WHERE correo_electronico = :correo"
    ), {"correo": correo}).scalar_one()


def _asignar_unidad_http(db, usuario_id, unidad_id, incluye_descendientes=True):
    db.execute(text(
        "INSERT INTO seguridad.usuarios_unidades "
        "(usuario_id, unidad_organizacional_id, incluye_descendientes, activo) "
        "VALUES (:usuario_id, :unidad_id, :incluye, TRUE)"
    ), {"usuario_id": usuario_id, "unidad_id": unidad_id, "incluye": incluye_descendientes})


def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestDashboardDepartamentos:
    def test_no_mezcla_direccion_division_con_departamento(self, db_motor, api_client):
        tipos = _crear_tipo_unidad_ids(db_motor)
        direccion_id = _crear_unidad(db_motor, codigo="DIR_DASH", tipo_id=tipos["DIRECCION"])
        division_id = _crear_unidad(db_motor, codigo="DIV_DASH", tipo_id=tipos["DIVISION"], padre_id=direccion_id)
        departamento_id = _crear_unidad(db_motor, codigo="DEP_DASH", tipo_id=tipos["DEPARTAMENTO"], padre_id=division_id)
        puesto_id = _crear_puesto(db_motor)
        horario_id, politica_id = _seed_horario_politica(db_motor, sufijo="DEPTDASH")

        emp_departamento = _crear_empleado(db_motor, codigo="EMP-DASH-DEPTO", unidad_id=departamento_id, puesto_id=puesto_id)
        emp_division = _crear_empleado(db_motor, codigo="EMP-DASH-DIV", unidad_id=division_id, puesto_id=puesto_id)

        fecha = HOY - timedelta(days=5)
        _crear_asistencia_diaria(db_motor, empleado_id=emp_departamento, horario_id=horario_id, politica_id=politica_id, fecha=fecha, estatus="FALTA")
        _crear_asistencia_diaria(db_motor, empleado_id=emp_division, horario_id=horario_id, politica_id=politica_id, fecha=fecha, estatus="FALTA")

        rol_id = _crear_rol_dashboard(db_motor, codigo="ROL_DASH_TOTAL", alcance="TOTAL")
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="dash_total@dae.test")
        db_motor.commit()

        resp = api_client.get("/api/v1/dashboard/resumen", headers=_auth_headers(usuario_id))
        assert resp.status_code == 200, resp.text

        departamentos = resp.json()["departamentos_incidencias"]
        nombres = {d["departamento_nombre"] for d in departamentos}

        assert "DEP_DASH" in nombres
        assert "DIV_DASH" not in nombres
        assert "DIR_DASH" not in nombres

        sin_departamento = [d for d in departamentos if d["unidad_organizacional_id"] is None]
        assert len(sin_departamento) == 1
        assert sin_departamento[0]["empleados_involucrados"] == 1

        depto_row = next(d for d in departamentos if d["unidad_organizacional_id"] == departamento_id)
        assert depto_row["empleados_involucrados"] == 1


@pytest.mark.integration
class TestDashboardAsistenciaHoy:
    def test_incluye_todos_los_estatus_y_no_contamina_denominador(self, db_motor, api_client):
        tipos = _crear_tipo_unidad_ids(db_motor)
        unidad_id = _crear_unidad(db_motor, codigo="UO_DASH_HOY", tipo_id=tipos["DEPARTAMENTO"])
        puesto_id = _crear_puesto(db_motor)
        horario_id, politica_id = _seed_horario_politica(db_motor, sufijo="HOY")

        estatus_lista = [
            "COMPLETO", "TOLERANCIA", "RETARDO_MENOR", "RETARDO_MAYOR",
            "FALTA", "OMISION_ENTRADA", "OMISION_SALIDA", "DIA_NO_LABORAL",
        ]
        for i, estatus in enumerate(estatus_lista):
            emp_id = _crear_empleado(db_motor, codigo=f"EMP-HOY-{i}", unidad_id=unidad_id, puesto_id=puesto_id)
            _crear_asistencia_diaria(
                db_motor, empleado_id=emp_id, horario_id=horario_id,
                politica_id=politica_id, fecha=HOY, estatus=estatus,
                requiere_revision=(estatus == "FALTA"),
            )

        rol_id = _crear_rol_dashboard(db_motor, codigo="ROL_DASH_HOY", alcance="TOTAL")
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="dash_hoy@dae.test")
        db_motor.commit()

        resp = api_client.get("/api/v1/dashboard/resumen", headers=_auth_headers(usuario_id))
        assert resp.status_code == 200, resp.text

        hoy = resp.json()["asistencia_hoy"]
        assert hoy["total"] == 8
        assert hoy["completos"] == 1
        assert hoy["tolerancias"] == 1
        assert hoy["retardos_menores"] == 1
        assert hoy["retardos_mayores"] == 1
        assert hoy["faltas"] == 1
        assert hoy["omisiones_entrada"] == 1
        assert hoy["omisiones_salida"] == 1
        assert hoy["dias_no_laborales"] == 1
        assert hoy["requieren_revision"] == 1

        # dias_laborables = 8 - 1 (DIA_NO_LABORAL) = 7
        # pct_puntualidad = completos / dias_laborables = 1/7 = 14.3%
        # (si el denominador incluyera el día no laboral daría 12.5%)
        assert hoy["pct_puntualidad"] == pytest.approx(14.3, abs=0.1)

    def test_dia_totalmente_no_laboral_no_reporta_cero_puntualidad_enganosamente(self, db_motor, api_client):
        tipos = _crear_tipo_unidad_ids(db_motor)
        unidad_id = _crear_unidad(db_motor, codigo="UO_DASH_FERIADO", tipo_id=tipos["DEPARTAMENTO"])
        puesto_id = _crear_puesto(db_motor)
        horario_id, politica_id = _seed_horario_politica(db_motor, sufijo="FERIADO")

        emp_id = _crear_empleado(db_motor, codigo="EMP-FERIADO", unidad_id=unidad_id, puesto_id=puesto_id)
        _crear_asistencia_diaria(
            db_motor, empleado_id=emp_id, horario_id=horario_id,
            politica_id=politica_id, fecha=HOY, estatus="DIA_NO_LABORAL",
        )

        rol_id = _crear_rol_dashboard(db_motor, codigo="ROL_DASH_FERIADO", alcance="TOTAL")
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="dash_feriado@dae.test")
        db_motor.commit()

        resp = api_client.get("/api/v1/dashboard/resumen", headers=_auth_headers(usuario_id))
        assert resp.status_code == 200, resp.text

        hoy = resp.json()["asistencia_hoy"]
        assert hoy["total"] == 1
        assert hoy["dias_no_laborales"] == 1
        # dias_laborables = 0 -> el guard evita división por cero y no
        # reporta 0% como si fuera una caída de puntualidad real.
        assert hoy["pct_puntualidad"] == 0
        assert hoy["pct_asistencia"] == 0


@pytest.mark.integration
class TestDashboardScopesHTTP:
    def _seed_dos_areas(self, db):
        tipos = _crear_tipo_unidad_ids(db)
        unidad_propia = _crear_unidad(db, codigo="UO_DASH_PROPIA", tipo_id=tipos["DEPARTAMENTO"])
        unidad_ajena = _crear_unidad(db, codigo="UO_DASH_AJENA", tipo_id=tipos["DEPARTAMENTO"])
        puesto_id = _crear_puesto(db)
        horario_id, politica_id = _seed_horario_politica(db, sufijo="SCOPE")

        emp_propio = _crear_empleado(db, codigo="EMP-DASH-PROPIA", unidad_id=unidad_propia, puesto_id=puesto_id)
        emp_ajeno = _crear_empleado(db, codigo="EMP-DASH-AJENA", unidad_id=unidad_ajena, puesto_id=puesto_id)

        _crear_asistencia_diaria(db, empleado_id=emp_propio, horario_id=horario_id, politica_id=politica_id, fecha=HOY, estatus="FALTA")
        _crear_asistencia_diaria(db, empleado_id=emp_ajeno, horario_id=horario_id, politica_id=politica_id, fecha=HOY, estatus="FALTA")

        return unidad_propia, emp_propio

    def test_area_solo_ve_su_unidad(self, db_motor, api_client):
        unidad_propia, _ = self._seed_dos_areas(db_motor)

        rol_id = _crear_rol_dashboard(db_motor, codigo="ROL_DASH_AREA", alcance="AREA")
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="dash_area@dae.test")
        _asignar_unidad_http(db_motor, usuario_id, unidad_propia)
        db_motor.commit()

        resp = api_client.get("/api/v1/dashboard/resumen", headers=_auth_headers(usuario_id))
        assert resp.status_code == 200, resp.text
        assert resp.json()["asistencia_hoy"]["faltas"] == 1

    def test_propio_solo_ve_su_propio_registro(self, db_motor, api_client):
        _, emp_propio = self._seed_dos_areas(db_motor)

        rol_id = _crear_rol_dashboard(db_motor, codigo="ROL_DASH_PROPIO", alcance="PROPIO")
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="dash_propio@dae.test", empleado_id=emp_propio)
        db_motor.commit()

        resp = api_client.get("/api/v1/dashboard/resumen", headers=_auth_headers(usuario_id))
        assert resp.status_code == 200, resp.text
        assert resp.json()["asistencia_hoy"]["faltas"] == 1
        assert resp.json()["asistencia_hoy"]["total"] == 1

    def test_sin_permiso_recibe_403(self, db_motor, api_client):
        rol_id = db_motor.execute(text(
            "INSERT INTO seguridad.roles (codigo, nombre, activo) "
            "VALUES ('ROL_SIN_DASHBOARD', 'ROL_SIN_DASHBOARD', TRUE) RETURNING id"
        )).scalar_one()
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="sindash@dae.test")
        db_motor.commit()

        resp = api_client.get("/api/v1/dashboard/resumen", headers=_auth_headers(usuario_id))
        assert resp.status_code == 403, resp.text
