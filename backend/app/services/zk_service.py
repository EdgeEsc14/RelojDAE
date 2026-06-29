from __future__ import annotations

from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
import os
from typing import Any, Optional

from dotenv import load_dotenv
from zk import ZK, const


# ============================================================
# Cargar .env del backend
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(ENV_PATH)


# ============================================================
# Utilidades de configuración
# ============================================================

def parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"1", "true", "yes", "y", "si", "sí"}


def parse_csv_set(value: Optional[str]) -> set[str]:
    if not value:
        return set()

    return {
        item.strip()
        for item in value.split(",")
        if item.strip()
    }


@dataclass(frozen=True)
class ZKSettings:
    ip: str
    port: int
    password: int
    timeout: int
    force_udp: bool
    ommit_ping: bool
    allow_writes: bool
    protected_user_ids: set[str]
    protected_names: set[str]

    @classmethod
    def from_env(cls) -> "ZKSettings":
        return cls(
            ip=os.getenv("ZK_IP", "10.254.26.251"),
            port=int(os.getenv("ZK_PORT", "4370")),
            password=int(os.getenv("ZK_PASSWORD", "171")),
            timeout=int(os.getenv("ZK_TIMEOUT", "5")),
            force_udp=parse_bool(os.getenv("ZK_FORCE_UDP"), default=False),
            ommit_ping=parse_bool(os.getenv("ZK_OMMIT_PING"), default=False),
            allow_writes=parse_bool(os.getenv("ZK_ALLOW_WRITES"), default=False),
            protected_user_ids=parse_csv_set(os.getenv("ZK_PROTECTED_USER_IDS", "1")),
            protected_names={
                name.lower()
                for name in parse_csv_set(os.getenv("ZK_PROTECTED_NAMES", "admin"))
            },
        )


# ============================================================
# Utilidades de normalización
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()
    text = "".join(ch for ch in text if ch.isprintable())
    return text.strip()


def normalize_group_id(value: Any) -> str:
    """
    Algunos relojes devuelven group_id como carácter de control.
    Ejemplo: '\x01'. Eso puede interpretarse como grupo 1.
    """
    if value is None:
        return ""

    text = str(value)

    if len(text) == 1 and ord(text) < 32:
        return str(ord(text))

    return clean_text(text)


def get_privilege_label(privilege: Any) -> str:
    if privilege == const.USER_ADMIN:
        return "Admin"

    return "User"


def get_user_default_privilege() -> int:
    """
    Algunas versiones de pyzk tienen const.USER_DEFAULT.
    Si no existe, el valor estándar para usuario normal suele ser 0.
    """
    return getattr(const, "USER_DEFAULT", 0)


# ============================================================
# DTO normalizado
# ============================================================

@dataclass
class ZKUserDTO:
    uid: int
    user_id: str
    name: str
    privilege: str
    group_id: str
    has_pin: bool
    is_admin: bool
    is_protected: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "user_id": self.user_id,
            "name": self.name,
            "privilege": self.privilege,
            "group_id": self.group_id,
            "has_pin": self.has_pin,
            "is_admin": self.is_admin,
            "is_protected": self.is_protected,
        }


# ============================================================
# Servicio principal
# ============================================================

class ZKDeviceService:
    """
    Servicio seguro para comunicación con reloj ZKTeco mediante pyzk.

    Reglas de seguridad:
    - No imprime PINs.
    - No borra usuarios protegidos.
    - No permite escrituras si ZK_ALLOW_WRITES=false.
    - Siempre intenta reactivar el dispositivo en finally.
    """

    def __init__(self, settings: Optional[ZKSettings] = None) -> None:
        self.settings = settings or ZKSettings.from_env()

    def _build_client(self) -> ZK:
        return ZK(
            self.settings.ip,
            port=self.settings.port,
            timeout=self.settings.timeout,
            password=self.settings.password,
            force_udp=self.settings.force_udp,
            ommit_ping=self.settings.ommit_ping,
        )

    @contextmanager
    def connection(self, disable_device: bool = True):
        conn = None
        device_disabled = False

        try:
            zk = self._build_client()
            conn = zk.connect()

            if disable_device:
                conn.disable_device()
                device_disabled = True

            yield conn

        finally:
            if conn:
                if device_disabled:
                    with suppress(Exception):
                        conn.enable_device()

                with suppress(Exception):
                    conn.disconnect()

    def _is_protected_user(
        self,
        uid: Any,
        user_id: Any,
        name: Any,
        privilege: Any,
    ) -> bool:
        clean_user_id = clean_text(user_id)
        clean_name = clean_text(name).lower()

        if clean_user_id in self.settings.protected_user_ids:
            return True

        if clean_name in self.settings.protected_names:
            return True

        if privilege == const.USER_ADMIN:
            return True

        return False

    def _normalize_user(self, user: Any) -> ZKUserDTO:
        uid = int(user.uid)
        user_id = clean_text(user.user_id)
        name = clean_text(user.name)
        privilege = get_privilege_label(user.privilege)
        group_id = normalize_group_id(user.group_id)
        has_pin = bool(clean_text(user.password))
        is_admin = user.privilege == const.USER_ADMIN

        is_protected = self._is_protected_user(
            uid=uid,
            user_id=user_id,
            name=name,
            privilege=user.privilege,
        )

        return ZKUserDTO(
            uid=uid,
            user_id=user_id,
            name=name,
            privilege=privilege,
            group_id=group_id,
            has_pin=has_pin,
            is_admin=is_admin,
            is_protected=is_protected,
        )

    def list_users(self, include_admin: bool = True) -> list[dict[str, Any]]:
        """
        Lista usuarios del reloj.

        No devuelve el PIN. Solo devuelve has_pin=True/False.
        """
        with self.connection(disable_device=True) as conn:
            raw_users = conn.get_users()

        users = [self._normalize_user(user) for user in raw_users]

        if not include_admin:
            users = [user for user in users if not user.is_admin]

        return [user.to_dict() for user in users]

    def get_user_by_user_id(self, user_id: str) -> Optional[dict[str, Any]]:
        user_id = clean_text(user_id)

        users = self.list_users(include_admin=True)

        for user in users:
            if user["user_id"] == user_id:
                return user

        return None

    def user_id_exists(self, user_id: str) -> bool:
        return self.get_user_by_user_id(user_id) is not None

    def get_next_uid(self) -> int:
        users = self.list_users(include_admin=True)

        existing_uids = [
            int(user["uid"])
            for user in users
            if user.get("uid") is not None
        ]

        if not existing_uids:
            return 1

        return max(existing_uids) + 1

    def _assert_writes_enabled(self) -> None:
        if not self.settings.allow_writes:
            raise PermissionError(
                "Escrituras bloqueadas. Cambia ZK_ALLOW_WRITES=true en .env "
                "solo cuando quieras permitir altas/bajas en el reloj."
            )

    def create_user(
        self,
        *,
        name: str,
        user_id: str,
        password: str = "",
        group_id: str = "",
        privilege: str = "user",
    ) -> dict[str, Any]:
        """
        Crea usuario en el reloj.

        Requiere:
        ZK_ALLOW_WRITES=true

        No registra huella. Solo crea usuario con ID, nombre y PIN opcional.
        """
        self._assert_writes_enabled()

        name = clean_text(name)
        user_id = clean_text(user_id)
        password = clean_text(password)
        group_id = clean_text(group_id)

        if not name:
            raise ValueError("El nombre no puede estar vacío.")

        if not user_id:
            raise ValueError("El user_id no puede estar vacío.")

        if not user_id.isdigit():
            raise ValueError("El user_id debe ser numérico para este reloj.")

        if user_id in self.settings.protected_user_ids:
            raise ValueError(f"El user_id {user_id} está protegido.")

        if name.lower() in self.settings.protected_names:
            raise ValueError(f"El nombre {name} está protegido.")

        if self.user_id_exists(user_id):
            raise ValueError(f"Ya existe un usuario con user_id={user_id} en el reloj.")

        if privilege.lower() == "admin":
            zk_privilege = const.USER_ADMIN
        else:
            zk_privilege = get_user_default_privilege()

        new_uid = self.get_next_uid()

        with self.connection(disable_device=True) as conn:
            conn.set_user(
                uid=new_uid,
                name=name,
                privilege=zk_privilege,
                password=password,
                group_id=group_id,
                user_id=user_id,
            )

        created = self.get_user_by_user_id(user_id)

        if not created:
            raise RuntimeError(
                "El usuario se intentó crear, pero no apareció en la lectura posterior."
            )

        return created

    def delete_user_by_user_id(
        self,
        *,
        user_id: str,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """
        Borra usuario por user_id.

        Por seguridad:
        - dry_run=True por defecto.
        - Requiere ZK_ALLOW_WRITES=true si dry_run=False.
        - No borra admins.
        - No borra usuarios protegidos.
        """
        user_id = clean_text(user_id)

        if not user_id:
            raise ValueError("El user_id no puede estar vacío.")

        user = self.get_user_by_user_id(user_id)

        if not user:
            return {
                "deleted": False,
                "dry_run": dry_run,
                "reason": "Usuario no encontrado.",
                "user_id": user_id,
            }

        if user["is_admin"] or user["is_protected"]:
            raise PermissionError(
                f"No se puede borrar el usuario protegido: "
                f"uid={user['uid']} user_id={user['user_id']} name={user['name']}"
            )

        if dry_run:
            return {
                "deleted": False,
                "dry_run": True,
                "reason": "Simulación. No se borró nada.",
                "user": user,
            }

        self._assert_writes_enabled()

        uid = int(user["uid"])

        with self.connection(disable_device=True) as conn:
            result = conn.delete_user(uid=uid)

        still_exists = self.get_user_by_user_id(user_id) is not None

        return {
            "deleted": not still_exists,
            "dry_run": False,
            "result": result,
            "user": user,
        }