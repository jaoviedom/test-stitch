---
description: Gestión de múltiples roles y permisos por el Administrador
---

# HU-002: Gestión de múltiples roles y permisos por el Administrador

## Historia de Usuario
**Como** usuario con rol `administrador`
**Quiero** asignar o revocar múltiples roles (`usuario`, `vendedor`, `administrador`) y permisos granulares a cualquier usuario
**Para** controlar de forma segura quién puede ver, crear o editar recursos en la tienda.

## Criterios de Aceptación (Gherkin)

Scenario: Asignación de múltiples roles a un usuario
  Given que estoy autenticado como "administrador" en "/admin/users"
  And existe un usuario "María" que solo tiene el rol "usuario"
  When abro el modal de accesos de "María" y selecciono los roles "usuario" y "vendedor"
  Then "María" conserva ambos roles asignados
  And ahora puede acceder a consultar categorías (`categories.view`) pero no a editarlas (`categories.edit`).

Scenario: Otorgar un permiso específico de categoría a un vendedor
  Given que "María" tiene el rol "vendedor"
  When el "administrador" le activa el permiso directo `categories.create`
  Then "María" puede ejecutar la acción de registrar una nueva categoría (HU-001 de catalog).

Scenario: Protección contra escalación de privilegios en Livewire
  Given un usuario sin el permiso `users.manage-access`
  When intenta invocar el método de actualización de roles en el componente Livewire
  Then la petición es rechazada con estado 403 Forbidden.
