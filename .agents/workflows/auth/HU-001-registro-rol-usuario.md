---
description: Registro de usuario con rol base por defecto
---

# HU-001: Registro de usuario con rol base por defecto

## Historia de Usuario
**Como** visitante de la aplicación
**Quiero** registrarme con mi nombre, correo y contraseña
**Para** obtener una cuenta activa con el rol inicial de `usuario` hasta que un administrador me asigne permisos adicionales.

## Criterios de Aceptación (Gherkin)

Scenario: Registro exitoso asigna únicamente el rol "usuario"
  Given que soy un visitante no autenticado en "/register"
  When completo el registro con nombre "Juan Pérez", email "juan@tienda.co" y contraseña válida
  Then mi cuenta se crea en la base de datos dentro de una transacción
  And se me asigna exclusivamente el rol "usuario"
  And soy redirigido a "/dashboard".

Scenario: Usuario recién registrado tiene restringido el módulo de Categorías
  Given que acabo de registrarme con el rol "usuario"
  When intento acceder a la ruta de listar o crear categorías ("/catalog/categories")
  Then el sistema responde con estado HTTP 403 Forbidden.
