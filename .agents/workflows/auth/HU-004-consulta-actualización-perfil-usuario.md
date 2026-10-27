---
description: Consulta y Actualización de Perfil de Usuario
---

# HU-004: Consulta y Actualización de Perfil de Usuario

## Historia de Usuario
**Como** usuario autenticado (`usuario`, `vendedor` o `administrador`)
**Quiero** acceder a la sección "Mi Perfil" desde el menú del sidebar para ver mis roles asignados y actualizar mi nombre, correo electrónico o contraseña
**Para** mantener mi información personal al día y conocer qué nivel de acceso tengo en Tienda Fresca.

---

## Criterios de Aceptación (Gherkin)

Scenario: Acceso permitido para cualquier rol autenticado y visualización de roles
  Given un usuario autenticado con los roles "usuario" y "vendedor"
  When accede a la ruta `/profile` desde el menú de su nombre en el sidebar
  Then recibe respuesta HTTP 200 OK
  And visualiza sus datos actuales ("Nombre", "Email") y los badges de sus roles asignados ("usuario", "vendedor") en modo solo lectura.

Scenario: Actualización exitosa de datos personales (Nombre y Email)
  Given que estoy autenticado en `/profile`
  When cambio mi nombre a "Jose Alonso Oviedo" y guardo el formulario de información de perfil
  Then los cambios se persisten en la base de datos dentro de `DB::transaction`
  And el nombre mostrado en el pie del sidebar se actualiza a "Jose Alonso Oviedo"
  And se muestra una notificación de éxito.

Scenario: Cambio de contraseña validando contraseña actual
  Given que estoy autenticado en `/profile`
  When ingreso una "contraseña actual" incorrecta e intento definir una nueva contraseña
  Then el sistema rechaza el cambio mostrando un mensaje de error accesible con `role="alert"` y `text-rose-600`
  And cuando ingreso mi "contraseña actual" correcta y una nueva contraseña válida con confirmación
  Then mi contraseña se actualiza con hash seguro.

Scenario: Inmutabilidad de roles desde el propio perfil (Seguridad RBAC)
  Given un usuario con rol "usuario" en la vista `/profile`
  When envía una petición intentando modificar sus propios roles o permisos desde el componente de perfil
  Then sus roles en la base de datos permanecen intactos sin cambios.

---

## Directrices Técnicas y Restricciones NFR (Para Compuerta 1)

1. **Ruta y Seguridad (`routes/web.php`):**
   - `GET /profile` -> Nombre de ruta: `profile` -> Middleware: `['auth']` (accesible para todos los roles autenticados).
2. **Arquitectura Backend (`Actions`):**
   - `App\Actions\Auth\UpdateUserProfileAction` (`execute(User $user, array $data): User`).
   - `App\Actions\Auth\UpdateUserPasswordAction` (`execute(User $user, string $newPassword): void`).
3. **Cumplimiento UI/UX (`01-ui-ux-system.md` - Paleta Mercado Fresco POS):**
   - Componente Livewire SFC en `resources/views/livewire/auth/profile.blade.php` heredando de `components.layouts.app`.
   - Dos tarjetas separadas (`bg-white rounded-xl border border-slate-200 shadow-sm p-6`):
     1. **Información Personal y Roles Actuales:** Muestra badges semánticos de los roles que posee el usuario (solo lectura) e inputs para `name` y `email` validando unicidad (`Rule::unique('users')->ignore($user->id)`).
     2. **Seguridad y Contraseña:** Inputs para `current_password` (regla `current_password`), `password` y `password_confirmation`.
   - Botones de guardado con color primario `bg-emerald-600 hover:bg-emerald-700` y directiva `wire:loading.attr="disabled"`.
