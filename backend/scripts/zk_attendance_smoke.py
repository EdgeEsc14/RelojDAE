from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


from app.services.zk_service import ZKDeviceService  # noqa: E402


LIMIT = 50


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def attendance_to_dict(attendance):
    return {
        "uid": getattr(attendance, "uid", None),
        "user_id": clean_text(getattr(attendance, "user_id", "")),
        "timestamp": getattr(attendance, "timestamp", None),
        "status": getattr(attendance, "status", None),
        "punch": getattr(attendance, "punch", None),
    }


def main():
    service = ZKDeviceService()

    print("Conectando al reloj para leer marcaciones...")
    print("Modo solo lectura. No se modifica el dispositivo.\n")

    with service.connection(disable_device=True) as conn:
        attendances = conn.get_attendance()

    records = [attendance_to_dict(item) for item in attendances]

    records = sorted(
        records,
        key=lambda item: item["timestamp"] or "",
        reverse=True,
    )

    print(f"Marcaciones totales encontradas: {len(records)}")
    print(f"Mostrando últimas {min(LIMIT, len(records))} marcaciones:\n")

    for item in records[:LIMIT]:
        print(f"User ID   : {item['user_id']}")
        print(f"UID       : {item['uid']}")
        print(f"Fecha/hora: {item['timestamp']}")
        print(f"Status    : {item['status']}")
        print(f"Punch     : {item['punch']}")
        print("-" * 50)


if __name__ == "__main__":
    main()