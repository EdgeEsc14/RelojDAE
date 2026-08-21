"""
Configuración central de pytest para RelojDAE.

AISLAMIENTO:
- Los tests NUNCA se conectan a la BD productiva (dae_reloj).
- La BD de integración es dae_reloj_test (variable TEST_DATABASE_URL).
- Guardia de seguridad valida current_database() antes de escribir.

ESTRATEGIA:
- Tests unitarios (@pytest.mark.unit): sin BD, importan funciones puras.
- Tests de integración (@pytest.mark.integration): requieren dae_reloj_test.
  Usan transacción + rollback por test para aislamiento.
- Tests de contrato (@pytest.mark.contract): exigen comportamiento del contrato.
"""

import os
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Asegurar que el directorio backend esté en sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ruta al baseline SQL
BASELINE_SQL_PATH = Path(__file__).parent / "sql" / "baseline_test.sql"


# ============================================================
# Valores de referencia — Política DAE General (migración 022)
# ============================================================

POLITICA_DAE = {
    "codigo": "POLITICA_DAE_GENERAL",
    "version": 1,
    "nombre": "Política general DAE",
    "tipo_periodo": "QUINCENAL",
    "limite_tolerancia_segundos": 659,
    "limite_retardo_menor_segundos": 1259,
    "limite_retardo_mayor_segundos": 1859,
    "puntos_retardo_menor": 1,
    "puntos_retardo_mayor": 2,
    "puntos_para_descanso": 10,
    "max_dias_justificables_periodo": 2,
    "max_puntos_descontables_por_dia": 2,
    "descansos_para_revision_baja": 7,
    "faltas_consecutivas_revision_baja": 3,
    "vigencia_desde": date(2026, 1, 1),
    "vigencia_hasta": None,
    "activo": True,
}


# ============================================================
# SEGURIDAD: Guardia contra BD productiva
# ============================================================


def _validate_test_database(engine):
    """
    Valida que la conexión apunta a dae_reloj_test.
    ABORTA si detecta dae_reloj o cualquier BD que no termine en _test.
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database()")).scalar_one()

    db_name = str(result).strip()

    if db_name == "dae_reloj":
        raise RuntimeError(
            f"SEGURIDAD: Tests intentaron conectarse a la BD PRODUCTIVA ({db_name}). "
            "ABORTANDO. Configura TEST_DATABASE_URL apuntando a dae_reloj_test."
        )

    if not db_name.endswith("_test"):
        raise RuntimeError(
            f"SEGURIDAD: La BD conectada ({db_name}) no termina en '_test'. "
            "ABORTANDO. Solo se permiten tests contra bases que terminen en _test."
        )

    return db_name


# ============================================================
# FIXTURES: Engine y sesión para integración
# ============================================================


def _get_test_database_url():
    """
    Obtiene TEST_DATABASE_URL del entorno.
    Si no está definida, intenta cargar de .env.test.
    NUNCA hace fallback a la URL productiva.
    """
    url = os.environ.get("TEST_DATABASE_URL")

    if url:
        return url

    # Intentar cargar de .env.test
    env_test_path = BACKEND_DIR / ".env.test"
    if env_test_path.exists():
        for line in env_test_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("TEST_DATABASE_URL=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip()

    return None


@pytest.fixture(scope="session")
def test_engine():
    """
    Engine de SQLAlchemy conectado a dae_reloj_test.
    Scope de sesión: se crea una vez para toda la suite.
    Valida seguridad antes de devolver.
    """
    url = _get_test_database_url()

    if url is None:
        pytest.skip(
            "TEST_DATABASE_URL no definida. "
            "Crea backend/.env.test con la URL de dae_reloj_test."
        )

    engine = create_engine(url, future=True)

    # GUARDIA DE SEGURIDAD
    db_name = _validate_test_database(engine)

    return engine


@pytest.fixture(scope="session")
def apply_baseline(test_engine):
    """
    Aplica el baseline SQL a dae_reloj_test una vez por sesión.
    Limpia y recrea las tablas del núcleo.
    """
    if not BASELINE_SQL_PATH.exists():
        pytest.fail(f"No se encontró baseline SQL: {BASELINE_SQL_PATH}")

    sql = BASELINE_SQL_PATH.read_text(encoding="utf-8")

    with test_engine.begin() as conn:
        # El baseline incluye DROP SCHEMA CASCADE + CREATE
        conn.execute(text(sql))

    return True


@pytest.fixture(scope="function")
def db_session(test_engine, apply_baseline):
    """
    Sesión de BD con transacción externa + savepoints para aislamiento.

    Estrategia (SQLAlchemy 2.0+):
    1. Abre conexión con transacción externa (begin).
    2. Crea Session con join_transaction_mode="create_savepoint".
    3. Cuando código productivo hace session.commit(), solo consolida savepoint.
    4. Al final, rollback de transacción exterior deshace todo.

    Esto permite testear funciones que hacen db.commit() sin que los datos
    persistan entre tests.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    # Verificación de seguridad per-test
    db_name = session.execute(text("SELECT current_database()")).scalar_one()
    assert str(db_name).endswith("_test"), (
        f"SEGURIDAD: BD conectada es '{db_name}', no termina en _test. ABORTANDO."
    )

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ============================================================
# FIXTURES: Datos sintéticos para tests de integración
# ============================================================


@pytest.fixture
def seed_basico(db_session):
    """
    Seed mínimo para tests del núcleo:
    - 1 unidad organizacional
    - 1 puesto
    - 1 tipo turno
    - 1 horario
    - 1 política de asistencia
    - 1 calendario activo
    - 1 empleado activo con asignación de horario
    """
    db = db_session

    # Unidad organizacional
    db.execute(text(
        "INSERT INTO organizacion.unidades_organizacionales (codigo, nombre) "
        "VALUES ('TEST_UNIT', 'Unidad de Pruebas')"
    ))

    # Puesto
    db.execute(text(
        "INSERT INTO organizacion.puestos (codigo, nombre, nivel_jerarquico) "
        "VALUES ('TEST_PUESTO', 'Puesto de Prueba', 1)"
    ))

    # Tipo turno matutino
    db.execute(text(
        "INSERT INTO asistencia.tipos_turno "
        "(codigo, nombre, duracion_jornada_minutos, modalidad_tiempo_extra, hora_entrada_desde, hora_entrada_hasta) "
        "VALUES ('MATUTINO', 'Matutino', 420, 'DESPUES_SALIDA', '06:00', '10:00')"
    ))

    # Horario 08:00 - 15:00
    db.execute(text(
        "INSERT INTO asistencia.horarios "
        "(codigo, nombre, tipo_turno_id, hora_entrada, hora_salida, tolerancia_entrada_minutos, permite_tiempo_extra) "
        "VALUES ('HORARIO_TEST', 'Horario Test 08-15', "
        "(SELECT id FROM asistencia.tipos_turno WHERE codigo='MATUTINO'), "
        "'08:00', '15:00', 10, TRUE)"
    ))

    # Política DAE General
    db.execute(text(
        "INSERT INTO asistencia.politicas_asistencia "
        "(codigo, version, nombre, tipo_periodo, "
        "limite_tolerancia_segundos, limite_retardo_menor_segundos, limite_retardo_mayor_segundos, "
        "puntos_retardo_menor, puntos_retardo_mayor, puntos_para_descanso, "
        "max_dias_justificables_periodo, max_puntos_descontables_por_dia, "
        "descansos_para_revision_baja, faltas_consecutivas_revision_baja, "
        "vigencia_desde, activo) "
        "VALUES ('POLITICA_DAE_GENERAL', 1, 'Política general DAE', 'QUINCENAL', "
        "659, 1259, 1859, 1, 2, 10, 2, 2, 7, 3, '2026-01-01', TRUE)"
    ))

    # Calendario activo
    db.execute(text(
        "INSERT INTO asistencia.calendarios (codigo, nombre, activo) "
        "VALUES ('CALENDARIO_TEST', 'Calendario de Pruebas', TRUE)"
    ))

    # Empleado
    db.execute(text(
        "INSERT INTO personal.empleados "
        "(codigo_empleado, nombres, apellido_paterno, "
        "unidad_organizacional_id, puesto_id, estatus, zk_user_id) "
        "VALUES ('EMP-TEST-001', 'JUAN', 'PEREZ', "
        "(SELECT id FROM organizacion.unidades_organizacionales WHERE codigo='TEST_UNIT'), "
        "(SELECT id FROM organizacion.puestos WHERE codigo='TEST_PUESTO'), "
        "'ACTIVO', '100')"
    ))

    # Asignación de horario
    db.execute(text(
        "INSERT INTO asistencia.asignaciones_horario "
        "(empleado_id, horario_id, fecha_inicio, estatus) "
        "VALUES ("
        "(SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'), "
        "(SELECT id FROM asistencia.horarios WHERE codigo='HORARIO_TEST'), "
        "'2026-01-01', 'ACTIVA')"
    ))

    db.flush()

    return {
        "empleado_codigo": "EMP-TEST-001",
        "horario_codigo": "HORARIO_TEST",
        "politica_codigo": "POLITICA_DAE_GENERAL",
    }


@pytest.fixture
def politica_dae():
    """Política DAE General como dict de referencia."""
    return POLITICA_DAE.copy()


# ============================================================
# FIXTURES: Sesión para motor completo (con TRUNCATE, sin savepoint)
# Para funciones que hacen commit()/rollback() interno.
# ============================================================


@pytest.fixture(scope="function")
def db_motor(test_engine, apply_baseline):
    """
    Sesión DIRECTA para tests del motor completo.

    NO usa savepoints — permite que el código productivo haga
    commit()/rollback() libremente.

    Limpieza: TRUNCATE de tablas de datos antes de cada test.
    Solo funciona contra dae_reloj_test (verificado).
    """
    connection = test_engine.connect()
    session = Session(bind=connection)

    # GUARDIA DOBLE de seguridad
    db_name = session.execute(text("SELECT current_database()")).scalar_one()
    assert str(db_name) == "dae_reloj_test", (
        f"SEGURIDAD: BD es '{db_name}', esperada 'dae_reloj_test'. ABORTANDO."
    )
    assert str(db_name).endswith("_test"), (
        f"SEGURIDAD: BD '{db_name}' no termina en '_test'. ABORTANDO."
    )

    # Limpiar tablas de datos (TRUNCATE solo en dae_reloj_test)
    session.execute(text(
        "TRUNCATE "
        "auditoria.bitacora, "
        "seguridad.login_auditoria, "
        "seguridad.usuarios_unidades, "
        "seguridad.usuarios, "
        "seguridad.permisos_rol, "
        "seguridad.modulos, "
        "seguridad.roles, "
        "dispositivos.empleado_dispositivo, "
        "dispositivos.dispositivos, "
        "asistencia.movimientos_puntos, "
        "asistencia.resumen_periodo_empleado, "
        "asistencia.incidencias, "
        "asistencia.tipos_incidencia, "
        "asistencia.asistencias_diarias, "
        "asistencia.marcaciones_crudas, "
        "asistencia.calendario_eventos, "
        "asistencia.asignaciones_horario, "
        "asistencia.horario_dias, "
        "asistencia.horarios, "
        "asistencia.tipos_turno, "
        "asistencia.politicas_asistencia, "
        "asistencia.periodos_evaluacion, "
        "asistencia.calendarios, "
        "personal.empleados, "
        "organizacion.puestos, "
        "organizacion.unidades_organizacionales "
        "RESTART IDENTITY CASCADE"
    ))
    session.commit()

    yield session

    # Limpiar después del test (por si acaso)
    try:
        db_name_post = session.execute(text("SELECT current_database()")).scalar_one()
        if str(db_name_post) == "dae_reloj_test":
            session.execute(text(
                "TRUNCATE "
                "auditoria.bitacora, "
                "seguridad.login_auditoria, "
        "seguridad.usuarios_unidades, "
                "seguridad.usuarios, "
                "seguridad.permisos_rol, "
                "seguridad.modulos, "
                "seguridad.roles, "
                "dispositivos.empleado_dispositivo, "
                "dispositivos.dispositivos, "
                "asistencia.movimientos_puntos, "
                "asistencia.resumen_periodo_empleado, "
                "asistencia.incidencias, "
                "asistencia.tipos_incidencia, "
                "asistencia.asistencias_diarias, "
                "asistencia.marcaciones_crudas, "
                "asistencia.calendario_eventos, "
                "asistencia.asignaciones_horario, "
                "asistencia.horario_dias, "
                "asistencia.horarios, "
                "asistencia.tipos_turno, "
                "asistencia.politicas_asistencia, "
                "asistencia.periodos_evaluacion, "
                "asistencia.calendarios, "
                "personal.empleados, "
                "organizacion.puestos, "
                "organizacion.unidades_organizacionales "
                "RESTART IDENTITY CASCADE"
            ))
            session.commit()
    except Exception:
        session.rollback()

    session.close()
    connection.close()


@pytest.fixture
def seed_motor(db_motor):
    """
    Seed para tests del motor completo.
    Crea datos mínimos y hace commit (necesario para que el motor los vea).
    """
    db = db_motor

    db.execute(text(
        "INSERT INTO organizacion.unidades_organizacionales (codigo, nombre) "
        "VALUES ('TEST_UNIT', 'Unidad de Pruebas')"
    ))
    db.execute(text(
        "INSERT INTO organizacion.puestos (codigo, nombre, nivel_jerarquico) "
        "VALUES ('TEST_PUESTO', 'Puesto de Prueba', 1)"
    ))
    db.execute(text(
        "INSERT INTO asistencia.tipos_turno "
        "(codigo, nombre, duracion_jornada_minutos, modalidad_tiempo_extra, hora_entrada_desde, hora_entrada_hasta) "
        "VALUES ('MATUTINO', 'Matutino', 420, 'DESPUES_SALIDA', '06:00', '10:00')"
    ))
    db.execute(text(
        "INSERT INTO asistencia.horarios "
        "(codigo, nombre, tipo_turno_id, hora_entrada, hora_salida, tolerancia_entrada_minutos, permite_tiempo_extra) "
        "VALUES ('HORARIO_TEST', 'Horario Test 08-15', "
        "(SELECT id FROM asistencia.tipos_turno WHERE codigo='MATUTINO'), "
        "'08:00', '15:00', 10, TRUE)"
    ))
    db.execute(text(
        "INSERT INTO asistencia.politicas_asistencia "
        "(codigo, version, nombre, tipo_periodo, "
        "limite_tolerancia_segundos, limite_retardo_menor_segundos, limite_retardo_mayor_segundos, "
        "puntos_retardo_menor, puntos_retardo_mayor, puntos_para_descanso, "
        "max_dias_justificables_periodo, max_puntos_descontables_por_dia, "
        "descansos_para_revision_baja, faltas_consecutivas_revision_baja, "
        "vigencia_desde, activo) "
        "VALUES ('POLITICA_DAE_GENERAL', 1, 'Política general DAE', 'QUINCENAL', "
        "659, 1259, 1859, 1, 2, 10, 2, 2, 7, 3, '2026-01-01', TRUE)"
    ))
    db.execute(text(
        "INSERT INTO asistencia.calendarios (codigo, nombre, activo) "
        "VALUES ('CALENDARIO_TEST', 'Calendario de Pruebas', TRUE)"
    ))
    db.execute(text(
        "INSERT INTO personal.empleados "
        "(codigo_empleado, nombres, apellido_paterno, "
        "unidad_organizacional_id, puesto_id, estatus, zk_user_id) "
        "VALUES ('EMP-TEST-001', 'JUAN', 'PEREZ', "
        "(SELECT id FROM organizacion.unidades_organizacionales WHERE codigo='TEST_UNIT'), "
        "(SELECT id FROM organizacion.puestos WHERE codigo='TEST_PUESTO'), "
        "'ACTIVO', '100')"
    ))
    db.execute(text(
        "INSERT INTO asistencia.asignaciones_horario "
        "(empleado_id, horario_id, fecha_inicio, estatus) "
        "VALUES ("
        "(SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'), "
        "(SELECT id FROM asistencia.horarios WHERE codigo='HORARIO_TEST'), "
        "'2026-01-01', 'ACTIVA')"
    ))
    db.commit()

    return {
        "empleado_codigo": "EMP-TEST-001",
        "horario_codigo": "HORARIO_TEST",
        "politica_codigo": "POLITICA_DAE_GENERAL",
    }


# ============================================================
# FIXTURE: cliente HTTP real (TestClient) para tests de autorización
# ============================================================


@pytest.fixture(scope="function")
def api_client(db_motor):
    """
    TestClient de FastAPI con get_db sobreescrito para usar la misma
    sesión de db_motor (mismo aislamiento/TRUNCATE por test).

    Permite ejercer la autorización real de extremo a extremo: JWT real
    (create_access_token/decode_access_token) + dependencias de
    autorización reales (require_module_access, build_access_scope),
    sin mockear nada de la capa de seguridad.
    """
    from fastapi.testclient import TestClient

    from app.main import app
    from app.core.database import get_db

    def _override_get_db():
        yield db_motor

    app.dependency_overrides[get_db] = _override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
