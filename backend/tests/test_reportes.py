"""
Tests del módulo de Reportes:

- reporte por empleado (fuente real, todos los estatus, requiere_revision,
  rango de fechas);
- reporte por departamento (jerarquía organizacional real, sin mezclar
  Dirección/División con Departamento, filtro por fecha, detalle de
  empleados);
- scopes de autorización (TOTAL/AREA/PROPIO/LECTURA) aplicados a JSON,
  CSV y PDF;
- configuración institucional real (branding) sin hardcodear una
  institución específica en los generadores;
- exportación CSV.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text

from app.core.security import create_access_token
from app.repositories.reportes_repo import (
    obtener_reporte_departamental,
    obtener_reporte_empleado,
)
from app.services import institucion_config
from app.services.reportes_export_service import (
    generar_csv_reporte_departamental,
    generar_csv_reporte_empleado,
    generar_pdf_reporte_departamental,
)


FECHA_A = date(2026, 3, 2)
FECHA_B = date(2026, 3, 3)
FECHA_C = date(2026, 3, 4)


# ============================================================
# Configuración institucional real (branding) — sin BD
# ============================================================


@pytest.mark.unit
class TestConfiguracionInstitucional:
    def test_defaults_neutros_sin_configuracion(self, tmp_path, monkeypatch):
        monkeypatch.setattr(institucion_config, "BRANDING_DIR", tmp_path)
        monkeypatch.setattr(institucion_config, "CONFIG_PATH", tmp_path / "config.json")

        config = institucion_config.obtener_configuracion_institucional()

        assert config["nombre_institucion"] == "Institución"
        assert config["nombre_corto"] == ""
        assert config["pie_pagina"] == ""

    def test_guardar_y_releer_configuracion(self, tmp_path, monkeypatch):
        monkeypatch.setattr(institucion_config, "BRANDING_DIR", tmp_path)
        monkeypatch.setattr(institucion_config, "CONFIG_PATH", tmp_path / "config.json")

        guardado = institucion_config.guardar_configuracion_institucional(
            nombre_institucion="Universidad de Prueba",
            nombre_corto="UDP",
            pie_pagina="Documento oficial UDP",
        )
        assert guardado["nombre_institucion"] == "Universidad de Prueba"

        releido = institucion_config.obtener_configuracion_institucional()
        assert releido == guardado

    def test_guardar_rechaza_nombre_vacio(self, tmp_path, monkeypatch):
        monkeypatch.setattr(institucion_config, "BRANDING_DIR", tmp_path)
        monkeypatch.setattr(institucion_config, "CONFIG_PATH", tmp_path / "config.json")

        with pytest.raises(ValueError):
            institucion_config.guardar_configuracion_institucional(
                nombre_institucion="   ",
                nombre_corto="X",
                pie_pagina="",
            )

    def test_logo_path_ausente_es_fallback_neutro(self, tmp_path, monkeypatch):
        monkeypatch.setattr(institucion_config, "BRANDING_DIR", tmp_path)

        assert institucion_config.obtener_logo_path() is None

    def test_logo_path_presente_se_resuelve(self, tmp_path, monkeypatch):
        monkeypatch.setattr(institucion_config, "BRANDING_DIR", tmp_path)
        logo_file = tmp_path / "logo.png"
        logo_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        assert institucion_config.obtener_logo_path() == logo_file


@pytest.mark.unit
class TestGeneradoresPdfSinInstitucionHardcodeada:
    """
    Contrato explícito de la tarea: 'no hardcodear IPN/DAE en el
    generador'. Se verifica sobre el código fuente porque el texto de
    un PDF generado puede no ser recuperable por búsqueda de substring
    (streams comprimidos), pero el requisito es sobre el código, no
    sobre el binario.
    """

    def _leer_fuente(self, modulo) -> str:
        import inspect

        return inspect.getsource(modulo)

    def test_reporte_pdf_service_no_hardcodea_institucion(self):
        from app.services import reporte_pdf_service

        fuente = self._leer_fuente(reporte_pdf_service)
        prohibidos = [
            "Instituto Politécnico",
            "Instituto Politecnico",
            "Dirección de Administración Escolar",
            "Direccion de Administracion Escolar",
        ]
        for texto in prohibidos:
            assert texto not in fuente, (
                f"'{texto}' sigue hardcodeado en reporte_pdf_service.py"
            )

    def test_reportes_export_service_no_hardcodea_institucion(self):
        from app.services import reportes_export_service

        fuente = self._leer_fuente(reportes_export_service)
        prohibidos = [
            "Instituto Politécnico",
            "Instituto Politecnico",
            "Dirección de Administración Escolar",
            "Direccion de Administracion Escolar",
        ]
        for texto in prohibidos:
            assert texto not in fuente, (
                f"'{texto}' sigue hardcodeado en reportes_export_service.py"
            )


# ============================================================
# Helpers de seed — organización, empleados, política/horario,
# asistencias diarias
# ============================================================


def _crear_tipo_unidad_ids(db) -> dict[str, int]:
    rows = db.execute(text(
        "SELECT codigo, id FROM organizacion.tipos_unidad"
    )).all()
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


def _crear_puesto(db, codigo="PUESTO_REP"):
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


def _seed_horario_politica(db, *, sufijo="REP"):
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
    minutos_retardo=0, minutos_ordinarios=420, minutos_extra=0,
    puntos_generados=0,
):
    db.execute(text(
        "INSERT INTO asistencia.asistencias_diarias "
        "(empleado_id, politica_asistencia_id, horario_id, fecha, "
        "estatus, procesada, requiere_revision, fecha_procesamiento, "
        "minutos_retardo, minutos_ordinarios, minutos_extra, puntos_generados) "
        "VALUES (:empleado_id, :politica_id, :horario_id, :fecha, "
        ":estatus, TRUE, :requiere_revision, CURRENT_TIMESTAMP, "
        ":minutos_retardo, :minutos_ordinarios, :minutos_extra, :puntos_generados)"
    ), {
        "empleado_id": empleado_id,
        "politica_id": politica_id,
        "horario_id": horario_id,
        "fecha": fecha,
        "estatus": estatus,
        "requiere_revision": requiere_revision,
        "minutos_retardo": minutos_retardo,
        "minutos_ordinarios": minutos_ordinarios,
        "minutos_extra": minutos_extra,
        "puntos_generados": puntos_generados,
    })


class _ScopeTotal:
    data_scope = "TOTAL"
    employee_id = None
    allowed_unit_ids = ()

    def allows(self, action):
        return True


def _scope_propio(employee_id: int):
    class _Scope:
        data_scope = "PROPIO"
        allowed_unit_ids = ()

        def allows(self, action):
            return True

    scope = _Scope()
    scope.employee_id = employee_id
    return scope


# ============================================================
# Reporte por empleado — fuente real, estatus, requiere_revision,
# rango de fechas
# ============================================================


@pytest.mark.integration
class TestReporteEmpleado:
    def test_incluye_todos_los_estatus_y_requiere_revision(self, db_session):
        tipos = _crear_tipo_unidad_ids(db_session)
        unidad_id = _crear_unidad(db_session, codigo="UO_EMP", tipo_id=tipos["DEPARTAMENTO"])
        puesto_id = _crear_puesto(db_session)
        empleado_id = _crear_empleado(db_session, codigo="EMP-REP-01", unidad_id=unidad_id, puesto_id=puesto_id)
        horario_id, politica_id = _seed_horario_politica(db_session, sufijo="EMP1")

        estatus_esperados = [
            "COMPLETO", "TOLERANCIA", "RETARDO_MENOR", "RETARDO_MAYOR",
            "FALTA", "OMISION_ENTRADA", "OMISION_SALIDA", "DIA_NO_LABORAL",
        ]
        fecha_base = date(2026, 3, 1)
        for i, estatus in enumerate(estatus_esperados):
            _crear_asistencia_diaria(
                db_session,
                empleado_id=empleado_id,
                horario_id=horario_id,
                politica_id=politica_id,
                fecha=fecha_base.replace(day=1 + i),
                estatus=estatus,
                requiere_revision=(estatus == "OMISION_ENTRADA"),
            )
        db_session.flush()

        data = obtener_reporte_empleado(
            db=db_session,
            codigo_empleado="EMP-REP-01",
            fecha_inicio=fecha_base,
            fecha_fin=fecha_base.replace(day=1 + len(estatus_esperados)),
            access_scope=_ScopeTotal(),
        )

        assert data is not None
        assert {d["estatus"] for d in data["dias"]} == set(estatus_esperados)

        dia_omision_entrada = next(
            d for d in data["dias"] if d["estatus"] == "OMISION_ENTRADA"
        )
        assert dia_omision_entrada["requiere_revision"] is True

        resumen = data["resumen"]
        assert resumen["dias_completos"] == 1
        assert resumen["tolerancias"] == 1
        assert resumen["retardos_menores"] == 1
        assert resumen["retardos_mayores"] == 1
        assert resumen["faltas"] == 1
        assert resumen["omisiones_entrada"] == 1
        assert resumen["omisiones_salida"] == 1
        assert resumen["dias_no_laborales"] == 1
        assert resumen["dias_requieren_revision"] == 1

    def test_respeta_rango_de_fechas(self, db_session):
        tipos = _crear_tipo_unidad_ids(db_session)
        unidad_id = _crear_unidad(db_session, codigo="UO_EMP2", tipo_id=tipos["DEPARTAMENTO"])
        puesto_id = _crear_puesto(db_session)
        empleado_id = _crear_empleado(db_session, codigo="EMP-REP-02", unidad_id=unidad_id, puesto_id=puesto_id)
        horario_id, politica_id = _seed_horario_politica(db_session, sufijo="EMP2")

        _crear_asistencia_diaria(
            db_session, empleado_id=empleado_id, horario_id=horario_id,
            politica_id=politica_id, fecha=date(2026, 3, 1), estatus="COMPLETO",
        )
        _crear_asistencia_diaria(
            db_session, empleado_id=empleado_id, horario_id=horario_id,
            politica_id=politica_id, fecha=date(2026, 3, 15), estatus="FALTA",
        )
        db_session.flush()

        data = obtener_reporte_empleado(
            db=db_session,
            codigo_empleado="EMP-REP-02",
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 3, 5),
            access_scope=_ScopeTotal(),
        )

        assert len(data["dias"]) == 1
        assert data["dias"][0]["fecha"] == date(2026, 3, 1)

    def test_scope_propio_no_ve_otro_empleado(self, db_session):
        tipos = _crear_tipo_unidad_ids(db_session)
        unidad_id = _crear_unidad(db_session, codigo="UO_EMP3", tipo_id=tipos["DEPARTAMENTO"])
        puesto_id = _crear_puesto(db_session)
        propio_id = _crear_empleado(db_session, codigo="EMP-PROPIO-REP", unidad_id=unidad_id, puesto_id=puesto_id)
        otro_id = _crear_empleado(db_session, codigo="EMP-OTRO-REP", unidad_id=unidad_id, puesto_id=puesto_id)

        data_propio = obtener_reporte_empleado(
            db=db_session, codigo_empleado="EMP-PROPIO-REP",
            fecha_inicio=FECHA_A, fecha_fin=FECHA_C,
            access_scope=_scope_propio(propio_id),
        )
        assert data_propio is not None

        data_otro = obtener_reporte_empleado(
            db=db_session, codigo_empleado="EMP-OTRO-REP",
            fecha_inicio=FECHA_A, fecha_fin=FECHA_C,
            access_scope=_scope_propio(propio_id),
        )
        assert data_otro is None


# ============================================================
# Reporte por departamento — jerarquía organizacional real
# ============================================================


@pytest.mark.integration
class TestReporteDepartamental:
    def _seed_jerarquia(self, db):
        tipos = _crear_tipo_unidad_ids(db)
        direccion_id = _crear_unidad(db, codigo="DIR_TEST", tipo_id=tipos["DIRECCION"])
        division_id = _crear_unidad(db, codigo="DIV_TEST", tipo_id=tipos["DIVISION"], padre_id=direccion_id)
        departamento_id = _crear_unidad(
            db, codigo="DEP_TEST", tipo_id=tipos["DEPARTAMENTO"], padre_id=division_id
        )
        return direccion_id, division_id, departamento_id

    def test_no_mezcla_direccion_division_con_departamento(self, db_session):
        direccion_id, division_id, departamento_id = self._seed_jerarquia(db_session)
        puesto_id = _crear_puesto(db_session)
        horario_id, politica_id = _seed_horario_politica(db_session, sufijo="DEPT1")

        emp_departamento = _crear_empleado(
            db_session, codigo="EMP-DEPTO", unidad_id=departamento_id, puesto_id=puesto_id
        )
        emp_division = _crear_empleado(
            db_session, codigo="EMP-DIVISION", unidad_id=division_id, puesto_id=puesto_id
        )

        _crear_asistencia_diaria(
            db_session, empleado_id=emp_departamento, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_A, estatus="COMPLETO",
        )
        _crear_asistencia_diaria(
            db_session, empleado_id=emp_division, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_A, estatus="COMPLETO",
        )
        db_session.flush()

        data = obtener_reporte_departamental(
            db=db_session, fecha_inicio=FECHA_A, fecha_fin=FECHA_A,
            access_scope=_ScopeTotal(),
        )

        nombres_departamentos = {d["unidad_nombre"] for d in data["departamentos"]}
        assert "DEP_TEST" in nombres_departamentos
        assert "DIV_TEST" not in nombres_departamentos
        assert "DIR_TEST" not in nombres_departamentos

        # El empleado asignado directamente a la División cae en el
        # grupo "sin departamento" (unidad_id/nombre None), nunca
        # etiquetado bajo el nombre de la División.
        sin_departamento = [d for d in data["departamentos"] if d["unidad_id"] is None]
        assert len(sin_departamento) == 1
        assert sin_departamento[0]["total_empleados"] == 1

        depto_row = next(d for d in data["departamentos"] if d["unidad_id"] == departamento_id)
        assert depto_row["total_empleados"] == 1

    def test_filtro_por_fecha(self, db_session):
        _, _, departamento_id = self._seed_jerarquia(db_session)
        puesto_id = _crear_puesto(db_session)
        horario_id, politica_id = _seed_horario_politica(db_session, sufijo="DEPT2")
        empleado_id = _crear_empleado(
            db_session, codigo="EMP-DEPTO-FECHA", unidad_id=departamento_id, puesto_id=puesto_id
        )

        _crear_asistencia_diaria(
            db_session, empleado_id=empleado_id, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_A, estatus="FALTA",
        )
        _crear_asistencia_diaria(
            db_session, empleado_id=empleado_id, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_C, estatus="COMPLETO",
        )
        db_session.flush()

        data = obtener_reporte_departamental(
            db=db_session, fecha_inicio=FECHA_A, fecha_fin=FECHA_A,
            access_scope=_ScopeTotal(),
        )

        depto_row = next(d for d in data["departamentos"] if d["unidad_id"] == departamento_id)
        assert depto_row["total_registros"] == 1
        assert depto_row["faltas"] == 1
        assert depto_row["dias_completos"] == 0

    def test_filtro_por_unidad_no_departamento_lanza_error(self, db_session):
        _, division_id, _ = self._seed_jerarquia(db_session)

        with pytest.raises(ValueError):
            obtener_reporte_departamental(
                db=db_session, fecha_inicio=FECHA_A, fecha_fin=FECHA_A,
                access_scope=_ScopeTotal(),
                unidad_organizacional_id=division_id,
            )

    def test_incluye_detalle_de_empleados(self, db_session):
        _, _, departamento_id = self._seed_jerarquia(db_session)
        puesto_id = _crear_puesto(db_session)
        horario_id, politica_id = _seed_horario_politica(db_session, sufijo="DEPT3")
        empleado_id = _crear_empleado(
            db_session, codigo="EMP-DEPTO-DETALLE", unidad_id=departamento_id, puesto_id=puesto_id
        )
        _crear_asistencia_diaria(
            db_session, empleado_id=empleado_id, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_A, estatus="COMPLETO",
        )
        db_session.flush()

        data = obtener_reporte_departamental(
            db=db_session, fecha_inicio=FECHA_A, fecha_fin=FECHA_A,
            access_scope=_ScopeTotal(),
        )

        assert "detalle_empleados" in data
        detalle = [e for e in data["detalle_empleados"] if e["codigo_empleado"] == "EMP-DEPTO-DETALLE"]
        assert len(detalle) == 1
        assert detalle[0]["unidad_nombre"] == "DEP_TEST"
        assert detalle[0]["dias_completos"] == 1


# ============================================================
# CSV — mismas fuentes/filtros, columnas consistentes
# ============================================================


@pytest.mark.unit
class TestExportacionCSV:
    def test_csv_empleado_incluye_requiere_revision(self):
        data = {
            "empleado": {
                "codigo_empleado": "EMP-CSV",
                "nombre_completo": "Empleado Csv",
                "puesto": "Analista",
                "unidad_organizacional": "Departamento X",
            },
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-03-01",
            "resumen": {
                "dias_periodo": 1, "dias_completos": 0, "tolerancias": 0,
                "retardos_menores": 0, "retardos_mayores": 0, "faltas": 0,
                "omisiones_entrada": 1, "omisiones_salida": 0,
                "dias_no_laborales": 0, "dias_requieren_revision": 1,
                "total_puntos": 0, "total_minutos_retardo": 0,
                "total_minutos_ordinarios": 0, "total_minutos_extra": 0,
                "porcentaje_asistencia": 0,
            },
            "dias": [{
                "fecha": date(2026, 3, 1),
                "entrada_programada": None, "salida_programada": None,
                "primera_entrada": None, "ultima_salida": None,
                "minutos_retardo": 0, "minutos_ordinarios": 0, "minutos_extra": 0,
                "estatus": "OMISION_ENTRADA", "puntos_generados": 0,
                "requiere_revision": True, "observaciones": None,
            }],
        }

        csv_text = generar_csv_reporte_empleado(data)

        assert "Requiere revisión" in csv_text
        assert "Sí" in csv_text
        assert "OMISION_ENTRADA" in csv_text

    def test_csv_departamental_incluye_detalle_empleados(self):
        data = {
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-03-01",
            "totales": {"departamentos": 1, "empleados": 1, "dias_completos": 1, "faltas": 0, "retardos": 0},
            "departamentos": [{
                "unidad_id": 1, "unidad_nombre": "DEP_TEST", "total_empleados": 1,
                "total_registros": 1, "dias_completos": 1, "tolerancias": 0,
                "retardos_menores": 0, "retardos_mayores": 0, "faltas": 0,
                "omisiones_entrada": 0, "omisiones_salida": 0, "dias_no_laborales": 0,
                "dias_requieren_revision": 0, "total_puntos": 0,
                "total_minutos_retardo": 0, "total_minutos_ordinarios": 480,
                "total_minutos_extra": 0,
            }],
            "detalle_empleados": [{
                "empleado_id": 1, "codigo_empleado": "EMP-DEPTO-DETALLE",
                "nombre_completo": "Empleado Depto", "unidad_id": 1,
                "unidad_nombre": "DEP_TEST", "total_registros": 1,
                "dias_completos": 1, "tolerancias": 0, "retardos_menores": 0,
                "retardos_mayores": 0, "faltas": 0, "omisiones_entrada": 0,
                "omisiones_salida": 0, "dias_no_laborales": 0,
                "dias_requieren_revision": 0, "total_puntos": 0,
                "total_minutos_retardo": 0, "total_minutos_ordinarios": 480,
                "total_minutos_extra": 0,
            }],
        }

        csv_text = generar_csv_reporte_departamental(data)

        assert "DETALLE POR EMPLEADO" in csv_text
        assert "EMP-DEPTO-DETALLE" in csv_text

    def test_pdf_departamental_genera_bytes_validos(self, tmp_path, monkeypatch):
        monkeypatch.setattr(institucion_config, "BRANDING_DIR", tmp_path)
        monkeypatch.setattr(institucion_config, "CONFIG_PATH", tmp_path / "config.json")

        data = {
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-03-01",
            "totales": {"departamentos": 1, "empleados": 1, "dias_completos": 1, "faltas": 0, "retardos": 0},
            "departamentos": [{
                "unidad_id": 1, "unidad_nombre": "DEP_TEST", "total_empleados": 1,
                "total_registros": 1, "dias_completos": 1, "tolerancias": 0,
                "retardos_menores": 0, "retardos_mayores": 0, "faltas": 0,
                "omisiones_entrada": 0, "omisiones_salida": 0, "dias_no_laborales": 0,
                "dias_requieren_revision": 0, "total_puntos": 0,
                "total_minutos_retardo": 0, "total_minutos_ordinarios": 480,
                "total_minutos_extra": 0,
            }],
            "detalle_empleados": [],
        }

        pdf_bytes = generar_pdf_reporte_departamental(data)

        assert pdf_bytes[:5] == b"%PDF-"


# ============================================================
# HTTP — scopes TOTAL / AREA / PROPIO / LECTURA aplicados a
# json / csv / pdf
# ============================================================


def _crear_modulo(db, codigo="REPORTES"):
    db.execute(text(
        "INSERT INTO seguridad.modulos (codigo, nombre, activo) "
        "VALUES (:codigo, :codigo, TRUE) ON CONFLICT (codigo) DO NOTHING"
    ), {"codigo": codigo})
    return db.execute(text(
        "SELECT id FROM seguridad.modulos WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_rol_reportes(db, *, codigo, alcance, puede_consultar=True, puede_exportar=True):
    db.execute(text(
        "INSERT INTO seguridad.roles (codigo, nombre, activo) VALUES (:codigo, :codigo, TRUE)"
    ), {"codigo": codigo})
    rol_id = db.execute(text(
        "SELECT id FROM seguridad.roles WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()
    modulo_id = _crear_modulo(db)
    db.execute(text(
        "INSERT INTO seguridad.permisos_rol "
        "(rol_id, modulo_id, alcance_datos, puede_consultar, puede_crear, "
        "puede_editar, puede_eliminar, puede_aprobar, puede_exportar) "
        "VALUES (:rol_id, :modulo_id, :alcance, :consultar, FALSE, FALSE, FALSE, FALSE, :exportar)"
    ), {
        "rol_id": rol_id, "modulo_id": modulo_id, "alcance": alcance,
        "consultar": puede_consultar, "exportar": puede_exportar,
    })
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
class TestReportesScopesHTTP:
    def _seed_base(self, db):
        tipos = _crear_tipo_unidad_ids(db)
        unidad_id = _crear_unidad(db, codigo="UO_HTTP_REP", tipo_id=tipos["DEPARTAMENTO"])
        puesto_id = _crear_puesto(db)
        horario_id, politica_id = _seed_horario_politica(db, sufijo="HTTP1")
        empleado_id = _crear_empleado(db, codigo="EMP-HTTP-REP", unidad_id=unidad_id, puesto_id=puesto_id)
        _crear_asistencia_diaria(
            db, empleado_id=empleado_id, horario_id=horario_id,
            politica_id=politica_id, fecha=FECHA_A, estatus="COMPLETO",
        )
        return unidad_id, empleado_id

    def test_propio_ve_su_reporte_pero_no_otro(self, db_motor, api_client):
        unidad_id, empleado_id = self._seed_base(db_motor)
        puesto_id = _crear_puesto(db_motor)
        otro_id = _crear_empleado(db_motor, codigo="EMP-HTTP-OTRO", unidad_id=unidad_id, puesto_id=puesto_id)

        rol_id = _crear_rol_reportes(db_motor, codigo="ROL_REP_PROPIO", alcance="PROPIO")
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="propio_rep@dae.test", empleado_id=empleado_id)
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        resp_propio = api_client.get(
            "/api/v1/reportes/empleado/EMP-HTTP-REP",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A)},
            headers=headers,
        )
        assert resp_propio.status_code == 200, resp_propio.text

        resp_otro = api_client.get(
            "/api/v1/reportes/empleado/EMP-HTTP-OTRO",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A)},
            headers=headers,
        )
        assert resp_otro.status_code == 404, resp_otro.text

        # El PDF dedicado también debe respetar el scope (antes no lo hacía).
        resp_otro_pdf = api_client.get(
            "/api/v1/reportes/empleado/EMP-HTTP-OTRO/pdf",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A)},
            headers=headers,
        )
        assert resp_otro_pdf.status_code == 404, resp_otro_pdf.text

    def test_area_bloquea_fuera_de_su_unidad(self, db_motor, api_client):
        tipos = _crear_tipo_unidad_ids(db_motor)
        unidad_propia = _crear_unidad(db_motor, codigo="UO_AREA_PROPIA_REP", tipo_id=tipos["DEPARTAMENTO"])
        unidad_ajena = _crear_unidad(db_motor, codigo="UO_AREA_AJENA_REP", tipo_id=tipos["DEPARTAMENTO"])
        puesto_id = _crear_puesto(db_motor)
        emp_ajeno = _crear_empleado(db_motor, codigo="EMP-AREA-AJENA-REP", unidad_id=unidad_ajena, puesto_id=puesto_id)

        rol_id = _crear_rol_reportes(db_motor, codigo="ROL_REP_AREA", alcance="AREA")
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="area_rep@dae.test")
        _asignar_unidad_http(db_motor, usuario_id, unidad_propia)
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        resp = api_client.get(
            f"/api/v1/reportes/empleado/EMP-AREA-AJENA-REP",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A)},
            headers=headers,
        )
        assert resp.status_code == 404, resp.text

    def test_total_puede_consultar_y_exportar(self, db_motor, api_client):
        unidad_id, empleado_id = self._seed_base(db_motor)

        rol_id = _crear_rol_reportes(db_motor, codigo="ROL_REP_TOTAL", alcance="TOTAL")
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="total_rep@dae.test")
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        resp_json = api_client.get(
            "/api/v1/reportes/empleado/EMP-HTTP-REP",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A)},
            headers=headers,
        )
        assert resp_json.status_code == 200, resp_json.text

        resp_csv = api_client.get(
            "/api/v1/reportes/empleado/EMP-HTTP-REP",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A), "formato": "csv"},
            headers=headers,
        )
        assert resp_csv.status_code == 200, resp_csv.text
        assert resp_csv.headers["content-type"].startswith("text/csv")

        resp_dept_csv = api_client.get(
            "/api/v1/reportes/departamental",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A), "formato": "csv"},
            headers=headers,
        )
        assert resp_dept_csv.status_code == 200, resp_dept_csv.text

    def test_lectura_puede_consultar_json_pero_no_exportar(self, db_motor, api_client):
        """
        Rol 'LECTURA': alcance TOTAL, puede_consultar=True,
        puede_exportar=False. Debe poder ver el preview JSON pero no
        descargar CSV/PDF.
        """
        unidad_id, empleado_id = self._seed_base(db_motor)

        rol_id = _crear_rol_reportes(
            db_motor, codigo="ROL_REP_LECTURA", alcance="TOTAL",
            puede_consultar=True, puede_exportar=False,
        )
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="lectura_rep@dae.test")
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        resp_json = api_client.get(
            "/api/v1/reportes/empleado/EMP-HTTP-REP",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A)},
            headers=headers,
        )
        assert resp_json.status_code == 200, resp_json.text

        resp_csv = api_client.get(
            "/api/v1/reportes/empleado/EMP-HTTP-REP",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A), "formato": "csv"},
            headers=headers,
        )
        assert resp_csv.status_code == 403, resp_csv.text

        resp_pdf = api_client.get(
            "/api/v1/reportes/empleado/EMP-HTTP-REP/pdf",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A)},
            headers=headers,
        )
        assert resp_pdf.status_code == 403, resp_pdf.text

        resp_dept_json = api_client.get(
            "/api/v1/reportes/departamental",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A)},
            headers=headers,
        )
        assert resp_dept_json.status_code == 200, resp_dept_json.text

        resp_dept_pdf = api_client.get(
            "/api/v1/reportes/departamental",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A), "formato": "pdf"},
            headers=headers,
        )
        assert resp_dept_pdf.status_code == 403, resp_dept_pdf.text

    def test_sin_permiso_en_modulo_recibe_403(self, db_motor, api_client):
        rol_id = db_motor.execute(text(
            "INSERT INTO seguridad.roles (codigo, nombre, activo) "
            "VALUES ('ROL_SIN_REPORTES', 'ROL_SIN_REPORTES', TRUE) RETURNING id"
        )).scalar_one()
        usuario_id = _crear_usuario_http(db_motor, rol_id=rol_id, correo="sinreportes@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/reportes/empleado/EMP-HTTP-REP",
            params={"fecha_inicio": str(FECHA_A), "fecha_fin": str(FECHA_A)},
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 403, resp.text
