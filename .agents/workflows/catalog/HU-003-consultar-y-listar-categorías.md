---
description: Consultar y listar categorías
---

# HU-002: Consultar y listar categorías

## Historia de Usuario
Como administrador o encargado de inventario
Quiero ver la lista de categorías existentes y buscar por nombre
Para verificar la parametrización del catálogo y el total de productos asociados.

## Criterios de Aceptación (Gherkin):

### Escenario 1: Visualización paginada
Dado que existen categorías registradas en el sistema,
Cuando el usuario entra a la vista de categorías,
Entonces el sistema muestra una tabla paginada con: Nombre, Descripción, Conteo de productos asociados, Estado y botones con íconos para ver el detalle, editar y eliminar.

### Escenario 2: Búsqueda por texto
Dado un listado amplio de categorías,
Cuando el usuario escribe una palabra clave en el buscador,
Entonces la tabla filtra en tiempo real mostrando únicamente los registros cuyo nombre coincida con el término ingresado.

### Scenario 3: Bloqueo de creación de categoría para rol "usuario" o "vendedor" sin permiso

Dado que un usuario autenticado con el rol "usuario" (sin permiso `categories.create`)
Cuando intenta acceder a la vista o ejecutar la acción de crear categoría
Entonces recibe una respuesta 403 Forbidden y no se persiste ningún registro.