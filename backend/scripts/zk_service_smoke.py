from pathlib import Path
import sys


# Permite importar app.services.zk_service cuando ejecutas desde scripts/
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


from app.services.zk_service import ZKDeviceService  # noqa: E402


def print_users_table(users):
    print("\nUsuarios detectados desde ZKDeviceService:\n")

    if not users:
        print("No se encontraron usuarios.")
        return

    print(f"{'UID':<6} {'User ID':<10} {'Nombre':<25} {'Privilegio':<10} {'PIN':<6} {'Protegido':<10}")
    print("-" * 80)

    for user in users:
        has_pin = "Sí" if user["has_pin"] else "No"
        protected = "Sí" if user["is_protected"] else "No"

        print(
            f"{user['uid']:<6} "
            f"{user['user_id']:<10} "
            f"{user['name']:<25} "
            f"{user['privilege']:<10} "
            f"{has_pin:<6} "
            f"{protected:<10}"
        )


def main():
    service = ZKDeviceService()

    print("Probando servicio ZK en modo seguro...")
    print("Esta prueba solo lista usuarios. No crea ni borra nada.")

    users = service.list_users(include_admin=True)
    print_users_table(users)

    print("\nPrueba finalizada correctamente.")


if __name__ == "__main__":
    main()