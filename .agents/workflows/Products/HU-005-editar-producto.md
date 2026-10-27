---
description: Editar categoría
---

# HU-002: Editar categoría

## Historia de Usuario

Como administrador del sistema
Quiero actualizar el nombre o descripción de una categoría
Para corregir errores tipográficos o reclasificar grupos de productos.

---

## Reglas de Negocio
- El `nombre` es obligatorio, único (case-insensitive) y con longitud máxima de 100 caracteres.
- La `descripción` es opcional, con un máximo de 500 caracteres.
- El sistema debe generar automáticamente un `slug` único y amigable para URL a partir del nombre (ej. "Cafés Especiales" -> "cafes-especiales").
- El estado por defecto al crear es `activo` (booleano o enum según el modelo).

---

## Criterios de Aceptación

### Escenario 1: Edición exitosa de datos

Dado una categoría existente llamada "Lácteos",
Cuando el usuario edita el nombre a "Lácteos y Quesos" y guarda los cambios,
Entonces el sistema actualiza el registro y propaga el cambio visual a todos los productos asociados sin modificar sus históricos de venta.

### Escenario 2: Intentar renombrar a un nombre ya existente

Dado que existen las categorías "Bebidas" y "Snacks",
Cuando el usuario edita "Snacks" y le asigna el nombre "Bebidas",
Entonces el sistema rechaza la actualización e indica que el nombre ya está en uso.

### Scenario 3: Bloqueo de creación de categoría para rol "usuario" o "vendedor" sin permiso

Dado que un usuario autenticado con el rol "usuario" (sin permiso `categories.create`)
Cuando intenta acceder a la vista o ejecutar la acción de crear categoría
Entonces recibe una respuesta 403 Forbidden y no se persiste ningún registro.