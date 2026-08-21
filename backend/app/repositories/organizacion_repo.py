"""
Utilidades SQL compartidas de jerarquía organizacional.

Cualquier consulta que agrupe/etiquete resultados "por departamento"
(reportes, dashboard) debe usar DEPARTAMENTO_RESUELTO_CTE en vez de
reimplementar la resolución: evita que dos módulos diverjan sobre qué
significa "el departamento" de un empleado o registro.
"""

from __future__ import annotations

# Resuelve, para cada unidad organizacional, el DEPARTAMENTO
# ancestro-o-sí-misma más cercano (organizacion.tipos_unidad.codigo =
# 'DEPARTAMENTO'). Evita mezclar Dirección/División/Comité/
# Encargaduría con Departamento: una unidad cuya cadena de ancestros
# nunca llega a un Departamento (p. ej. asignada directamente a una
# Dirección o División) resuelve a NULL y debe reportarse aparte,
# nunca bajo el nombre de esa Dirección/División.
DEPARTAMENTO_RESUELTO_CTE = """
    WITH RECURSIVE cadena_unidad AS (
        SELECT
            uo.id AS unidad_origen_id,
            uo.id AS unidad_actual_id,
            uo.nombre AS unidad_actual_nombre,
            uo.unidad_padre_id AS unidad_actual_padre_id,
            tu.codigo AS unidad_actual_tipo
        FROM organizacion.unidades_organizacionales uo
        INNER JOIN organizacion.tipos_unidad tu
            ON tu.id = uo.tipo_unidad_id

        UNION ALL

        SELECT
            cu.unidad_origen_id,
            padre.id,
            padre.nombre,
            padre.unidad_padre_id,
            tu.codigo
        FROM cadena_unidad cu
        INNER JOIN organizacion.unidades_organizacionales padre
            ON padre.id = cu.unidad_actual_padre_id
        INNER JOIN organizacion.tipos_unidad tu
            ON tu.id = padre.tipo_unidad_id
        WHERE cu.unidad_actual_tipo <> 'DEPARTAMENTO'
    ),
    departamento_resuelto AS (
        SELECT DISTINCT ON (unidad_origen_id)
            unidad_origen_id,
            unidad_actual_id AS departamento_id,
            unidad_actual_nombre AS departamento_nombre
        FROM cadena_unidad
        WHERE unidad_actual_tipo = 'DEPARTAMENTO'
        ORDER BY unidad_origen_id, unidad_actual_id
    )
"""
