---
description: Registrar nueva categoría
---

# HU-001: Registrar nueva categoría

## Historia de Usuario

Como administrador del sistema
Quiero crear una categoría con su nombre y descripción
Para clasificar los artículos de la tienda de forma organizada.

---

## Reglas de Negocio
- El `nombre` es obligatorio, único (case-insensitive) y con longitud máxima de 100 caracteres.
- La `descripción` es opcional, con un máximo de 500 caracteres.
- El sistema debe generar automáticamente un `slug` único y amigable para URL a partir del nombre (ej. "Cafés Especiales" -> "cafes-especiales").
- El estado por defecto al crear es `activo` (booleano o enum según el modelo).
- **Seguridad y Permisos (RBAC):** Solo usuarios autenticados con el rol `administrador` o con el permiso explícito `categories.create` pueden acceder a la ruta y ejecutar la creación de categorías. Usuarios con rol `usuario` o `vendedor` (sin dicho permiso) reciben `403 Forbidden`.


---

## Criterios de Aceptación

### Escenario 1: Creación exitosa

Dado que el usuario administrador accede al formulario de creación de categorías por medio del menú en el sidebar,
Cuando ingresa un nombre válido y no registrado previamente (ej. "Bebidas") y confirma el guardado,
Entonces el sistema persiste la categoría con estado "Activo" y retorna un mensaje de confirmación.

### Escenario 2: Nombre duplicado

Dado que ya existe una categoría llamada "Abarrotes",
Cuando el usuario intenta registrar otra categoría con el nombre "Abarrotes" (sin distinguir mayúsculas/minúsculas),
Entonces el sistema cancela la operación y muestra el error "La categoría ya se encuentra registrada".

### Scenario 3: Bloqueo de creación de categoría para rol "usuario" o "vendedor" sin permiso

Dado que un usuario autenticado con el rol "usuario" (sin permiso `categories.create`)
Cuando intenta acceder a la vista o ejecutar la acción de crear categoría
Entonces recibe una respuesta 403 Forbidden y no se persiste ningún registro.