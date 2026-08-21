"""
Tests del módulo de Auditoría:

- auditoria.bitacora registra cambios reales (trigger genérico) y
  atribuye el usuario de aplicación una vez conectado el contexto de
  auditoría (antes usuario_app_id/correo quedaban siempre NULL);
- filtros de bitácora (esquema/tabla/operación/fecha/texto) funcionan
  realmente contra datos reales;
- detalle de un evento expone datos_anteriores/datos_nuevos/cambios;
- seguridad.login_auditoria ya poblada por /auth/login se lista y
  filtra por resultado;
- scopes: solo SUPER_ADMIN/AUDITOR tienen acceso; AUDITOR es de solo
  lectura (no existe ningún endpoint de escritura en /auditoria);
- exportación CSV.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import text

from app.core.security import create_access_token


def _crear_modulo(db, codigo="AUDITORIA"):
    db.execute(text(
        "INSERT INTO seguridad.modulos (codigo, nombre, activo) "
        "VALUES (:codigo, :codigo, TRUE) ON CONFLICT (codigo) DO NOTHING"
    ), {"codigo": codigo})
    return db.execute(text(
        "SELECT id FROM seguridad.modulos WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_rol_auditoria(db, *, codigo, alcance="TOTAL", puede_consultar=True, puede_exportar=True):
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


def _crear_rol_configuracion(db, *, codigo):
    """Rol con acceso a CONFIGURACION (para provocar un cambio auditable
    vía POST/PUT reales) pero sin ningún permiso sobre AUDITORIA."""
    db.execute(text(
        "INSERT INTO seguridad.roles (codigo, nombre, activo) VALUES (:codigo, :codigo, TRUE)"
    ), {"codigo": codigo})
    rol_id = db.execute(text(
        "SELECT id FROM seguridad.roles WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()
    modulo_id = _crear_modulo(db, "CONFIGURACION")
    db.execute(text(
        "INSERT INTO seguridad.permisos_rol "
        "(rol_id, modulo_id, alcance_datos, puede_consultar, puede_crear, "
        "puede_editar, puede_eliminar, puede_aprobar, puede_exportar) "
        "VALUES (:rol_id, :modulo_id, 'TOTAL', TRUE, TRUE, TRUE, FALSE, FALSE, FALSE)"
    ), {"rol_id": rol_id, "modulo_id": modulo_id})
    return rol_id


def _crear_usuario(db, *, rol_id, correo, empleado_id=None):
    db.execute(text(
        "INSERT INTO seguridad.usuarios "
        "(empleado_id, rol_id, correo, correo_electronico, estatus) "
        "VALUES (:empleado_id, :rol_id, :correo, :correo, 'ACTIVO')"
    ), {"empleado_id": empleado_id, "rol_id": rol_id, "correo": correo})
    return db.execute(text(
        "SELECT id FROM seguridad.usuarios WHERE correo_electronico = :correo"
    ), {"correo": correo}).scalar_one()


def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestBitacoraAtribucion:
    def test_insert_via_endpoint_real_queda_atribuido_al_usuario(self, db_motor, api_client):
        """
        Ejercita un INSERT real (POST /horarios) autenticado como un
        usuario de aplicación y verifica que auditoria.bitacora quedó
        con usuario_app_id/usuario_app_correo poblados — antes de la
        corrección, el trigger existía pero nadie fijaba los GUCs
        app.usuario_id/app.usuario_correo, así que siempre quedaban NULL.
        """
        rol_id = db_motor.execute(text(
            "INSERT INTO seguridad.roles (codigo, nombre, activo) "
            "VALUES ('ROL_HORARIOS_AUD', 'ROL_HORARIOS_AUD', TRUE) RETURNING id"
        )).scalar_one()
        modulo_id = _crear_modulo(db_motor, "HORARIOS")
        db_motor.execute(text(
            "INSERT INTO seguridad.permisos_rol "
            "(rol_id, modulo_id, alcance_datos, puede_consultar, puede_crear, "
            "puede_editar, puede_eliminar, puede_aprobar, puede_exportar) "
            "VALUES (:rol_id, :modulo_id, 'TOTAL', TRUE, TRUE, TRUE, FALSE, FALSE, FALSE)"
        ), {"rol_id": rol_id, "modulo_id": modulo_id})
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="crea_horarios@dae.test")

        db_motor.execute(text(
            "INSERT INTO asistencia.tipos_turno "
            "(codigo, nombre, duracion_jornada_minutos, modalidad_tiempo_extra, hora_entrada_desde) "
            "VALUES ('TURNO_AUD', 'Turno Aud', 420, 'NO_APLICA', '06:00')"
        ))
        tipo_turno_id = db_motor.execute(text(
            "SELECT id FROM asistencia.tipos_turno WHERE codigo = 'TURNO_AUD'"
        )).scalar_one()
        db_motor.commit()

        resp = api_client.post(
            "/api/v1/horarios",
            json={
                "codigo": "HORARIO_AUDITADO",
                "nombre": "Horario Auditado",
                "tipo_turno_id": tipo_turno_id,
                "hora_entrada": "08:00",
                "hora_salida": "16:00",
                "tolerancia_entrada_minutos": 10,
                "descanso_minutos": 0,
                "permite_tiempo_extra": True,
                "activo": True,
            },
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 201, resp.text

        row = db_motor.execute(text(
            "SELECT usuario_app_id, usuario_app_correo, operacion "
            "FROM auditoria.bitacora "
            "WHERE esquema = 'asistencia' AND tabla = 'horarios' "
            "  AND operacion = 'INSERT' "
            "ORDER BY id DESC LIMIT 1"
        )).mappings().first()

        assert row is not None, "El trigger de auditoria.bitacora no registró el INSERT."
        assert row["usuario_app_id"] == usuario_id
        assert row["usuario_app_correo"] == "crea_horarios@dae.test"


@pytest.mark.integration
class TestBitacoraListadoYFiltros:
    def _seed_evento(self, db, *, esquema="asistencia", tabla="horarios", operacion="INSERT", registro_id="999"):
        db.execute(text(
            "INSERT INTO auditoria.bitacora "
            "(esquema, tabla, operacion, registro_id, usuario_app_correo, datos_nuevos) "
            "VALUES (:esquema, :tabla, :operacion, :registro_id, 'seed@dae.test', '{\"id\": 999}'::jsonb)"
        ), {"esquema": esquema, "tabla": tabla, "operacion": operacion, "registro_id": registro_id})

    def test_filtra_por_esquema_tabla_operacion(self, db_motor, api_client):
        self._seed_evento(db_motor, esquema="seguridad", tabla="usuarios", operacion="UPDATE", registro_id="1")
        self._seed_evento(db_motor, esquema="asistencia", tabla="horarios", operacion="INSERT", registro_id="2")

        rol_id = _crear_rol_auditoria(db_motor, codigo="ROL_AUD_FILTRO")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="filtro_aud@dae.test")
        db_motor.commit()

        # Nota: crear el usuario de prueba (_crear_usuario) también
        # genera un INSERT real y auditado sobre seguridad.usuarios,
        # además del UPDATE sembrado a propósito — por eso se filtra
        # también por operación en vez de asumir un total fijo.
        resp = api_client.get(
            "/api/v1/auditoria/bitacora",
            params={"esquema": "seguridad", "tabla": "usuarios", "operacion": "UPDATE"},
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["esquema"] == "seguridad"
        assert body["items"][0]["operacion"] == "UPDATE"

    def test_detalle_incluye_datos_anteriores_nuevos_y_cambios(self, db_motor, api_client):
        db_motor.execute(text(
            "INSERT INTO auditoria.bitacora "
            "(esquema, tabla, operacion, registro_id, datos_anteriores, datos_nuevos, cambios) "
            "VALUES ('seguridad', 'usuarios', 'UPDATE', '5', "
            "'{\"estatus\": \"ACTIVO\"}'::jsonb, '{\"estatus\": \"BLOQUEADO\"}'::jsonb, "
            "'{\"estatus\": {\"antes\": \"ACTIVO\", \"despues\": \"BLOQUEADO\"}}'::jsonb) "
            "RETURNING id"
        ))
        evento_id = db_motor.execute(text(
            "SELECT id FROM auditoria.bitacora WHERE tabla = 'usuarios' AND registro_id = '5'"
        )).scalar_one()

        rol_id = _crear_rol_auditoria(db_motor, codigo="ROL_AUD_DETALLE")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="detalle_aud@dae.test")
        db_motor.commit()

        resp = api_client.get(
            f"/api/v1/auditoria/bitacora/{evento_id}",
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["datos_anteriores"]["estatus"] == "ACTIVO"
        assert body["datos_nuevos"]["estatus"] == "BLOQUEADO"
        assert body["cambios"]["estatus"]["despues"] == "BLOQUEADO"

    def test_evento_inexistente_recibe_404(self, db_motor, api_client):
        rol_id = _crear_rol_auditoria(db_motor, codigo="ROL_AUD_404")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="aud404@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/auditoria/bitacora/999999999",
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 404, resp.text

    def test_filtro_de_texto_libre(self, db_motor, api_client):
        self._seed_evento(db_motor, esquema="dispositivos", tabla="dispositivos", operacion="UPDATE", registro_id="77")

        rol_id = _crear_rol_auditoria(db_motor, codigo="ROL_AUD_Q")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="aud_q@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/auditoria/bitacora",
            params={"q": "dispositivos"},
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["total"] >= 1

    def test_export_csv(self, db_motor, api_client):
        self._seed_evento(db_motor)

        rol_id = _crear_rol_auditoria(db_motor, codigo="ROL_AUD_CSV")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="aud_csv@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/auditoria/bitacora/export",
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"].startswith("text/csv")
        assert "ID" in resp.text
        assert "Esquema" in resp.text


@pytest.mark.integration
class TestLoginAuditoria:
    def test_listado_real_desde_auth_login(self, db_motor, api_client):
        """
        POST /auth/login ya escribe en seguridad.login_auditoria
        (backend/app/api/routes/auth.py) en cada intento. Se ejercita
        un login fallido real y se verifica que aparece en el listado.
        """
        resp_login = api_client.post(
            "/api/v1/auth/login",
            json={"correo": "no-existe-aud@dae.test", "password": "loquesea"},
        )
        assert resp_login.status_code == 401

        rol_id = _crear_rol_auditoria(db_motor, codigo="ROL_AUD_LOGIN")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="aud_login@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/auditoria/login",
            params={"resultado": "FALLIDO", "q": "no-existe-aud"},
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] >= 1
        assert body["items"][0]["correo_intentado"] == "no-existe-aud@dae.test"
        assert body["items"][0]["resultado"] == "FALLIDO"

    def test_export_csv_login(self, db_motor, api_client):
        rol_id = _crear_rol_auditoria(db_motor, codigo="ROL_AUD_LOGIN_CSV")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="aud_login_csv@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/auditoria/login/export",
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"].startswith("text/csv")


@pytest.mark.integration
class TestAuditoriaResumen:
    def test_resumen_cuenta_operaciones_reales(self, db_motor, api_client):
        hoy = date.today()
        db_motor.execute(text(
            "INSERT INTO auditoria.bitacora (esquema, tabla, operacion, registro_id, datos_nuevos) "
            "VALUES ('seguridad', 'usuarios', 'INSERT', '1', '{}'::jsonb)"
        ))
        db_motor.execute(text(
            "INSERT INTO seguridad.login_auditoria (correo_intentado, resultado, motivo) "
            "VALUES ('resumen@dae.test', 'EXITOSO', 'LOGIN_OK')"
        ))

        rol_id = _crear_rol_auditoria(db_motor, codigo="ROL_AUD_RESUMEN")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="aud_resumen@dae.test")
        db_motor.commit()

        resp = api_client.get(
            "/api/v1/auditoria/resumen",
            params={"fecha_inicio": str(hoy), "fecha_fin": str(hoy)},
            headers=_auth_headers(usuario_id),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["bitacora"]["inserts"] >= 1
        assert body["bitacora"]["cambios_seguridad"] >= 1
        assert body["login"]["exitosos"] >= 1


@pytest.mark.integration
class TestAuditoriaScopesHTTP:
    def test_sin_permiso_recibe_403(self, db_motor, api_client):
        rol_id = _crear_rol_configuracion(db_motor, codigo="ROL_SIN_AUDITORIA")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="sinauditoria@dae.test")
        db_motor.commit()

        for path in ("/api/v1/auditoria/resumen", "/api/v1/auditoria/bitacora", "/api/v1/auditoria/login"):
            resp = api_client.get(path, headers=_auth_headers(usuario_id))
            assert resp.status_code == 403, f"{path}: {resp.text}"

    def test_sin_token_recibe_401(self, db_motor, api_client):
        resp = api_client.get("/api/v1/auditoria/bitacora")
        assert resp.status_code == 401, resp.text

    def test_auditor_puede_consultar_y_exportar_pero_no_existe_endpoint_de_escritura(self, db_motor, api_client):
        """
        AUDITOR debe ser de solo lectura: se verifica leyendo/exportando
        con éxito, y confirmando que /auditoria no expone ningún método
        de escritura (POST/PUT/PATCH/DELETE) que un cliente pudiera invocar.
        """
        rol_id = _crear_rol_auditoria(db_motor, codigo="ROL_AUDITOR_LECTURA", alcance="TOTAL")
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="auditor_lectura@dae.test")
        db_motor.commit()

        headers = _auth_headers(usuario_id)

        assert api_client.get("/api/v1/auditoria/resumen", headers=headers).status_code == 200
        assert api_client.get("/api/v1/auditoria/bitacora", headers=headers).status_code == 200
        assert api_client.get("/api/v1/auditoria/login", headers=headers).status_code == 200
        assert api_client.get("/api/v1/auditoria/bitacora/export", headers=headers).status_code == 200

        from app.main import app

        metodos_escritura = {"POST", "PUT", "PATCH", "DELETE"}
        rutas_auditoria_con_escritura = [
            route.path
            for route in app.routes
            if getattr(route, "path", "").startswith("/api/v1/auditoria")
            and metodos_escritura & set(getattr(route, "methods", set()) or set())
        ]
        assert rutas_auditoria_con_escritura == []
