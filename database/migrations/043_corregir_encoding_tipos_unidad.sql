BEGIN;

UPDATE organizacion.tipos_unidad
SET
    nombre = 'Dirección',
    descripcion = 'Unidad directiva principal.'
WHERE codigo = 'DIRECCION';

UPDATE organizacion.tipos_unidad
SET
    nombre = 'División',
    descripcion = 'Unidad organizacional de nivel división.'
WHERE codigo = 'DIVISION';

UPDATE organizacion.tipos_unidad
SET
    nombre = 'Departamento',
    descripcion = 'Unidad organizacional de nivel departamento.'
WHERE codigo = 'DEPARTAMENTO';

UPDATE organizacion.tipos_unidad
SET
    nombre = 'Comité',
    descripcion = 'Órgano colegiado o comité interno.'
WHERE codigo = 'COMITE';

UPDATE organizacion.tipos_unidad
SET
    nombre = 'Encargaduría',
    descripcion = 'Unidad o función operativa bajo encargaduría.'
WHERE codigo = 'ENCARGADURIA';

COMMIT;