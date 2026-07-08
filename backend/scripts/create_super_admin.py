from pathlib import Path
import getpass
import sys

from sqlalchemy import text


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402


SUPER_ADMIN_ROLE_CODE = "SUPER_ADMIN"


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def ask_required(prompt):
    while True:
        value = clean_text(input(prompt))

        if value:
            return value

        print("Este valor es obligatorio.")


def ask_password():
    while True:
        password = getpass.getpass("Contraseña Super Admin: ")
        confirm = getpass.getpass("Confirmar contraseña: ")

        if not password:
            print("La contraseña no puede estar vacía.")
            continue

        if len(password) < 8:
            print("La contraseña debe tener al menos 8 caracteres.")
            continue

        if password != confirm:
            print("Las contraseñas no coinciden.")
            continue

        return password


def get_super_admin_role(db):
    query = text(
        """
        SELECT
            id,
            codigo,
            nombre
        FROM seguridad.roles
        WHERE codigo = :codigo
          AND activo = TRUE
        LIMIT 1
        """
    )

    role = db.execute(
        query,
        {"codigo": SUPER_ADMIN_ROLE_CODE},
    ).mappings().first()

    if role is None:
        raise ValueError("No existe rol activo SUPER_ADMIN en seguridad.roles.")

    return role


def user_exists(db, correo):
    query = text(
        """
        SELECT
            id,
            correo,
            correo_electronico,
            nombre_usuario,
            rol_id,
            rol,
            estatus
        FROM seguridad.usuarios
        WHERE LOWER(correo) = LOWER(:correo)
           OR LOWER(correo_electronico) = LOWER(:correo)
        LIMIT 1
        """
    )

    return db.execute(query, {"correo": correo}).mappings().first()


def create_super_admin(db, correo, nombre_usuario, password):
    role = get_super_admin_role(db)
    password_hash = hash_password(password)

    query = text(
        """
        INSERT INTO seguridad.usuarios (
            correo,
            correo_electronico,
            nombre_usuario,
            password_hash,
            rol_id,
            rol,
            estatus,
            correo_verificado,
            requiere_cambio_password,
            aprobado_en,
            fecha_creacion,
            fecha_modificacion
        )
        VALUES (
            :correo,
            :correo,
            :nombre_usuario,
            :password_hash,
            :rol_id,
            'super_admin',
            'ACTIVO',
            TRUE,
            FALSE,
            NOW(),
            NOW(),
            NOW()
        )
        RETURNING
            id,
            correo,
            correo_electronico,
            nombre_usuario,
            rol_id,
            rol,
            estatus,
            correo_verificado
        """
    )

    return db.execute(
        query,
        {
            "correo": correo,
            "nombre_usuario": nombre_usuario,
            "password_hash": password_hash,
            "rol_id": role["id"],
        },
    ).mappings().first()


def main():
    print("\nCrear primer Super Admin real\n")

    correo = ask_required("Correo: ")
    nombre_usuario = ask_required("Nombre de usuario: ")
    password = ask_password()

    db = SessionLocal()

    try:
        existing = user_exists(db, correo)

        if existing:
            print("\nYa existe un usuario con ese correo:")
            print(f"ID: {existing['id']}")
            print(f"Correo: {existing['correo']}")
            print(f"Correo electrónico: {existing['correo_electronico']}")
            print(f"Usuario: {existing['nombre_usuario']}")
            print(f"rol_id: {existing['rol_id']}")
            print(f"Rol: {existing['rol']}")
            print(f"Estatus: {existing['estatus']}")
            return

        user = create_super_admin(
            db=db,
            correo=correo,
            nombre_usuario=nombre_usuario,
            password=password,
        )

        db.commit()

        print("\nSuper Admin creado correctamente:")
        print(f"ID: {user['id']}")
        print(f"Correo: {user['correo']}")
        print(f"Correo electrónico: {user['correo_electronico']}")
        print(f"Usuario: {user['nombre_usuario']}")
        print(f"rol_id: {user['rol_id']}")
        print(f"Rol: {user['rol']}")
        print(f"Estatus: {user['estatus']}")
        print(f"Correo verificado: {user['correo_verificado']}")

    except Exception as exc:
        db.rollback()
        print(f"\nError creando Super Admin: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()