BEGIN;

UPDATE organizacion.tipos_unidad
SET
    nombre = U&'Direcci\00F3n',
    descripcion = U&'Unidad directiva principal.'
WHERE codigo = 'DIRECCION';

UPDATE organizacion.tipos_unidad
SET
    nombre = U&'Divisi\00F3n',
    descripcion = U&'Unidad organizacional de nivel divisi\00F3n.'
WHERE codigo = 'DIVISION';

UPDATE organizacion.tipos_unidad
SET
    nombre = U&'Departamento',
    descripcion = U&'Unidad organizacional de nivel departamento.'
WHERE codigo = 'DEPARTAMENTO';

UPDATE organizacion.tipos_unidad
SET
    nombre = U&'Comit\00E9',
    descripcion = U&'\00D3rgano colegiado o comit\00E9 interno.'
WHERE codigo = 'COMITE';

UPDATE organizacion.tipos_unidad
SET
    nombre = U&'Encargadur\00EDa',
    descripcion = U&'Unidad o funci\00F3n operativa bajo encargadur\00EDa.'
WHERE codigo = 'ENCARGADURIA';

COMMIT;