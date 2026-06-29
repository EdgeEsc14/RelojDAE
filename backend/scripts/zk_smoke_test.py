from zk import ZK, const
from contextlib import suppress
import random


ZK_IP = "10.254.26.251"
ZK_PORT = 4370
ZK_PASSWORD = 171


def clean_text(value):
    if value is None:
        return ""

    text = str(value).strip()
    text = "".join(ch for ch in text if ch.isprintable())
    return text.strip()


def get_next_uid(users):
    """
    Obtiene el siguiente UID interno disponible.
    El UID es el identificador interno del reloj.
    """
    existing_uids = [int(user.uid) for user in users if user.uid is not None]

    if not existing_uids:
        return 1

    return max(existing_uids) + 1


def generate_random_user_id(users):
    """
    Genera un User ID aleatorio que no exista en el reloj.
    Este es el ID visible del usuario en ZKTeco.
    """
    existing_user_ids = {
        clean_text(user.user_id)
        for user in users
        if clean_text(user.user_id)
    }

    for _ in range(100):
        candidate = str(random.randint(9000, 9999))

        if candidate not in existing_user_ids:
            return candidate

    raise Exception("No se pudo generar un user_id disponible.")


def print_users(users):
    print("\nUsuarios actuales en el reloj:\n")

    for user in users:
        privilege = "Admin" if user.privilege == const.USER_ADMIN else "User"

        print(f"+ UID #{user.uid}")
        print(f"  Name      : {clean_text(user.name)}")
        print(f"  User ID   : {clean_text(user.user_id)}")
        print(f"  Privilege : {privilege}")
        print("-" * 40)


def main():
    conn = None
    device_disabled = False

    try:
        zk = ZK(
            ZK_IP,
            port=ZK_PORT,
            timeout=5,
            password=ZK_PASSWORD,
            force_udp=False,
            ommit_ping=False
        )

        print("Conectando al reloj...")
        conn = zk.connect()

        print("Conexión exitosa.")
        conn.disable_device()
        device_disabled = True

        users_before = conn.get_users()

        print_users(users_before)

        new_uid = get_next_uid(users_before)
        new_user_id = generate_random_user_id(users_before)

        new_name = "Puebita de hoy"
        new_password = "1234"
        new_privilege = const.USER_DEFAULT
        new_group_id = ""

        print("\nRegistrando nuevo usuario de prueba...")
        print(f"  UID interno : {new_uid}")
        print(f"  User ID     : {new_user_id}")
        print(f"  Nombre      : {new_name}")
        print(f"  Password    : {new_password}")
        print(f"  Privilegio  : Usuario normal")

        conn.set_user(
            uid=new_uid,
            name=new_name,
            privilege=new_privilege,
            password=new_password,
            group_id=new_group_id,
            user_id=new_user_id
        )

        print("\nUsuario creado. Verificando lectura desde el reloj...")

        users_after = conn.get_users()

        created_user = None

        for user in users_after:
            if int(user.uid) == int(new_uid):
                created_user = user
                break

        if created_user:
            print("\nUsuario encontrado correctamente:\n")
            print(f"+ UID #{created_user.uid}")
            print(f"  Name      : {clean_text(created_user.name)}")
            print(f"  User ID   : {clean_text(created_user.user_id)}")
            print(f"  Privilege : {'Admin' if created_user.privilege == const.USER_ADMIN else 'User'}")
            print(f"  Password  : {clean_text(created_user.password)}")
        else:
            print("\nEl usuario se intentó crear, pero no apareció en la lectura posterior.")

    except Exception as e:
        print(f"Process terminate: {e}")

    finally:
        if conn:
            if device_disabled:
                print("\nRehabilitando dispositivo...")
                with suppress(Exception):
                    conn.enable_device()

            print("Cerrando conexión...")
            with suppress(Exception):
                conn.disconnect()


if __name__ == "__main__":
    main()