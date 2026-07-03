from pathlib import Path
import sys


# Permite importar app.services.zk_service desde backend/scripts
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


from app.services.zk_service import ZKDeviceService  # noqa: E402


# ============================================================
# Configuración de seguridad
# ============================================================

TARGET_NAMES = {
    "Puebita de hoy",
}

TARGET_USER_IDS = {
    "9821",
}

# Primero déjalo en False.
# False = solo muestra qué borraría.
# True  = intenta borrar candidatos.
EXECUTE_DELETE = True

# Protección extra: aunque EXECUTE_DELETE sea True, este texto debe coincidir.
CONFIRM_TEXT = "BORRAR_PREuebita"

# Para ejecutar realmente:
# EXECUTE_DELETE = True
# CONFIRM_TEXT = "BORRAR_PUEBITA"


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def is_candidate(user):
    name = clean_text(user.get("name"))
    user_id = clean_text(user.get("user_id"))

    if user.get("is_admin") or user.get("is_protected"):
        return False

    return name in TARGET_NAMES or user_id in TARGET_USER_IDS


def main():
    service = ZKDeviceService()

    print("Leyendo usuarios actuales del reloj...")
    users = service.list_users(include_admin=True)

    candidates = [user for user in users if is_candidate(user)]

    print("\nCandidatos encontrados para limpieza:\n")

    if not candidates:
        print("No se encontraron usuarios de prueba para borrar.")
        return

    for user in candidates:
        print(f"+ UID interno : {user['uid']}")
        print(f"  User ID     : {user['user_id']}")
        print(f"  Nombre      : {user['name']}")
        print(f"  Privilegio  : {user['privilege']}")
        print(f"  Protegido   : {user['is_protected']}")
        print("-" * 50)

    if not EXECUTE_DELETE:
        print("\nMODO SIMULACIÓN.")
        print("No se borró nada.")
        print("\nPara borrar realmente:")
        print("1. Cambia EXECUTE_DELETE = True")
        print('2. Cambia CONFIRM_TEXT = "BORRAR_PUEBITA"')
        print("3. Cambia ZK_ALLOW_WRITES=true en backend/.env")
        return

    if CONFIRM_TEXT != "BORRAR_PUEBITA":
        print("\nBloqueado por seguridad.")
        print('Para borrar realmente, CONFIRM_TEXT debe ser "BORRAR_PUEBITA".')
        return

    print("\nBorrando usuarios de prueba...")

    for user in candidates:
        user_id = user["user_id"]

        print(f"Borrando User ID {user_id} | {user['name']}")

        result = service.delete_user_by_user_id(
            user_id=user_id,
            dry_run=False,
        )

        print(result)

    print("\nVerificando limpieza...")
    users_after = service.list_users(include_admin=True)
    remaining = [user for user in users_after if is_candidate(user)]

    if remaining:
        print("\nAdvertencia: todavía quedaron candidatos:")
        for user in remaining:
            print(f"UID {user['uid']} | User ID {user['user_id']} | {user['name']}")
    else:
        print("\nLimpieza completada. Ya no hay usuarios de prueba detectados.")


if __name__ == "__main__":
    main()