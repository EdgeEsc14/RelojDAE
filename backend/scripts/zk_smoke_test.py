from zk import ZK


ZK_IP = "10.254.26.251"
ZK_PORT = 4370
ZK_PASSWORD = 0
TIMEOUT_SECONDS = 10


def main():
    print("=== ZKTeco Smoke Test ===")
    print(f"IP: {ZK_IP}")
    print(f"Puerto: {ZK_PORT}")
    print(f"Password SDK: {ZK_PASSWORD}")
    print()

    conn = None

    try:
        zk = ZK(
            ZK_IP,
            port=ZK_PORT,
            timeout=TIMEOUT_SECONDS,
            password=ZK_PASSWORD,
            force_udp=False,
            ommit_ping=False,
        )

        print("Conectando al reloj...")
        conn = zk.connect()
        print("Conexión OK")

        print()
        print("Información del dispositivo:")

        try:
            print("Firmware:", conn.get_firmware_version())
        except Exception as error:
            print("No se pudo leer firmware:", error)

        try:
            print("Serial:", conn.get_serialnumber())
        except Exception as error:
            print("No se pudo leer serial:", error)

        try:
            print("Platform:", conn.get_platform())
        except Exception as error:
            print("No se pudo leer platform:", error)

        try:
            print("Device name:", conn.get_device_name())
        except Exception as error:
            print("No se pudo leer device name:", error)

        print()
        print("Leyendo usuarios...")
        users = conn.get_users()
        print(f"Usuarios encontrados: {len(users)}")

        for user in users[:20]:
            print(
                {
                    "uid": user.uid,
                    "user_id": user.user_id,
                    "name": user.name,
                    "privilege": user.privilege,
                    "password": user.password,
                    "group_id": user.group_id,
                    "card": user.card,
                }
            )

        print()
        print("Leyendo marcaciones...")
        attendances = conn.get_attendance()
        print(f"Marcaciones encontradas: {len(attendances)}")

        for attendance in attendances[:20]:
            print(
                {
                    "uid": attendance.uid,
                    "user_id": attendance.user_id,
                    "timestamp": attendance.timestamp,
                    "status": attendance.status,
                    "punch": attendance.punch,
                }
            )

        print()
        print("Prueba terminada correctamente. No se modificó el reloj.")

    except Exception as error:
        print()
        print("ERROR al conectar o leer el reloj:")
        print(repr(error))

    finally:
        if conn:
            try:
                conn.disconnect()
                print("Conexión cerrada.")
            except Exception:
                pass


if __name__ == "__main__":
    main()