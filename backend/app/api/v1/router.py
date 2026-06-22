from fastapi import APIRouter

from app.api.v1.endpoints import asistencia, catalogos, empleados, empleados_config, health, marcaciones

router = APIRouter()

router.include_router(health.router)
router.include_router(empleados.router)
router.include_router(empleados_config.router)
router.include_router(asistencia.router)
router.include_router(marcaciones.router)
router.include_router(catalogos.router)