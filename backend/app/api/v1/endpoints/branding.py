"""
Endpoints para gestión de branding/logo institucional.

Permite subir, consultar y eliminar la imagen usada en reportes PDF.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.access_control import AccessScope
from app.core.auth_dependencies import require_module_access


router = APIRouter(
    prefix="/branding",
    tags=["Branding"],
)

# Directorio donde se almacena el logo
BRANDING_DIR = Path(__file__).resolve().parents[3] / "static" / "branding"
BRANDING_DIR.mkdir(parents=True, exist_ok=True)

# Archivos permitidos
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _get_current_logo_path() -> Path | None:
    """Busca el logo actual en el directorio de branding."""
    for ext in [".png", ".jpg", ".jpeg"]:
        path = BRANDING_DIR / f"logo{ext}"
        if path.exists():
            return path
    return None


def _delete_existing_logos():
    """Elimina todos los logos existentes."""
    for ext in [".png", ".jpg", ".jpeg"]:
        path = BRANDING_DIR / f"logo{ext}"
        if path.exists():
            path.unlink()


# ============================================================
# GET /branding/logo — Obtener logo actual
# ============================================================

@router.get("/logo")
def get_logo():
    """
    Retorna la imagen del logo institucional actual.
    Si no hay logo configurado, retorna un JSON indicándolo.
    """
    logo_path = _get_current_logo_path()

    if logo_path is None:
        return {
            "ok": True,
            "has_logo": False,
            "message": "No hay logo configurado.",
        }

    return FileResponse(
        path=str(logo_path),
        media_type=f"image/{logo_path.suffix.lstrip('.')}",
        filename=logo_path.name,
    )


# ============================================================
# GET /branding/logo/info — Información del logo sin descargar
# ============================================================

@router.get("/logo/info")
def get_logo_info():
    """Retorna metadata del logo actual sin descargar la imagen."""
    logo_path = _get_current_logo_path()

    if logo_path is None:
        return {
            "ok": True,
            "has_logo": False,
        }

    file_size = logo_path.stat().st_size

    return {
        "ok": True,
        "has_logo": True,
        "filename": logo_path.name,
        "extension": logo_path.suffix,
        "size_bytes": file_size,
        "size_kb": round(file_size / 1024, 1),
        "url": f"/api/v1/branding/logo",
    }


# ============================================================
# POST /branding/logo — Subir nuevo logo
# ============================================================

@router.post("/logo")
async def upload_logo(
    file: Annotated[UploadFile, File(description="Imagen del logo (JPG/PNG, máx 5MB)")],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("CONFIGURACION", "editar")
        ),
    ],
):
    """
    Sube una nueva imagen de logo institucional.

    Validaciones:
    - Solo JPG, JPEG, PNG.
    - Máximo 5 MB.
    - Valida MIME type.
    - Reemplaza el logo anterior si existe.
    """
    # Validar extensión
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe tener un nombre.",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión no permitida: {ext}. Solo se aceptan: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validar MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido: {file.content_type}. Solo se aceptan imágenes JPG/PNG.",
        )

    # Leer contenido y validar tamaño
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)} MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío.",
        )

    # Eliminar logos anteriores
    _delete_existing_logos()

    # Guardar nuevo logo
    logo_path = BRANDING_DIR / f"logo{ext}"
    logo_path.write_bytes(content)

    return {
        "ok": True,
        "message": "Logo actualizado correctamente.",
        "filename": logo_path.name,
        "size_bytes": len(content),
        "size_kb": round(len(content) / 1024, 1),
    }


# ============================================================
# DELETE /branding/logo — Eliminar logo
# ============================================================

@router.delete("/logo")
def delete_logo(
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("CONFIGURACION", "editar")
        ),
    ],
):
    """Elimina el logo institucional actual."""
    logo_path = _get_current_logo_path()

    if logo_path is None:
        return {
            "ok": True,
            "message": "No había logo configurado.",
        }

    _delete_existing_logos()

    return {
        "ok": True,
        "message": "Logo eliminado correctamente.",
    }
