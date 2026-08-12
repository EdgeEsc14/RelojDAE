from fastapi import APIRouter

from app.api.v1.endpoints import (
    asistencia,
    calendario,
    catalogos,
    dashboard,
    dispositivos,
    empleados,
    empleados_config,
    health,
    horarios,
    incidencias,
    marcaciones,
    reportes,
    usuarios,
)

router = APIRouter()

router.include_router(health.router)
router.include_router(dashboard.router)
router.include_router(empleados.router)
router.include_router(empleados_config.router)
router.include_router(asistencia.router)
router.include_router(marcaciones.router)
router.include_router(catalogos.router)
router.include_router(horarios.router)
router.include_router(usuarios.router)
router.include_router(reportes.router)
router.include_router(incidencias.router)
router.include_router(calendario.router)
router.include_router(dispositivos.router)