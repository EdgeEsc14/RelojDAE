from datetime import datetime
from pathlib import Path
import os
import sys

from dotenv import load_dotenv
from zk import ZK


BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(ENV_PATH)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "si", "sí"}


def main():
    zk_ip = os.getenv("ZK_IP", "192.168.137.218")
    zk_port = int(os.getenv("ZK_PORT", "4370"))
    zk_password = int(os.getenv("ZK_PASSWORD", "0"))
    zk_timeout = int(os.getenv("ZK_TIMEOUT", "10"))
    zk_force_udp = env_bool("ZK_FORCE_UDP", False)
    zk_ommit_ping = env_bool("ZK_OMMIT_PING", True)

    now = datetime.now().replace(microsecond=0)

    print("Sincronizando hora del reloj ZKTeco")
    print(f"IP: {zk_ip}")
    print(f"Puerto: {zk_port}")
    print(f"Hora PC: {now}")

    zk = ZK(
        zk_ip,
        port=zk_port,
        timeout=zk_timeout,
        password=zk_password,
        force_udp=zk_force_udp,
        ommit_ping=zk_ommit_ping,
    )

    conn = None

    try:
        conn = zk.connect()
        conn.disable_device()

        before = conn.get_time()
        print(f"Hora actual del reloj antes: {before}")

        conn.set_time(now)

        after = conn.get_time()
        print(f"Hora actual del reloj después: {after}")

        conn.enable_device()

        print("Hora sincronizada correctamente.")

    except Exception as exc:
        print(f"Error sincronizando hora: {exc}")
        sys.exit(1)

    finally:
        if conn:
            try:
                conn.enable_device()
            except Exception:
                pass

            conn.disconnect()


if __name__ == "__main__":
    main()