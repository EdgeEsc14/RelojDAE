from zk import ZK
import time

ZK_IP = "192.168.137.147"
ZK_PORT = 4370
ZK_PASSWORD = 171
ZK_TIMEOUT = 5

TARGET_USER_ID = "5"
VOICE_INDEX = 10

last_attendance_uid = None


def connect_zk():
    zk = ZK(
        ZK_IP,
        port=ZK_PORT,
        timeout=ZK_TIMEOUT,
        password=ZK_PASSWORD,
        force_udp=False,
        ommit_ping=False
    )
    return zk.connect()


while True:
    conn = None

    try:
        conn = connect_zk()
        conn.disable_device()

        attendances = conn.get_attendance()

        if attendances:
            attendances = sorted(attendances, key=lambda x: x.uid)

            if last_attendance_uid is None:
                last_attendance_uid = attendances[-1].uid
                print(f"Inicializado en UID {last_attendance_uid}")

            else:
                new_attendances = [
                    att for att in attendances
                    if att.uid > last_attendance_uid
                ]

                for att in new_attendances:
                    print(
                        f"Nueva checada | UID registro: {att.uid} | "
                        f"User ID: {att.user_id} | Hora: {att.timestamp} | "
                        f"Punch: {att.punch} | Status: {att.status}"
                    )

                    if str(att.user_id) == TARGET_USER_ID:
                        print("User ID 7 detectado. Reproduciendo sonido 10...")
                        conn.test_voice(index=VOICE_INDEX)

                    last_attendance_uid = max(last_attendance_uid, att.uid)

        conn.enable_device()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if conn:
            try:
                conn.enable_device()
                conn.disconnect()
            except Exception:
                pass

    time.sleep(1)