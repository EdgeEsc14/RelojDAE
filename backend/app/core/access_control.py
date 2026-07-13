from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


DataScope = Literal[
    "TOTAL",
    "AREA",
    "PROPIO",
    "NINGUNO",
]

PermissionAction = Literal[
    "consultar",
    "crear",
    "editar",
    "eliminar",
    "aprobar",
    "exportar",
]


_ACTION_ATTRIBUTE: dict[PermissionAction, str] = {
    "consultar": "can_read",
    "crear": "can_create",
    "editar": "can_edit",
    "eliminar": "can_delete",
    "aprobar": "can_approve",
    "exportar": "can_export",
}


@dataclass(frozen=True, slots=True)
class AccessScope:
    """
    Representa los permisos efectivos de un usuario para un módulo.

    El objeto combina:

    - Identidad del usuario.
    - Rol.
    - Módulo solicitado.
    - Alcance de los datos.
    - Acciones permitidas.
    - Unidades organizacionales autorizadas.

    Este objeto debe construirse en el backend a partir de PostgreSQL.
    El frontend nunca debe decidir el alcance efectivo de seguridad.
    """

    user_id: int
    employee_id: int | None
    role_id: int | None
    role_code: str

    module_code: str
    data_scope: DataScope

    can_read: bool
    can_create: bool
    can_edit: bool
    can_delete: bool
    can_approve: bool
    can_export: bool

    allowed_unit_ids: tuple[int, ...] = ()

    def allows(self, action: PermissionAction) -> bool:
        """
        Indica si el usuario tiene permitida una acción concreta.
        """
        attribute = _ACTION_ATTRIBUTE[action]
        return bool(getattr(self, attribute))

    @property
    def has_data_access(self) -> bool:
        """
        Indica si existe algún alcance de datos utilizable.
        """
        return self.data_scope != "NINGUNO"

    @property
    def has_complete_access(self) -> bool:
        return self.data_scope == "TOTAL"

    @property
    def has_area_access(self) -> bool:
        return self.data_scope == "AREA"

    @property
    def has_own_access(self) -> bool:
        return self.data_scope == "PROPIO"