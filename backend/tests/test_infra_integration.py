"""
Tests de infraestructura de integración.

Verifican que:
1. La conexión a dae_reloj_test funciona.
2. La guardia de seguridad protege contra dae_reloj.
3. El baseline crea los schemas y tablas esperados.
4. El aislamiento por rollback funciona.
"""

import pytest
from sqlalchemy import text


# ============================================================
# 0. Guardia de seguridad — validación de rechazo
# ============================================================


@pytest.mark.integration
class TestGuardiaSeguridad:
    """Verifica que la guardia rechazaría nombres de BD inseguros."""

    def test_funcion_guardia_rechaza_dae_reloj(self):
        """La función _validate_test_database debe rechazar 'dae_reloj'."""
        from tests.conftest import _validate_test_database
        from unittest.mock import MagicMock

        # Simular un engine que retorna 'dae_reloj'
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = lambda s, *a: None
        mock_conn.execute.return_value.scalar_one.return_value = "dae_reloj"

        with pytest.raises(RuntimeError, match="PRODUCTIVA"):
            _validate_test_database(mock_engine)

    def test_funcion_guardia_rechaza_nombre_sin_test(self):
        """La guardia debe rechazar nombres que no terminen en _test."""
        from tests.conftest import _validate_test_database
        from unittest.mock import MagicMock

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = lambda s, *a: None
        mock_conn.execute.return_value.scalar_one.return_value = "otra_bd_produccion"

        with pytest.raises(RuntimeError, match="_test"):
            _validate_test_database(mock_engine)


# ============================================================
# 1. Conexión y seguridad
# ============================================================


@pytest.mark.integration
class TestConexionSeguridad:
    """Verifica que la infraestructura de BD está correcta."""

    def test_conexion_a_dae_reloj_test(self, db_session):
        """La sesión debe estar conectada a dae_reloj_test."""
        db_name = db_session.execute(text("SELECT current_database()")).scalar_one()
        assert db_name == "dae_reloj_test"

    def test_bd_termina_en_test(self, db_session):
        """current_database() debe terminar en _test."""
        db_name = db_session.execute(text("SELECT current_database()")).scalar_one()
        assert str(db_name).endswith("_test")

    def test_no_es_dae_reloj(self, db_session):
        """NUNCA debe ser dae_reloj."""
        db_name = db_session.execute(text("SELECT current_database()")).scalar_one()
        assert db_name != "dae_reloj"


# ============================================================
# 2. Schemas y tablas del baseline
# ============================================================


@pytest.mark.integration
class TestBaselineEsquema:
    """Verifica que el baseline creó las tablas correctas."""

    def test_schema_personal_existe(self, db_session):
        result = db_session.execute(text(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'personal'"
        )).scalar_one_or_none()
        assert result == "personal"

    def test_schema_asistencia_existe(self, db_session):
        result = db_session.execute(text(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'asistencia'"
        )).scalar_one_or_none()
        assert result == "asistencia"

    def test_schema_organizacion_existe(self, db_session):
        result = db_session.execute(text(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'organizacion'"
        )).scalar_one_or_none()
        assert result == "organizacion"

    def test_tabla_empleados(self, db_session):
        result = db_session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='personal' AND table_name='empleados'"
        )).scalar_one_or_none()
        assert result == "empleados"

    def test_tabla_asistencias_diarias(self, db_session):
        result = db_session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='asistencia' AND table_name='asistencias_diarias'"
        )).scalar_one_or_none()
        assert result == "asistencias_diarias"

    def test_tabla_marcaciones_crudas(self, db_session):
        result = db_session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='asistencia' AND table_name='marcaciones_crudas'"
        )).scalar_one_or_none()
        assert result == "marcaciones_crudas"

    def test_tabla_horarios(self, db_session):
        result = db_session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='asistencia' AND table_name='horarios'"
        )).scalar_one_or_none()
        assert result == "horarios"

    def test_tabla_politicas_asistencia(self, db_session):
        result = db_session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='asistencia' AND table_name='politicas_asistencia'"
        )).scalar_one_or_none()
        assert result == "politicas_asistencia"

    def test_tabla_calendario_eventos(self, db_session):
        result = db_session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='asistencia' AND table_name='calendario_eventos'"
        )).scalar_one_or_none()
        assert result == "calendario_eventos"

    def test_tabla_horario_dias(self, db_session):
        result = db_session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='asistencia' AND table_name='horario_dias'"
        )).scalar_one_or_none()
        assert result == "horario_dias"


# ============================================================
# 3. Aislamiento — rollback entre tests
# ============================================================


@pytest.mark.integration
class TestAislamiento:
    """Verifica que los tests están aislados por transacción."""

    def test_insertar_empleado(self, db_session, seed_basico):
        """Inserta un segundo empleado — no debe verse en otros tests."""
        db_session.execute(text(
            "INSERT INTO personal.empleados "
            "(codigo_empleado, nombres, apellido_paterno, unidad_organizacional_id, puesto_id, estatus) "
            "VALUES ('EMP-AISLAMIENTO', 'AISLAMIENTO', 'TEST', "
            "(SELECT id FROM organizacion.unidades_organizacionales LIMIT 1), "
            "(SELECT id FROM organizacion.puestos LIMIT 1), 'ACTIVO')"
        ))
        count = db_session.execute(text(
            "SELECT COUNT(*) FROM personal.empleados WHERE codigo_empleado = 'EMP-AISLAMIENTO'"
        )).scalar_one()
        assert count == 1

    def test_empleado_no_persiste(self, db_session, seed_basico):
        """El empleado del test anterior no debe existir (rollback)."""
        count = db_session.execute(text(
            "SELECT COUNT(*) FROM personal.empleados WHERE codigo_empleado = 'EMP-AISLAMIENTO'"
        )).scalar_one()
        assert count == 0

    def test_seed_basico_funciona(self, db_session, seed_basico):
        """El seed crea el empleado de prueba."""
        count = db_session.execute(text(
            "SELECT COUNT(*) FROM personal.empleados WHERE codigo_empleado = 'EMP-TEST-001'"
        )).scalar_one()
        assert count == 1


# ============================================================
# 4. Commit interno NO escapa de transacción exterior
# ============================================================


@pytest.mark.integration
class TestCommitInternoAislado:
    """
    Demuestra empíricamente que session.commit() dentro del test
    NO persiste datos fuera de la transacción exterior.

    Estrategia: join_transaction_mode="create_savepoint" (SQLAlchemy 2.0+).
    """

    def test_commit_interno_visible_dentro_del_test(self, db_session, seed_basico):
        """Un commit() interno es visible dentro del mismo test."""
        db_session.execute(text(
            "INSERT INTO organizacion.puestos (codigo, nombre, nivel_jerarquico) "
            "VALUES ('PUESTO_COMMIT_TEST', 'Puesto Commit', 5)"
        ))
        db_session.commit()  # <-- commit interno

        count = db_session.execute(text(
            "SELECT COUNT(*) FROM organizacion.puestos WHERE codigo = 'PUESTO_COMMIT_TEST'"
        )).scalar_one()
        assert count == 1

    def test_commit_interno_no_persiste_entre_tests(self, db_session, seed_basico):
        """El registro insertado+committed en el test anterior NO existe aquí."""
        count = db_session.execute(text(
            "SELECT COUNT(*) FROM organizacion.puestos WHERE codigo = 'PUESTO_COMMIT_TEST'"
        )).scalar_one()
        assert count == 0, "El commit interno del test anterior escapó de la transacción exterior"


# ============================================================
# 5. Check constraint de estatus
# ============================================================


@pytest.mark.integration
class TestConstraints:
    """Verifica que los constraints del esquema real funcionan."""

    def test_check_estatus_valido(self, db_session, seed_basico):
        """COMPLETO es un estatus válido."""
        db_session.execute(text(
            "INSERT INTO asistencia.asistencias_diarias "
            "(empleado_id, politica_asistencia_id, horario_id, fecha, estatus, procesada, fecha_procesamiento) "
            "VALUES ("
            "(SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'), "
            "(SELECT id FROM asistencia.politicas_asistencia WHERE codigo='POLITICA_DAE_GENERAL'), "
            "(SELECT id FROM asistencia.horarios WHERE codigo='HORARIO_TEST'), "
            "'2026-08-18', 'COMPLETO', TRUE, NOW())"
        ))
        # No debe lanzar excepción

    def test_check_estatus_tolerancia_valido(self, db_session, seed_basico):
        """TOLERANCIA es un estatus válido según CHECK constraint."""
        db_session.execute(text(
            "INSERT INTO asistencia.asistencias_diarias "
            "(empleado_id, politica_asistencia_id, horario_id, fecha, estatus, procesada, fecha_procesamiento) "
            "VALUES ("
            "(SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'), "
            "(SELECT id FROM asistencia.politicas_asistencia WHERE codigo='POLITICA_DAE_GENERAL'), "
            "(SELECT id FROM asistencia.horarios WHERE codigo='HORARIO_TEST'), "
            "'2026-08-19', 'TOLERANCIA', TRUE, NOW())"
        ))
        # TOLERANCIA está en el CHECK constraint — debe pasar

    def test_check_estatus_invalido_falla(self, db_session, seed_basico):
        """Un estatus no definido en CHECK debe fallar."""
        with pytest.raises(Exception):
            db_session.execute(text(
                "INSERT INTO asistencia.asistencias_diarias "
                "(empleado_id, politica_asistencia_id, horario_id, fecha, estatus, procesada, fecha_procesamiento) "
                "VALUES ("
                "(SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'), "
                "(SELECT id FROM asistencia.politicas_asistencia WHERE codigo='POLITICA_DAE_GENERAL'), "
                "(SELECT id FROM asistencia.horarios WHERE codigo='HORARIO_TEST'), "
                "'2026-08-20', 'ESTATUS_INVENTADO', TRUE, NOW())"
            ))
            db_session.flush()
