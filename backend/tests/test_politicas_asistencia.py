"""
Tests de la Política de Asistencia (asistencia.politicas_asistencia):
lectura/actualización de la política ACTIVA vigente y sus validaciones
(Contrato §5).

Cubre dos niveles:
- Servicio/repositorio directo (db_session + seed_basico): reglas de
  resolución (SIN_POLITICA / MULTIPLES_POLITICAS / OK) y persistencia
  de la actualización sin perder precisión en segundos.
- HTTP end-to-end (db_motor + api_client): autorización real por
  módulo CONFIGURACION y códigos de estado explícitos (404/409/400).
"""

from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from app.core.security import create_access_token
from app.schemas.politicas import PoliticaAsistenciaUpdate
from app.services.politica_service import (
    PoliticaSinResolucionUnica,
    actualizar_politica_activa,
    obtener_politica_activa,
)


FECHA_VIGENTE = date(2026, 3, 1)


# ============================================================
# Nivel servicio/repositorio
# ============================================================


@pytest.mark.integration
class TestObtenerPoliticaActiva:
    def test_retorna_la_politica_seedeada(self, db_session, seed_basico, politica_dae):
        politica = obtener_politica_activa(db_session, FECHA_VIGENTE)

        assert politica["codigo"] == politica_dae["codigo"]
        assert politica["limite_tolerancia_segundos"] == politica_dae["limite_tolerancia_segundos"]
        assert politica["limite_retardo_menor_segundos"] == politica_dae["limite_retardo_menor_segundos"]
        assert politica["limite_retardo_mayor_segundos"] == politica_dae["limite_retardo_mayor_segundos"]
        assert politica["puntos_retardo_menor"] == politica_dae["puntos_retardo_menor"]
        assert politica["puntos_retardo_mayor"] == politica_dae["puntos_retardo_mayor"]
        assert politica["puntos_para_descanso"] == politica_dae["puntos_para_descanso"]
        assert politica["descansos_para_revision_baja"] == politica_dae["descansos_para_revision_baja"]
        assert politica["faltas_consecutivas_revision_baja"] == politica_dae["faltas_consecutivas_revision_baja"]

    def test_sin_politica_lanza_error_explicito(self, db_session):
        # Sin seed: no existe ninguna política en la BD de test.
        with pytest.raises(PoliticaSinResolucionUnica) as exc_info:
            obtener_politica_activa(db_session, FECHA_VIGENTE)

        assert exc_info.value.estado == "SIN_POLITICA"

    def test_multiples_politicas_solapadas_lanza_error_explicito(
        self, db_session, seed_basico
    ):
        # Segunda política ACTIVA con vigencia solapada a la del seed
        # (POLITICA_DAE_GENERAL, vigente desde 2026-01-01 sin fin).
        db_session.execute(text(
            "INSERT INTO asistencia.politicas_asistencia "
            "(codigo, version, nombre, tipo_periodo, "
            "limite_tolerancia_segundos, limite_retardo_menor_segundos, "
            "limite_retardo_mayor_segundos, puntos_retardo_menor, "
            "puntos_retardo_mayor, puntos_para_descanso, "
            "max_dias_justificables_periodo, max_puntos_descontables_por_dia, "
            "descansos_para_revision_baja, faltas_consecutivas_revision_baja, "
            "vigencia_desde, activo) "
            "VALUES ('POLITICA_DUPLICADA', 1, 'Política duplicada', 'QUINCENAL', "
            "600, 1200, 1800, 1, 2, 10, 2, 2, 7, 3, '2026-02-01', TRUE)"
        ))
        db_session.flush()

        with pytest.raises(PoliticaSinResolucionUnica) as exc_info:
            obtener_politica_activa(db_session, FECHA_VIGENTE)

        assert exc_info.value.estado == "MULTIPLES_POLITICAS"
        assert len(exc_info.value.resolucion.candidatos) == 2


@pytest.mark.integration
class TestActualizarPoliticaActiva:
    def test_persiste_cambios_respetando_precision_en_segundos(
        self, db_session, seed_basico
    ):
        # Valores deliberadamente NO redondos en minutos (mm:59) para
        # comprobar que no se trunca precisión (Contrato §5).
        payload = PoliticaAsistenciaUpdate(
            limite_tolerancia_segundos=725,   # 12:05
            limite_retardo_menor_segundos=1325,  # 22:05
            limite_retardo_mayor_segundos=1925,  # 32:05
            puntos_retardo_menor=1,
            puntos_retardo_mayor=3,
            puntos_para_descanso=8,
            descansos_para_revision_baja=5,
            faltas_consecutivas_revision_baja=2,
        )

        actualizada = actualizar_politica_activa(db_session, payload, FECHA_VIGENTE)

        assert actualizada["limite_tolerancia_segundos"] == 725
        assert actualizada["limite_retardo_menor_segundos"] == 1325
        assert actualizada["limite_retardo_mayor_segundos"] == 1925
        assert actualizada["puntos_retardo_mayor"] == 3
        assert actualizada["puntos_para_descanso"] == 8
        assert actualizada["descansos_para_revision_baja"] == 5
        assert actualizada["faltas_consecutivas_revision_baja"] == 2

        # Releer desde BD confirma que persistió (no solo en memoria).
        releida = obtener_politica_activa(db_session, FECHA_VIGENTE)
        assert releida["limite_tolerancia_segundos"] == 725

    def test_sin_politica_activa_lanza_error_explicito(self, db_session):
        payload = PoliticaAsistenciaUpdate(
            limite_tolerancia_segundos=600,
            limite_retardo_menor_segundos=1200,
            limite_retardo_mayor_segundos=1800,
            puntos_retardo_menor=1,
            puntos_retardo_mayor=2,
            puntos_para_descanso=10,
            descansos_para_revision_baja=7,
            faltas_consecutivas_revision_baja=3,
        )

        with pytest.raises(PoliticaSinResolucionUnica) as exc_info:
            actualizar_politica_activa(db_session, payload, FECHA_VIGENTE)

        assert exc_info.value.estado == "SIN_POLITICA"

    @pytest.mark.parametrize(
        "overrides",
        [
            # Límites no crecientes (tolerancia == retardo_menor).
            {"limite_tolerancia_segundos": 1200},
            # retardo_mayor menor que retardo_menor.
            {"limite_retardo_mayor_segundos": 100},
        ],
    )
    def test_rechaza_limites_no_crecientes(self, overrides):
        base = {
            "limite_tolerancia_segundos": 600,
            "limite_retardo_menor_segundos": 1200,
            "limite_retardo_mayor_segundos": 1800,
            "puntos_retardo_menor": 1,
            "puntos_retardo_mayor": 2,
            "puntos_para_descanso": 10,
            "descansos_para_revision_baja": 7,
            "faltas_consecutivas_revision_baja": 3,
        }
        base.update(overrides)

        with pytest.raises(ValidationError):
            PoliticaAsistenciaUpdate(**base)

    def test_rechaza_puntos_retardo_mayor_menor_que_menor(self):
        with pytest.raises(ValidationError):
            PoliticaAsistenciaUpdate(
                limite_tolerancia_segundos=600,
                limite_retardo_menor_segundos=1200,
                limite_retardo_mayor_segundos=1800,
                puntos_retardo_menor=3,
                puntos_retardo_mayor=1,
                puntos_para_descanso=10,
                descansos_para_revision_baja=7,
                faltas_consecutivas_revision_baja=3,
            )

    @pytest.mark.parametrize(
        "campo",
        [
            "puntos_para_descanso",
            "descansos_para_revision_baja",
            "faltas_consecutivas_revision_baja",
        ],
    )
    def test_rechaza_valores_no_positivos_en_campos_gt_cero(self, campo):
        base = {
            "limite_tolerancia_segundos": 600,
            "limite_retardo_menor_segundos": 1200,
            "limite_retardo_mayor_segundos": 1800,
            "puntos_retardo_menor": 1,
            "puntos_retardo_mayor": 2,
            "puntos_para_descanso": 10,
            "descansos_para_revision_baja": 7,
            "faltas_consecutivas_revision_baja": 3,
        }
        base[campo] = 0

        with pytest.raises(ValidationError):
            PoliticaAsistenciaUpdate(**base)

    def test_rechaza_limites_negativos(self):
        with pytest.raises(ValidationError):
            PoliticaAsistenciaUpdate(
                limite_tolerancia_segundos=-1,
                limite_retardo_menor_segundos=1200,
                limite_retardo_mayor_segundos=1800,
                puntos_retardo_menor=1,
                puntos_retardo_mayor=2,
                puntos_para_descanso=10,
                descansos_para_revision_baja=7,
                faltas_consecutivas_revision_baja=3,
            )


# ============================================================
# Nivel HTTP (autorización real + códigos de estado explícitos)
# ============================================================


def _crear_modulo(db, codigo="CONFIGURACION"):
    db.execute(text(
        "INSERT INTO seguridad.modulos (codigo, nombre, activo) "
        "VALUES (:codigo, :codigo, TRUE) "
        "ON CONFLICT (codigo) DO NOTHING"
    ), {"codigo": codigo})
    return db.execute(text(
        "SELECT id FROM seguridad.modulos WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_rol_configuracion(db, *, codigo, puede_consultar=True, puede_editar=False):
    db.execute(text(
        "INSERT INTO seguridad.roles (codigo, nombre, activo) "
        "VALUES (:codigo, :codigo, TRUE)"
    ), {"codigo": codigo})
    rol_id = db.execute(text(
        "SELECT id FROM seguridad.roles WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()

    modulo_id = _crear_modulo(db)

    db.execute(text(
        "INSERT INTO seguridad.permisos_rol "
        "(rol_id, modulo_id, alcance_datos, puede_consultar, puede_crear, "
        "puede_editar, puede_eliminar, puede_aprobar, puede_exportar) "
        "VALUES (:rol_id, :modulo_id, 'TOTAL', :consultar, FALSE, "
        ":editar, FALSE, FALSE, FALSE)"
    ), {
        "rol_id": rol_id,
        "modulo_id": modulo_id,
        "consultar": puede_consultar,
        "editar": puede_editar,
    })
    return rol_id


def _crear_usuario(db, *, rol_id, correo):
    db.execute(text(
        "INSERT INTO seguridad.usuarios "
        "(rol_id, correo, correo_electronico, estatus) "
        "VALUES (:rol_id, :correo, :correo, 'ACTIVO')"
    ), {"rol_id": rol_id, "correo": correo})
    return db.execute(text(
        "SELECT id FROM seguridad.usuarios WHERE correo_electronico = :correo"
    ), {"correo": correo}).scalar_one()


def _seed_politica_vigente(db, *, codigo="HTTP_POLITICA", vigencia_desde="2026-01-01"):
    db.execute(text(
        "INSERT INTO asistencia.politicas_asistencia "
        "(codigo, version, nombre, tipo_periodo, limite_tolerancia_segundos, "
        "limite_retardo_menor_segundos, limite_retardo_mayor_segundos, "
        "puntos_retardo_menor, puntos_retardo_mayor, puntos_para_descanso, "
        "max_dias_justificables_periodo, max_puntos_descontables_por_dia, "
        "descansos_para_revision_baja, faltas_consecutivas_revision_baja, "
        "vigencia_desde, activo) "
        "VALUES (:codigo, 1, :codigo, 'QUINCENAL', 659, 1259, 1859, 1, 2, 10, "
        "2, 2, 7, 3, :vigencia_desde, TRUE)"
    ), {"codigo": codigo, "vigencia_desde": vigencia_desde})


def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


VALID_UPDATE_PAYLOAD = {
    "limite_tolerancia_segundos": 600,
    "limite_retardo_menor_segundos": 1200,
    "limite_retardo_mayor_segundos": 1800,
    "puntos_retardo_menor": 1,
    "puntos_retardo_mayor": 2,
    "puntos_para_descanso": 10,
    "descansos_para_revision_baja": 7,
    "faltas_consecutivas_revision_baja": 3,
}


@pytest.mark.integration
class TestPoliticaActivaHTTP:
    def test_get_requiere_permiso_de_consulta(self, db_motor, api_client):
        _seed_politica_vigente(db_motor)
        rol_id = _crear_rol_configuracion(db_motor, codigo="ROL_CONFIG_LECTURA")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="config_lectura@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/politicas-asistencia/activa",
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["codigo"] == "HTTP_POLITICA"
        assert body["limite_tolerancia_segundos"] == 659

    def test_get_sin_token_recibe_401(self, db_motor, api_client):
        resp = api_client.get("/api/v1/politicas-asistencia/activa")
        assert resp.status_code == 401, resp.text

    def test_get_sin_politica_activa_recibe_404(self, db_motor, api_client):
        # Sin seed de política: universo vacío en asistencia.politicas_asistencia.
        rol_id = _crear_rol_configuracion(db_motor, codigo="ROL_CONFIG_404")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="config_404@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/politicas-asistencia/activa",
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 404, resp.text

    def test_get_multiples_politicas_solapadas_recibe_409(self, db_motor, api_client):
        _seed_politica_vigente(db_motor, codigo="HTTP_POLITICA_A", vigencia_desde="2026-01-01")
        _seed_politica_vigente(db_motor, codigo="HTTP_POLITICA_B", vigencia_desde="2026-02-01")
        rol_id = _crear_rol_configuracion(db_motor, codigo="ROL_CONFIG_409")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="config_409@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/politicas-asistencia/activa",
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 409, resp.text
        assert len(resp.json()["detail"]["candidatos"]) == 2

    def test_put_sin_permiso_editar_recibe_403(self, db_motor, api_client):
        _seed_politica_vigente(db_motor)
        rol_id = _crear_rol_configuracion(
            db_motor, codigo="ROL_CONFIG_SOLO_LECTURA", puede_editar=False
        )
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="config_solo_lectura@dae.test")
        db_motor.commit()

        resp = api_client.put(
            "/api/v1/politicas-asistencia/activa",
            json=VALID_UPDATE_PAYLOAD,
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 403, resp.text

    def test_put_con_permiso_editar_actualiza_y_persiste(self, db_motor, api_client):
        _seed_politica_vigente(db_motor)
        rol_id = _crear_rol_configuracion(
            db_motor, codigo="ROL_CONFIG_EDITOR", puede_editar=True
        )
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="config_editor@dae.test")
        db_motor.commit()

        resp = api_client.put(
            "/api/v1/politicas-asistencia/activa",
            json=VALID_UPDATE_PAYLOAD,
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["limite_tolerancia_segundos"] == 600
        assert resp.json()["puntos_para_descanso"] == 10

        resp_get = api_client.get(
            "/api/v1/politicas-asistencia/activa",
            headers=_auth_headers(usuario_id),
        )
        assert resp_get.json()["limite_tolerancia_segundos"] == 600

    def test_put_limites_no_crecientes_recibe_400(self, db_motor, api_client):
        _seed_politica_vigente(db_motor)
        rol_id = _crear_rol_configuracion(
            db_motor, codigo="ROL_CONFIG_EDITOR_400", puede_editar=True
        )
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="config_editor_400@dae.test")
        db_motor.commit()

        payload_invalido = dict(VALID_UPDATE_PAYLOAD)
        payload_invalido["limite_retardo_mayor_segundos"] = 100  # menor que retardo_menor

        resp = api_client.put(
            "/api/v1/politicas-asistencia/activa",
            json=payload_invalido,
            headers=_auth_headers(usuario_id),
        )
        # Rechazado por Pydantic (422) antes de tocar el servicio.
        assert resp.status_code == 422, resp.text
