from __future__ import annotations

import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from zk import ZK


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BACKEND_DIR / ".env"

RUNTIME_DIR = BACKEND_DIR / "runtime"
STATE_PATH = RUNTIME_DIR / "zk_time_sync_state.json"

load_dotenv(ENV_PATH)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "si", "sí"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


def today_key() -> str:
    return date.today().isoformat()


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {
            "date": today_key(),
            "check_count": 0,
            "last_checked_at": None,
            "last_status": "NO_CHECKS_YET",
            "last_error": None,
        }

    try:
        with STATE_PATH.open("r", encoding="utf-8") as file:
            state = json.load(file)
    except Exception:
        state = {}

    if state.get("date") != today_key():
        return {
            "date": today_key(),
            "check_count": 0,
            "last_checked_at": None,
            "last_status": "RESET_NEW_DAY",
            "last_error": None,
        }

    return {
        "date": state.get("date", today_key()),
        "check_count": int(state.get("check_count", 0)),
        "last_checked_at": state.get("last_checked_at"),
        "last_status": state.get("last_status", "UNKNOWN"),
        "last_error": state.get("last_error"),
    }


def save_state(state: dict[str, Any]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    with STATE_PATH.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2, ensure_ascii=False)


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def should_check_time(
    *,
    state: dict[str, Any],
    force: bool,
    max_checks_per_day: int,
    min_interval_hours: int,
) -> tuple[bool, str]:
    if force:
        return True, "FORCED_CHECK"

    if state["check_count"] >= max_checks_per_day:
        return False, "MAX_DAILY_CHECKS_REACHED"

    last_checked_at = parse_iso_datetime(state.get("last_checked_at"))

    if last_checked_at:
        next_allowed_at = last_checked_at + timedelta(hours=min_interval_hours)

        if datetime.utcnow() < next_allowed_at:
            return False, "MIN_INTERVAL_NOT_REACHED"

    return True, "CHECK_ALLOWED"


def build_skipped_response(state: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "ok": True,
        "checked": False,
        "corrected": False,
        "status": reason,
        "date": state["date"],
        "check_count": state["check_count"],
        "max_checks_per_day": env_int("ZK_TIME_SYNC_MAX_CHECKS_PER_DAY", 5),
        "last_checked_at": state.get("last_checked_at"),
        "last_status": state.get("last_status"),
        "last_error": state.get("last_error"),
    }


def sync_zk_time_if_allowed(force: bool = False) -> dict[str, Any]:
    auto_sync_enabled = env_bool("ZK_AUTO_SYNC_TIME", True)
    allow_time_sync = env_bool("ZK_ALLOW_TIME_SYNC", False)

    max_checks_per_day = env_int("ZK_TIME_SYNC_MAX_CHECKS_PER_DAY", 5)
    min_interval_hours = env_int("ZK_TIME_SYNC_MIN_INTERVAL_HOURS", 4)
    max_drift_seconds = env_int("ZK_MAX_TIME_DRIFT_SECONDS", 120)

    state = load_state()

    if not auto_sync_enabled and not force:
        return build_skipped_response(
            state=state,
            reason="AUTO_SYNC_DISABLED",
        )

    allowed, reason = should_check_time(
        state=state,
        force=force,
        max_checks_per_day=max_checks_per_day,
        min_interval_hours=min_interval_hours,
    )

    if not allowed:
        return build_skipped_response(
            state=state,
            reason=reason,
        )

    # Se incrementa antes de conectar para evitar que un fallo cause spam de intentos.
    state["check_count"] = int(state.get("check_count", 0)) + 1
    state["last_checked_at"] = utc_now_iso()
    state["last_status"] = "CHECK_STARTED"
    state["last_error"] = None
    save_state(state)

    zk_ip = os.getenv("ZK_IP", "192.168.137.218")
    zk_port = env_int("ZK_PORT", 4370)
    zk_password = env_int("ZK_PASSWORD", 0)
    zk_timeout = env_int("ZK_TIMEOUT", 10)
    zk_force_udp = env_bool("ZK_FORCE_UDP", False)
    zk_ommit_ping = env_bool("ZK_OMMIT_PING", True)

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

        device_time = conn.get_time().replace(microsecond=0)
        server_time = datetime.now().replace(microsecond=0)

        drift_seconds = int(abs((server_time - device_time).total_seconds()))

        corrected = False
        status = "TIME_OK"

        if drift_seconds > max_drift_seconds:
            if allow_time_sync:
                conn.set_time(server_time)
                corrected = True
                status = "TIME_CORRECTED"
            else:
                status = "DRIFT_DETECTED_WRITE_DISABLED"

        after_time = conn.get_time().replace(microsecond=0)

        state["last_status"] = status
        state["last_error"] = None
        save_state(state)

        return {
            "ok": True,
            "checked": True,
            "corrected": corrected,
            "status": status,
            "date": state["date"],
            "check_count": state["check_count"],
            "max_checks_per_day": max_checks_per_day,
            "device_time_before": str(device_time),
            "server_time": str(server_time),
            "device_time_after": str(after_time),
            "drift_seconds": drift_seconds,
            "max_drift_seconds": max_drift_seconds,
            "allow_time_sync": allow_time_sync,
        }

    except Exception as exc:
        state["last_status"] = "ERROR"
        state["last_error"] = str(exc)
        save_state(state)

        return {
            "ok": False,
            "checked": True,
            "corrected": False,
            "status": "ERROR",
            "error": str(exc),
            "date": state["date"],
            "check_count": state["check_count"],
            "max_checks_per_day": max_checks_per_day,
        }

    finally:
        if conn:
            try:
                conn.enable_device()
            except Exception:
                pass

            conn.disconnect()