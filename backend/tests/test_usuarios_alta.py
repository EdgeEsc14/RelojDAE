"""
Tests HTTP del flujo de alta y administración de usuarios del sistema.

Verifican, contra los endpoints reales (TestClient + JWT real), que:
- SUPER_ADMIN y RH_ADMIN pueden crear cuentas vinculadas a empleados
  existentes, con reglas de autorización distintas entre ambos.
- SUPERVISOR, EMPLEADO y AUDITOR no pueden crear ni administrar cuentas,
  aunque el módulo SEGURIDAD les otorgue alcance TOTAL (la regla de
  negocio por rol es una capa adicional, no depende del scope genérico).
- La contraseña siempre es un hash (nunca texto plano) y la temporal
  generada por el backend solo se devuelve en la respuesta de creación.
- El primer login exige cambio de contraseña antes de usar el sistema.
"""

from sqlalchemy import text

import pytest

from app.core.security import hash_password


# ============================================================
# Helpers de seed
# ============================================================


def _crear_modulo_seguridad(db):
    db.execute(text(
        "INSERT INTO seguridad.modulos (codigo, nombre, activo) "
        "VALUES ('SEGURIDAD', 'SEGURIDAD', TRUE) "
        "ON CONFLICT (codigo) DO NOTHING"
    ))
    return db.execute(text(
        "SELECT id FROM seguridad.modulos WHERE codigo = 'SEGURIDAD'"
    )).scalar_one()


def _crear_rol_seguridad_total(db, codigo):
    """
    Crea (si no existe) un rol con alcance TOTAL y todas las acciones
    habilitadas para el módulo SEGURIDAD. Se usa para TODOS los roles
    de prueba (incluidos SUPERVISOR/EMPLEADO/AUDITOR) a propósito: así
    la prueba demuestra que el bloqueo viene de la regla de negocio por
    rol, no de que el módulo les niegue el alcance genérico.
    """
    existente = db.execute(text(
        "SELECT id FROM seguridad.roles WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar()

    if existente is not None:
        return existente

    rol_id = db.execute(text(
        "INSERT INTO seguridad.roles (codigo, nombre, activo) "
        "VALUES (:codigo, :codigo, TRUE) RETURNING id"
    ), {"codigo": codigo}).scalar_one()

    modulo_id = _crear_modulo_seguridad(db)

    db.execute(text(
        "INSERT INTO seguridad.permisos_rol "
        "(rol_id, modulo_id, alcance_datos, puede_consultar, puede_crear, "
        "puede_editar, puede_eliminar, puede_aprobar, puede_exportar) "
        "VALUES (:rol_id, :modulo_id, 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE)"
    ), {"rol_id": rol_id, "modulo_id": modulo_id})

    return rol_id


def _crear_usuario_actor(db, *, rol_codigo, correo, password="Actor-Pass-1!"):
    """Crea una cuenta ya utilizable (requiere_cambio_password=FALSE)
    para actuar como quien realiza la operación HTTP."""
    rol_id = _crear_rol_seguridad_total(db, rol_codigo)

    usuario_id = db.execute(text(
        "INSERT INTO seguridad.usuarios "
        "(rol_id, rol, correo, correo_electronico, password_hash, "
        "estatus, activo, requiere_cambio_password) "
        "VALUES (:rol_id, :rol_texto, :correo, :correo, :password_hash, "
        "'ACTIVO', TRUE, FALSE) RETURNING id"
    ), {
        "rol_id": rol_id,
        "rol_texto": rol_codigo.lower(),
        "correo": correo,
        "password_hash": hash_password(password),
    }).scalar_one()

    return usuario_id


def _crear_unidad_y_puesto(db):
    db.execute(text(
        "INSERT INTO organizacion.unidades_organizacionales (codigo, nombre, activo) "
        "VALUES ('UNIDAD_USR', 'Unidad Usuarios', TRUE) "
        "ON CONFLICT (codigo) DO NOTHING"
    ))
    db.execute(text(
        "INSERT INTO organizacion.puestos (codigo, nombre, nivel_jerarquico, activo) "
        "VALUES ('PUESTO_USR', 'Puesto Usuarios', 1, TRUE) "
        "ON CONFLICT (codigo) DO NOTHING"
    ))
    unidad_id = db.execute(text(
        "SELECT id FROM organizacion.unidades_organizacionales WHERE codigo='UNIDAD_USR'"
    )).scalar_one()
    puesto_id = db.execute(text(
        "SELECT id FROM organizacion.puestos WHERE codigo='PUESTO_USR'"
    )).scalar_one()
    return unidad_id, puesto_id


def _crear_empleado(db, codigo, unidad_id, puesto_id, estatus="ACTIVO"):
    db.execute(text(
        "INSERT INTO personal.empleados "
        "(codigo_empleado, nombres, apellido_paterno, correo, "
        "unidad_organizacional_id, puesto_id, estatus) "
        "VALUES (:codigo, 'TEST', 'USR', :correo, :unidad_id, :puesto_id, :estatus)"
    ), {
        "codigo": codigo,
        "correo": f"{codigo.lower()}@dae.test",
        "unidad_id": unidad_id,
        "puesto_id": puesto_id,
        "estatus": estatus,
    })
    return db.execute(text(
        "SELECT id FROM personal.empleados WHERE codigo_empleado = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _auth_headers_login(api_client, correo, password):
    resp = api_client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, resp.json()


def _auth_headers_directo(db, usuario_id):
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(usuario_id)})
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# 1-2: creación exitosa por SUPER_ADMIN y RH_ADMIN
# ============================================================


@pytest.mark.integration
class TestAltaUsuarios:

    def test_super_admin_puede_crear_usuario(self, db_motor, api_client):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="SUPER_ADMIN", correo="actor.super@dae.test"
        )
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(db_motor, "EMP-ALTA-01", unidad_id, puesto_id)
        rh_admin_id = _crear_rol_seguridad_total(db_motor, "RH_ADMIN")
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        resp = api_client.post(
            "/api/v1/usuarios",
            json={
                "correo_electronico": "nueva.cuenta.1@dae.test",
                "rol_id": rh_admin_id,
                "empleado_id": empleado_id,
            },
            headers=headers,
        )

        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["correo_electronico"] == "nueva.cuenta.1@dae.test"
        assert body["requiere_cambio_password"] is True
        assert "password_temporal" in body
        assert len(body["password_temporal"]) >= 12
        assert "password_hash" not in body
        assert "password" not in body

    def test_rh_admin_puede_crear_usuario_permitido(self, db_motor, api_client):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="RH_ADMIN", correo="actor.rh@dae.test"
        )
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(db_motor, "EMP-ALTA-02", unidad_id, puesto_id)
        empleado_rol_id = _crear_rol_seguridad_total(db_motor, "EMPLEADO")
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        resp = api_client.post(
            "/api/v1/usuarios",
            json={
                "correo_electronico": "nueva.cuenta.2@dae.test",
                "rol_id": empleado_rol_id,
                "empleado_id": empleado_id,
            },
            headers=headers,
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["rol_codigo"] == "EMPLEADO"

    # ============================================================
    # 3-5: restricciones de RH_ADMIN frente a SUPER_ADMIN
    # ============================================================

    def test_rh_admin_no_puede_crear_super_admin(self, db_motor, api_client):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="RH_ADMIN", correo="actor.rh2@dae.test"
        )
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(db_motor, "EMP-ALTA-03", unidad_id, puesto_id)
        super_admin_rol_id = _crear_rol_seguridad_total(db_motor, "SUPER_ADMIN")
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        resp = api_client.post(
            "/api/v1/usuarios",
            json={
                "correo_electronico": "intento.super@dae.test",
                "rol_id": super_admin_rol_id,
                "empleado_id": empleado_id,
            },
            headers=headers,
        )

        assert resp.status_code == 403, resp.text

    def test_rh_admin_no_puede_promover_a_super_admin(self, db_motor, api_client):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="RH_ADMIN", correo="actor.rh3@dae.test"
        )
        empleado_rol_id = _crear_rol_seguridad_total(db_motor, "EMPLEADO")
        super_admin_rol_id = _crear_rol_seguridad_total(db_motor, "SUPER_ADMIN")
        objetivo_id = _crear_usuario_actor(
            db_motor, rol_codigo="EMPLEADO", correo="objetivo.promocion@dae.test"
        )
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        resp = api_client.patch(
            f"/api/v1/usuarios/{objetivo_id}",
            json={"rol_id": super_admin_rol_id},
            headers=headers,
        )

        assert resp.status_code == 403, resp.text

        rol_actual = db_motor.execute(text(
            "SELECT rol_id FROM seguridad.usuarios WHERE id = :id"
        ), {"id": objetivo_id}).scalar_one()
        assert rol_actual == empleado_rol_id

    def test_rh_admin_no_puede_modificar_ni_desactivar_super_admin(self, db_motor, api_client):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="RH_ADMIN", correo="actor.rh4@dae.test"
        )
        objetivo_id = _crear_usuario_actor(
            db_motor, rol_codigo="SUPER_ADMIN", correo="objetivo.super@dae.test"
        )
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        resp_patch = api_client.patch(
            f"/api/v1/usuarios/{objetivo_id}",
            json={"nombre_usuario": "nuevo_nombre"},
            headers=headers,
        )
        assert resp_patch.status_code == 403, resp_patch.text

        resp_delete = api_client.delete(
            f"/api/v1/usuarios/{objetivo_id}", headers=headers
        )
        assert resp_delete.status_code == 403, resp_delete.text

        estatus_actual = db_motor.execute(text(
            "SELECT estatus FROM seguridad.usuarios WHERE id = :id"
        ), {"id": objetivo_id}).scalar_one()
        assert estatus_actual == "ACTIVO"

    # ============================================================
    # 6-8: roles sin permiso para crear/administrar cuentas
    # ============================================================

    @pytest.mark.parametrize("rol_codigo", ["SUPERVISOR", "EMPLEADO", "AUDITOR"])
    def test_rol_sin_permiso_no_puede_crear_usuarios(self, db_motor, api_client, rol_codigo):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo=rol_codigo, correo=f"actor.{rol_codigo.lower()}@dae.test"
        )
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(
            db_motor, f"EMP-ALTA-{rol_codigo}", unidad_id, puesto_id
        )
        empleado_rol_id = _crear_rol_seguridad_total(db_motor, "EMPLEADO")
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        resp = api_client.post(
            "/api/v1/usuarios",
            json={
                "correo_electronico": f"intento.{rol_codigo.lower()}@dae.test",
                "rol_id": empleado_rol_id,
                "empleado_id": empleado_id,
            },
            headers=headers,
        )

        assert resp.status_code == 403, resp.text

    def test_auditor_no_puede_modificar_cuentas(self, db_motor, api_client):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="AUDITOR", correo="actor.auditor2@dae.test"
        )
        objetivo_id = _crear_usuario_actor(
            db_motor, rol_codigo="EMPLEADO", correo="objetivo.auditor@dae.test"
        )
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        resp = api_client.patch(
            f"/api/v1/usuarios/{objetivo_id}",
            json={"nombre_usuario": "cambio_no_permitido"},
            headers=headers,
        )
        assert resp.status_code == 403, resp.text

    # ============================================================
    # 9-10: validaciones de datos
    # ============================================================

    def test_correo_duplicado_es_rechazado(self, db_motor, api_client):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="SUPER_ADMIN", correo="actor.dup@dae.test"
        )
        empleado_rol_id = _crear_rol_seguridad_total(db_motor, "EMPLEADO")
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        payload = {
            "correo_electronico": "duplicado@dae.test",
            "rol_id": empleado_rol_id,
        }

        primero = api_client.post("/api/v1/usuarios", json=payload, headers=headers)
        assert primero.status_code == 201, primero.text

        segundo = api_client.post("/api/v1/usuarios", json=payload, headers=headers)
        assert segundo.status_code == 400, segundo.text

    def test_empleado_ya_vinculado_es_rechazado(self, db_motor, api_client):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="SUPER_ADMIN", correo="actor.vinc@dae.test"
        )
        unidad_id, puesto_id = _crear_unidad_y_puesto(db_motor)
        empleado_id = _crear_empleado(db_motor, "EMP-VINCULADO", unidad_id, puesto_id)
        empleado_rol_id = _crear_rol_seguridad_total(db_motor, "EMPLEADO")
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        primero = api_client.post(
            "/api/v1/usuarios",
            json={
                "correo_electronico": "primera.cuenta@dae.test",
                "rol_id": empleado_rol_id,
                "empleado_id": empleado_id,
            },
            headers=headers,
        )
        assert primero.status_code == 201, primero.text

        segundo = api_client.post(
            "/api/v1/usuarios",
            json={
                "correo_electronico": "segunda.cuenta@dae.test",
                "rol_id": empleado_rol_id,
                "empleado_id": empleado_id,
            },
            headers=headers,
        )
        assert segundo.status_code == 400, segundo.text

    # ============================================================
    # 11: la contraseña se almacena como hash
    # ============================================================

    def test_password_almacenada_es_hash(self, db_motor, api_client):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="SUPER_ADMIN", correo="actor.hash@dae.test"
        )
        empleado_rol_id = _crear_rol_seguridad_total(db_motor, "EMPLEADO")
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)

        resp = api_client.post(
            "/api/v1/usuarios",
            json={
                "correo_electronico": "hash.check@dae.test",
                "rol_id": empleado_rol_id,
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        password_temporal = resp.json()["password_temporal"]

        stored_hash = db_motor.execute(text(
            "SELECT password_hash FROM seguridad.usuarios WHERE correo_electronico = 'hash.check@dae.test'"
        )).scalar_one()

        assert stored_hash != password_temporal
        assert stored_hash.startswith("pbkdf2_sha256$")


# ============================================================
# 12-15: primer login, cambio de contraseña, cuenta inactiva
# ============================================================


@pytest.mark.integration
class TestPrimerLoginYCambioPassword:

    def _crear_cuenta_con_temporal(self, db_motor, api_client, correo="primerlogin@dae.test"):
        actor_id = _crear_usuario_actor(
            db_motor, rol_codigo="SUPER_ADMIN", correo="actor.primerlogin@dae.test"
        )
        empleado_rol_id = _crear_rol_seguridad_total(db_motor, "EMPLEADO")
        db_motor.commit()

        headers = _auth_headers_directo(db_motor, actor_id)
        resp = api_client.post(
            "/api/v1/usuarios",
            json={"correo_electronico": correo, "rol_id": empleado_rol_id},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["password_temporal"]

    def test_primer_login_obliga_a_cambio_de_password(self, db_motor, api_client):
        correo = "primerlogin1@dae.test"
        password_temporal = self._crear_cuenta_con_temporal(db_motor, api_client, correo)

        login_headers, login_body = _auth_headers_login(api_client, correo, password_temporal)
        assert login_body["user"]["requiere_cambio_password"] is True

        resp_protegido = api_client.get("/api/v1/usuarios", headers=login_headers)
        assert resp_protegido.status_code == 403, resp_protegido.text
        assert "contraseña" in resp_protegido.json()["detail"].lower()

    def test_login_normal_funciona_despues_del_cambio(self, db_motor, api_client):
        correo = "primerlogin2@dae.test"
        password_temporal = self._crear_cuenta_con_temporal(db_motor, api_client, correo)

        login_headers, _ = _auth_headers_login(api_client, correo, password_temporal)

        resp_cambio = api_client.post(
            "/api/v1/auth/change-password",
            json={
                "password_actual": password_temporal,
                "password_nueva": "NuevaClaveSegura#2026",
            },
            headers=login_headers,
        )
        assert resp_cambio.status_code == 200, resp_cambio.text
        assert resp_cambio.json()["requiere_cambio_password"] is False

        nuevo_login_headers, nuevo_login_body = _auth_headers_login(
            api_client, correo, "NuevaClaveSegura#2026"
        )
        assert nuevo_login_body["user"]["requiere_cambio_password"] is False

        resp_protegido = api_client.get("/api/v1/usuarios", headers=nuevo_login_headers)
        assert resp_protegido.status_code == 200, resp_protegido.text

    def test_password_temporal_deja_de_funcionar_tras_el_cambio(self, db_motor, api_client):
        correo = "primerlogin3@dae.test"
        password_temporal = self._crear_cuenta_con_temporal(db_motor, api_client, correo)

        login_headers, _ = _auth_headers_login(api_client, correo, password_temporal)

        api_client.post(
            "/api/v1/auth/change-password",
            json={
                "password_actual": password_temporal,
                "password_nueva": "OtraClaveSegura#2026",
            },
            headers=login_headers,
        )

        resp_login_viejo = api_client.post(
            "/api/v1/auth/login",
            json={"correo": correo, "password": password_temporal},
        )
        assert resp_login_viejo.status_code == 401, resp_login_viejo.text

    def test_usuario_inactivo_no_puede_iniciar_sesion(self, db_motor, api_client):
        password = "ClaveInactivo#2026"
        db_motor.execute(text(
            "INSERT INTO seguridad.roles (codigo, nombre, activo) "
            "VALUES ('EMPLEADO', 'EMPLEADO', TRUE) ON CONFLICT (codigo) DO NOTHING"
        ))
        rol_id = db_motor.execute(text(
            "SELECT id FROM seguridad.roles WHERE codigo = 'EMPLEADO'"
        )).scalar_one()
        db_motor.execute(text(
            "INSERT INTO seguridad.usuarios "
            "(rol_id, rol, correo, correo_electronico, password_hash, estatus, activo) "
            "VALUES (:rol_id, 'empleado', 'inactivo@dae.test', 'inactivo@dae.test', "
            ":password_hash, 'INACTIVO', FALSE)"
        ), {"rol_id": rol_id, "password_hash": hash_password(password)})
        db_motor.commit()

        resp = api_client.post(
            "/api/v1/auth/login",
            json={"correo": "inactivo@dae.test", "password": password},
        )
        assert resp.status_code == 403, resp.text
