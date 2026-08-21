"""
Tests de la transición de identidad ZKTeco (Contrato §10).

Verifican que dispositivos.empleado_dispositivo sea la fuente canónica
para resolver empleado_id desde una marcación (dispositivo_origen +
zk_user_id), que personal.empleados.zk_user_id actúe únicamente como
fallback legacy temporal, y que una combinación ambigua nunca se
resuelva en silencio.
"""

from datetime import date, datetime

import pytest
from sqlalchemy import text

from app.repositories.asistencia_procesamiento_repo import (
    procesar_asistencia_diaria,
)
from app.repositories.zk_attendance_repo import insertar_marcaciones_crudas
from app.repositories.zk_employee_link_repo import (
    resolver_empleado_id_para_marcacion,
)


FECHA_TEST = date(2026, 8, 18)


# ============================================================
# Helpers de seed
# ============================================================


def _crear_unidad_y_puesto(db):
    db.execute(text(
        "INSERT INTO organizacion.unidades_organizacionales (codigo, nombre, activo) "
        "VALUES ('UNIDAD_ZK', 'Unidad ZK', TRUE)"
    ))
    db.execute(text(
        "INSERT INTO organizacion.puestos (codigo, nombre, nivel_jerarquico, activo) "
        "VALUES ('PUESTO_ZK', 'Puesto ZK', 1, TRUE)"
    ))
    unidad_id = db.execute(text(
        "SELECT id FROM organizacion.unidades_organizacionales WHERE codigo='UNIDAD_ZK'"
    )).scalar_one()
    puesto_id = db.execute(text(
        "SELECT id FROM organizacion.puestos WHERE codigo='PUESTO_ZK'"
    )).scalar_one()
    return unidad_id, puesto_id


def _crear_empleado(db, codigo, unidad_id, puesto_id, zk_user_id_legacy=None):
    db.execute(text(
        "INSERT INTO personal.empleados "
        "(codigo_empleado, nombres, apellido_paterno, unidad_organizacional_id, "
        "puesto_id, estatus, zk_user_id) "
        "VALUES (:codigo, 'TEST', 'ZK', :unidad_id, :puesto_id, 'ACTIVO', :zk_user_id)"
    ), {
        "codigo": codigo,
        "unidad_id": unidad_id,
        "puesto_id": puesto_id,
        "zk_user_id": zk_user_id_legacy,
    })
    return db.execute(text(
        "SELECT id FROM personal.empleados WHERE codigo_empleado = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_dispositivo(db, codigo, ip):
    db.execute(text(
        "INSERT INTO dispositivos.dispositivos (codigo, nombre, ip, activo) "
        "VALUES (:codigo, :codigo, :ip, TRUE)"
    ), {"codigo": codigo, "ip": ip})
    return db.execute(text(
        "SELECT id FROM dispositivos.dispositivos WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _vincular_empleado_dispositivo(db, empleado_id, dispositivo_id, zk_user_id, activo=True):
    db.execute(text(
        "INSERT INTO dispositivos.empleado_dispositivo "
        "(empleado_id, dispositivo_id, zk_user_id, activo) "
        "VALUES (:empleado_id, :dispositivo_id, :zk_user_id, :activo)"
    ), {
        "empleado_id": empleado_id,
        "dispositivo_id": dispositivo_id,
        "zk_user_id": zk_user_id,
        "activo": activo,
    })


def _insertar_marcacion_huerfana(db, dispositivo_origen, zk_user_id, fecha_hora, punch=0):
    db.execute(text(
        "INSERT INTO asistencia.marcaciones_crudas "
        "(dispositivo_origen, zk_user_id, fecha_hora, punch, punch_label, raw_payload) "
        "VALUES (:dispositivo_origen, :zk_user_id, :fecha_hora, :punch, :punch_label, '{}'::jsonb)"
    ), {
        "dispositivo_origen": dispositivo_origen,
        "zk_user_id": zk_user_id,
        "fecha_hora": fecha_hora,
        "punch": punch,
        "punch_label": "Entrada" if punch == 0 else "Salida",
    })


# ============================================================
# Tests: resolver_empleado_id_para_marcacion (unidad de resolución)
# ============================================================


@pytest.mark.integration
class TestResolucionIdentidadZK:

    def test_resolucion_canonica_por_dispositivo_y_zk_user_id(self, db_motor):
        """1. dispositivo_origen + zk_user_id resuelve correctamente vía
        dispositivos.empleado_dispositivo (fuente canónica)."""
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(db_motor, "EMP-ZK-01", unidad_id, puesto_id)
        dispositivo_id = _crear_dispositivo(db_motor, "ZK_A", "10.0.0.1")
        _vincular_empleado_dispositivo(db_motor, empleado_id, dispositivo_id, "501")
        db_motor.commit()

        resultado = resolver_empleado_id_para_marcacion(
            db=db_motor, dispositivo_origen="ZK_A", zk_user_id="501"
        )

        assert resultado["empleado_id"] == empleado_id
        assert resultado["fuente"] == "CANONICA"
        assert resultado["conflicto"] is False

    def test_mismo_zk_user_id_en_dos_dispositivos_distintos(self, db_motor):
        """2. El mismo zk_user_id usado en dos dispositivos distintos, para
        DOS empleados distintos, se resuelve correctamente por dispositivo
        (no es ambiguo porque cada marcación trae su propio
        dispositivo_origen)."""
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_a = _crear_empleado(db_motor, "EMP-ZK-A", unidad_id, puesto_id)
        empleado_b = _crear_empleado(db_motor, "EMP-ZK-B", unidad_id, puesto_id)
        dispositivo_a = _crear_dispositivo(db_motor, "ZK_A2", "10.0.0.2")
        dispositivo_b = _crear_dispositivo(db_motor, "ZK_B2", "10.0.0.3")
        _vincular_empleado_dispositivo(db_motor, empleado_a, dispositivo_a, "77")
        _vincular_empleado_dispositivo(db_motor, empleado_b, dispositivo_b, "77")
        db_motor.commit()

        resultado_a = resolver_empleado_id_para_marcacion(
            db=db_motor, dispositivo_origen="ZK_A2", zk_user_id="77"
        )
        resultado_b = resolver_empleado_id_para_marcacion(
            db=db_motor, dispositivo_origen="ZK_B2", zk_user_id="77"
        )

        assert resultado_a["empleado_id"] == empleado_a
        assert resultado_a["conflicto"] is False
        assert resultado_b["empleado_id"] == empleado_b
        assert resultado_b["conflicto"] is False

    def test_empleado_con_distinto_zk_user_id_por_dispositivo(self, db_motor):
        """3. Un mismo empleado con distinto zk_user_id en cada
        dispositivo se resuelve correctamente en ambos casos."""
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(db_motor, "EMP-ZK-MULTI", unidad_id, puesto_id)
        dispositivo_x = _crear_dispositivo(db_motor, "ZK_X", "10.0.0.4")
        dispositivo_y = _crear_dispositivo(db_motor, "ZK_Y", "10.0.0.5")
        _vincular_empleado_dispositivo(db_motor, empleado_id, dispositivo_x, "10")
        _vincular_empleado_dispositivo(db_motor, empleado_id, dispositivo_y, "20")
        db_motor.commit()

        resultado_x = resolver_empleado_id_para_marcacion(
            db=db_motor, dispositivo_origen="ZK_X", zk_user_id="10"
        )
        resultado_y = resolver_empleado_id_para_marcacion(
            db=db_motor, dispositivo_origen="ZK_Y", zk_user_id="20"
        )

        assert resultado_x["empleado_id"] == empleado_id
        assert resultado_y["empleado_id"] == empleado_id
        assert resultado_x["conflicto"] is False
        assert resultado_y["conflicto"] is False

    def test_fallback_a_campo_legacy(self, db_motor):
        """4. Sin relación resoluble en empleado_dispositivo, se usa
        personal.empleados.zk_user_id como fallback legacy."""
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(
            db_motor, "EMP-ZK-LEGACY", unidad_id, puesto_id, zk_user_id_legacy="999"
        )
        db_motor.commit()

        resultado = resolver_empleado_id_para_marcacion(
            db=db_motor, dispositivo_origen="ZK_DESCONOCIDO", zk_user_id="999"
        )

        assert resultado["empleado_id"] == empleado_id
        assert resultado["fuente"] == "LEGACY"
        assert resultado["conflicto"] is False

    def test_conflicto_ambiguo_no_se_resuelve_silenciosamente(self, db_motor):
        """5. Si el dispositivo no se identifica y el mismo zk_user_id
        está activo para más de un empleado en dispositivos distintos, no
        se elige ninguno: se reporta como conflicto explícito."""
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_a = _crear_empleado(db_motor, "EMP-ZK-CONF-A", unidad_id, puesto_id)
        empleado_b = _crear_empleado(db_motor, "EMP-ZK-CONF-B", unidad_id, puesto_id)
        dispositivo_a = _crear_dispositivo(db_motor, "ZK_CONF_A", "10.0.0.6")
        dispositivo_b = _crear_dispositivo(db_motor, "ZK_CONF_B", "10.0.0.7")
        _vincular_empleado_dispositivo(db_motor, empleado_a, dispositivo_a, "42")
        _vincular_empleado_dispositivo(db_motor, empleado_b, dispositivo_b, "42")
        db_motor.commit()

        resultado = resolver_empleado_id_para_marcacion(
            db=db_motor, dispositivo_origen="ZK_NO_EXISTE", zk_user_id="42"
        )

        assert resultado["empleado_id"] is None
        assert resultado["conflicto"] is True
        assert resultado["detalle"] is not None
        assert "42" in resultado["detalle"]

    def test_relacion_inactiva_no_se_usa_como_canonica(self, db_motor):
        """Una relación desactivada (activo=FALSE) no debe resolverse como
        canónica; debe caer al fallback legacy si existe, o quedar sin
        resolver."""
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(db_motor, "EMP-ZK-INACTIVO", unidad_id, puesto_id)
        dispositivo_id = _crear_dispositivo(db_motor, "ZK_INACTIVO", "10.0.0.8")
        _vincular_empleado_dispositivo(
            db_motor, empleado_id, dispositivo_id, "33", activo=False
        )
        db_motor.commit()

        resultado = resolver_empleado_id_para_marcacion(
            db=db_motor, dispositivo_origen="ZK_INACTIVO", zk_user_id="33"
        )

        assert resultado["fuente"] != "CANONICA"
        assert resultado["conflicto"] is False


# ============================================================
# Tests de integración: descarga de marcaciones
# ============================================================


@pytest.mark.integration
class TestDescargaMarcacionesIdentidadCanonica:

    def test_descarga_resuelve_por_dispositivo_canonico(self, db_motor):
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(db_motor, "EMP-DESC-01", unidad_id, puesto_id)
        dispositivo_id = _crear_dispositivo(db_motor, "ZK_DESC", "10.0.1.1")
        _vincular_empleado_dispositivo(db_motor, empleado_id, dispositivo_id, "601")
        db_motor.commit()

        resultado = insertar_marcaciones_crudas(
            db=db_motor,
            records=[{
                "user_id": "601",
                "timestamp": "2026-08-18T08:00:00",
                "uid": 1,
                "punch": 0,
                "punch_label": "Entrada",
                "status": 0,
                "status_label": "OK",
            }],
            sync_run_id="TEST-RUN-1",
            dispositivo_ip="10.0.1.1",
            dispositivo_origen="ZK_DESC",
        )

        assert resultado["insertadas"] == 1
        assert resultado["conflictos"] == []

        fila = db_motor.execute(text(
            "SELECT empleado_id FROM asistencia.marcaciones_crudas "
            "WHERE dispositivo_origen = 'ZK_DESC' AND zk_user_id = '601'"
        )).mappings().first()
        assert fila["empleado_id"] == empleado_id

    def test_descarga_reporta_conflicto_sin_asignar_empleado(self, db_motor):
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_a = _crear_empleado(db_motor, "EMP-DESC-CONF-A", unidad_id, puesto_id)
        empleado_b = _crear_empleado(db_motor, "EMP-DESC-CONF-B", unidad_id, puesto_id)
        dispositivo_a = _crear_dispositivo(db_motor, "ZK_DESC_A", "10.0.1.2")
        dispositivo_b = _crear_dispositivo(db_motor, "ZK_DESC_B", "10.0.1.3")
        _vincular_empleado_dispositivo(db_motor, empleado_a, dispositivo_a, "88")
        _vincular_empleado_dispositivo(db_motor, empleado_b, dispositivo_b, "88")
        db_motor.commit()

        resultado = insertar_marcaciones_crudas(
            db=db_motor,
            records=[{
                "user_id": "88",
                "timestamp": "2026-08-18T08:00:00",
                "uid": 1,
                "punch": 0,
                "punch_label": "Entrada",
                "status": 0,
                "status_label": "OK",
            }],
            sync_run_id="TEST-RUN-2",
            dispositivo_ip=None,
            dispositivo_origen="DISPOSITIVO_DESCONOCIDO",
        )

        assert resultado["insertadas"] == 1
        assert len(resultado["conflictos"]) == 1

        fila = db_motor.execute(text(
            "SELECT empleado_id FROM asistencia.marcaciones_crudas "
            "WHERE dispositivo_origen = 'DISPOSITIVO_DESCONOCIDO' AND zk_user_id = '88'"
        )).mappings().first()
        assert fila["empleado_id"] is None


# ============================================================
# Tests de integración: reconciliación de marcaciones huérfanas
# ============================================================


@pytest.mark.integration
class TestReconciliacionHuerfanasIdentidadCanonica:

    def test_reconciliacion_usa_resolucion_canonica(self, db_motor):
        """La reconciliación de huérfanas del motor debe vincular por
        dispositivo canónico."""
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_correcto = _crear_empleado(
            db_motor, "EMP-HUERF-CORRECTO", unidad_id, puesto_id
        )
        dispositivo_id = _crear_dispositivo(db_motor, "ZK_HUERF", "10.0.2.1")
        _vincular_empleado_dispositivo(
            db_motor, empleado_correcto, dispositivo_id, "700"
        )
        db_motor.commit()

        _insertar_marcacion_huerfana(
            db_motor, "ZK_HUERF", "700", datetime(2026, 8, 18, 7, 55, 0), punch=0
        )
        db_motor.commit()

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        fila = db_motor.execute(text(
            "SELECT empleado_id FROM asistencia.marcaciones_crudas "
            "WHERE dispositivo_origen = 'ZK_HUERF' AND zk_user_id = '700'"
        )).mappings().first()
        assert fila["empleado_id"] == empleado_correcto

    def test_reconciliacion_reporta_conflicto_ambiguo(self, db_motor):
        """Una marcación huérfana cuyo dispositivo no se identifica y cuyo
        zk_user_id está activo para más de un empleado en dispositivos
        distintos debe reportarse como conflicto, sin vincularse."""
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_a = _crear_empleado(db_motor, "EMP-HUERF-CONF-A", unidad_id, puesto_id)
        empleado_b = _crear_empleado(db_motor, "EMP-HUERF-CONF-B", unidad_id, puesto_id)
        dispositivo_a = _crear_dispositivo(db_motor, "ZK_HUERF_A", "10.0.2.2")
        dispositivo_b = _crear_dispositivo(db_motor, "ZK_HUERF_B", "10.0.2.3")
        _vincular_empleado_dispositivo(db_motor, empleado_a, dispositivo_a, "55")
        _vincular_empleado_dispositivo(db_motor, empleado_b, dispositivo_b, "55")
        db_motor.commit()

        _insertar_marcacion_huerfana(
            db_motor, "DISPOSITIVO_DESCONOCIDO", "55", datetime(2026, 8, 18, 7, 55, 0), punch=0
        )
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        assert len(resultado["conflictos_identidad_zk"]) == 1
        conflicto = resultado["conflictos_identidad_zk"][0]
        assert conflicto["zk_user_id"] == "55"

        fila = db_motor.execute(text(
            "SELECT empleado_id FROM asistencia.marcaciones_crudas "
            "WHERE dispositivo_origen = 'DISPOSITIVO_DESCONOCIDO' AND zk_user_id = '55'"
        )).mappings().first()
        assert fila["empleado_id"] is None

    def test_reconciliacion_cae_a_legacy_sin_relacion_canonica(self, db_motor):
        """Sin ninguna relación resoluble en empleado_dispositivo, la
        reconciliación debe seguir cayendo al campo legacy
        personal.empleados.zk_user_id (compatibilidad temporal)."""
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_legacy = _crear_empleado(
            db_motor, "EMP-HUERF-LEGACY", unidad_id, puesto_id, zk_user_id_legacy="850"
        )
        db_motor.commit()

        _insertar_marcacion_huerfana(
            db_motor, "ZK_SIN_CATALOGAR", "850", datetime(2026, 8, 18, 7, 55, 0), punch=0
        )
        db_motor.commit()

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        fila = db_motor.execute(text(
            "SELECT empleado_id FROM asistencia.marcaciones_crudas "
            "WHERE dispositivo_origen = 'ZK_SIN_CATALOGAR' AND zk_user_id = '850'"
        )).mappings().first()
        assert fila["empleado_id"] == empleado_legacy
