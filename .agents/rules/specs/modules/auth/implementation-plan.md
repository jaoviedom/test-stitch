# Plan de Implementación: Módulo Auth & RBAC (TeckStore Admin)

Este plan desglosa secuencialmente las tareas requeridas para implementar las historias de usuario de autenticación bajo TDD estricto en el stack **Django 6 + Python 3.12+ + Tailwind CSS v4**.

---

## HU-001: Registro de usuario con rol base por defecto (COMPLETADA ✅)
- [x] Tarea 1.1: Pruebas automatizadas de registro y RBAC inicial en `tests/auth/test_registration.py`.
- [x] Tarea 2.1: App `authentication`, servicio `RegisterUserService` con transacción atómica.
- [x] Tarea 3.1: Formulario `UserRegistrationForm` con validaciones limpias.
- [x] Tarea 4.1: Vista `register_view` y rutas `/auth/register/`.
- [x] Tarea 5.1: Plantilla `authentication/register.html` con sistema de diseño Stitch TeckStore y Tailwind 4.
- [x] Tarea 6.1: Validación de calidad en verde (8 tests pasados).

---

## HU-002: Gestión de múltiples roles y permisos por el Administrador (COMPLETADA ✅)

### Fase 1: Suite de Pruebas Automatizadas para HU-002 (Fase Red)
- [x] **Tarea 1.1:** Crear suite de pruebas de gestión de roles y control de accesos en `tests/auth/test_role_management.py`:
  - Pruebas unitarias de `UpdateUserAccessService`:
    - Asignar múltiples roles simultáneos (`usuario` y `vendedor`) a un usuario existente.
    - Otorgar permisos directos (`inventario.add_categoria`) a un vendedor.
    - Revocar un rol previamente asignado (quitar `vendedor` y dejar `usuario`).
    - Rechazo de ejecución si el usuario solicitante carece del permiso `authentication.manage_access` (PermissionDenied).
    - Atomicidad y rollback de la base de datos ante errores imprevistos.
  - Pruebas de integración HTTP y vistas:
    - Administrador autorizado accede a `/auth/usuarios/` (HTTP 200 OK) y visualiza tabla con badges de roles.
    - Administrador actualiza roles de un usuario mediante POST a `/auth/usuarios/<id>/accesos/` (302 y persistencia en BD).
    - Protección de seguridad RBAC: Usuario con rol `vendedor` o `usuario` recibe HTTP 403 Forbidden al intentar acceder o actualizar roles.
    - Protección de seguridad para anónimos: Visitante no autenticado es redirigido a login (código 302).
- [x] **Tarea 1.2:** Ejecutar la suite de pruebas en la terminal (`python manage.py test tests.auth`) y confirmar el fallo esperado por ausencia de código (Fase Red verificada).

---

### Fase 2: Modelos, Permisos y Grupos Oficiales
- [x] **Tarea 2.1:** Registrar el permiso oficial `manage_access` en `authentication/models.py`.
- [x] **Tarea 2.2:** Generar y aplicar migraciones (`python manage.py makemigrations authentication`, `python manage.py migrate`).
- [x] **Tarea 2.3:** Crear función auxiliar para inicializar grupos y permisos oficiales (`usuario`, `vendedor`, `administrador`).

---

### Fase 3: Capa de Dominio y Servicios (Backend HU-002)
- [x] **Tarea 3.1:** Implementar `UpdateUserAccessService` en `authentication/services.py` protegido con `@transaction.atomic` y verificación de `manage_access`.

---

### Fase 4: Capa de Validación y Formularios (HU-002)
- [x] **Tarea 4.1:** Implementar `UpdateUserAccessForm` en `authentication/forms.py` con selección múltiple accesible de roles y permisos directos.

---

### Fase 5: Enrutamiento, Vistas y Autorización (HU-002)
- [x] **Tarea 5.1:** Implementar `user_list_view` y `user_manage_access_view` en `authentication/views.py` protegidas con `@login_required` y `@permission_required('authentication.manage_access', raise_exception=True)`.
- [x] **Tarea 5.2:** Registrar las rutas en `authentication/urls.py` (`/auth/usuarios/` y `/auth/usuarios/<int:user_id>/accesos/`).

---

### Fase 6: Plantillas Django y Cumplimiento de UI/UX (Tailwind 4)
- [x] **Tarea 6.1:** Crear `authentication/templates/authentication/user_list.html` heredando de `base.html` con tabla de usuarios, badges dinámicos de rol y botones de gestión.
- [x] **Tarea 6.2:** Crear `authentication/templates/authentication/user_manage_access.html` con fieldsets accesibles, checkboxes para múltiples roles y permisos directos.

---

### Fase 7: Bucle TDD, Control de Calidad y Cierre (Fase Green)
- [x] **Tarea 7.1:** Ejecutar la suite de pruebas completa y verificar 100% de tests en verde (HU-001 + HU-002).
- [x] **Tarea 7.2:** Ejecutar `python manage.py check` y `python manage.py makemigrations --check --dry-run`.
- [x] **Tarea 7.3:** Validar la interfaz en vivo en el navegador (`http://127.0.0.1:8000/auth/usuarios/`).

---

## HU-003: Inicio de Sesión Seguro (Login) (COMPLETADA ✅)

### Fase 1: Suite de Pruebas Automatizadas para HU-003 (Fase Red)
- [x] **Tarea 1.1:** Crear suite de pruebas de autenticación y login en `tests/auth/test_login.py`:
  - Pruebas unitarias de `AuthenticateUserService`:
    - Autenticación exitosa por `username` exacto y en mayúsculas/minúsculas.
    - Autenticación exitosa por `email` exacto y en mayúsculas/minúsculas.
    - Retorno de `None` si la contraseña es incorrecta o el usuario no existe.
  - Pruebas de integración HTTP y vistas:
    - Login exitoso por nombre de usuario redirige a `/inventario/` (302) y crea sesión activa.
    - Login exitoso por correo electrónico redirige a `/inventario/` (302) y crea sesión activa.
    - Redirección con parámetro `next`: al iniciar sesión se redirige a la URL interna solicitada (`/inventario/productos/`).
    - Protección contra Open Redirect: parámetro `next=https://sitio-malicioso.com` es sanitizado y redirige a `/inventario/`.
    - Rechazo de credenciales incorrectas: responde con HTTP 200, no crea sesión, muestra alerta accesible con `role="alert"` y texto genérico de error ("Nombre de usuario, correo o contraseña incorrectos.").
    - Redirección preventiva: usuario ya autenticado que visita `/auth/login/` es redirigido a `/inventario/` (302) sin mostrar formulario.
    - Persistencia de sesión: con `remember_me=True` la sesión persiste; sin marcar, la sesión expira al cerrar navegador (`session.get_expiry_age() == 0` o expiración de navegador).
- [x] **Tarea 1.2:** Ejecutar la suite en la terminal (`python manage.py test tests.auth.test_login`) y verificar que falle controladamente por ausencia de código (Fase Red confirmada).

---

### Fase 2: Capa de Dominio y Servicios (Backend HU-003)
- [x] **Tarea 2.1:** Implementar `AuthenticateUserService` en `authentication/services.py` con resolución insensible de `username` o `email` y llamada a `authenticate()`.

---

### Fase 3: Capa de Validación y Formularios (HU-003)
- [x] **Tarea 3.1:** Implementar `LoginForm` en `authentication/forms.py` con campos `username`, `password`, `remember_me` y atributos de accesibilidad WCAG 2.1 AA (`aria-invalid`, `id_username`, `id_password`).

---

### Fase 4: Enrutamiento y Controlador de Vista (HU-003)
- [x] **Tarea 4.1:** Implementar `login_view` en `authentication/views.py` gestionando:
  - Redirección preventiva si `request.user.is_authenticated`.
  - Validación de credenciales mediante `AuthenticateUserService`.
  - Manejo de persistencia de sesión con `request.session.set_expiry`.
  - Validación segura de `next` con `url_has_allowed_host_and_scheme`.
  - Mensaje flash de bienvenida.
- [x] **Tarea 4.2:** Registrar ruta `path('login/', views.login_view, name='login')` en `authentication/urls.py`.

---

### Fase 5: Plantilla Django y UI/UX (Tailwind 4 + Stitch)
- [x] **Tarea 5.1:** Crear plantilla `authentication/templates/authentication/login.html` basada en el diseño de Stitch TeckStore (`screens/7ca704d41cf9433db46e5a6191773d5f`) utilizando tokens puros de Tailwind 4 (`@theme`), labels vinculados (`for`), `role="alert"` para mensajes de error y toggle visual de contraseña.

---

### Fase 6: Bucle TDD, Control de Calidad y Cierre (Fase Green)
- [x] **Tarea 6.1:** Ejecutar suite completa de tests de autenticación (`tests/auth/`) hasta alcanzar 100% de tests en verde (32 tests aprobados en total).
- [x] **Tarea 6.2:** Ejecutar verificaciones de calidad de Django (`python manage.py check`, `python manage.py makemigrations --check --dry-run`).
- [x] **Tarea 6.3:** Validar flujo interactivo en el navegador con `browser_subagent` (login con username, con email, error de contraseña, switch de tema).

---

## HU-004: Consulta y Actualización de Perfil de Usuario (COMPLETADA ✅)

### Fase 1: Suite de Pruebas Automatizadas para HU-004 (Fase Red)
- [x] **Tarea 1.1:** Crear suite de pruebas de consulta y actualización de perfil en `tests/auth/test_profile.py`:
  - Pruebas unitarias de servicios de dominio:
    - `UpdateUserProfileService`: Actualización atómica exitosa de `first_name` y `email`.
    - `UpdateUserProfileService`: Inmutabilidad de roles (intento de pasar `roles` o permisos es ignorado y no muta `user.groups`).
    - `UpdateUserProfileService`: Rollback atómico ante excepciones imprevistas de BD.
    - `UpdateUserPasswordService`: Actualización exitosa con hash criptográfico seguro al validar contraseña actual.
    - `UpdateUserPasswordService`: Rechazo controlado y lanzamiento de `ValidationError` si la contraseña actual no coincide.
  - Pruebas de integración HTTP y controladores de vista:
    - Acceso permitido para cualquier rol autenticado (`usuario`, `vendedor`, `administrador`) retornando HTTP 200 OK y visualizando badges de roles en modo solo lectura.
    - Redirección preventiva de visitantes anónimos a `/auth/login/?next=/auth/perfil/` con código HTTP 302.
    - Actualización exitosa de nombre y email mediante POST (`action='update_profile'`) persistiendo en base de datos y emitiendo mensaje flash.
    - Rechazo de actualización de perfil cuando los campos obligatorios están vacíos (`role="alert"` y `aria-invalid="true"`).
    - Rechazo de actualización de perfil si el email ya pertenece a otro usuario registrado.
    - Cambio de contraseña exitoso mediante POST (`action='change_password'`) actualizando el hash y conservando la sesión activa (`update_session_auth_hash`).
    - Rechazo de cambio de contraseña cuando la contraseña actual es errónea.
    - Rechazo de cambio de contraseña cuando la confirmación no coincide con la nueva contraseña.
    - Seguridad RBAC: Parámetros maliciosos inyectados en POST para escalar privilegios (`groups`, `is_staff`, `is_superuser`) no alteran los grupos en la base de datos.
- [x] **Tarea 1.2:** Ejecutar la suite en la terminal (`python manage.py test tests.auth.test_profile`) y verificar que falle controladamente por ausencia de código (Fase Red confirmada con 14 fallos esperados).

---

### Fase 2: Capa de Dominio y Servicios (Backend HU-004)
- [x] **Tarea 2.1:** Implementar `UpdateUserProfileService` en `authentication/services.py` con decorador `@transaction.atomic`, sanitización de datos y guardado estricto con `update_fields=['first_name', 'last_name', 'email']`.
- [x] **Tarea 2.2:** Implementar `UpdateUserPasswordService` en `authentication/services.py` con `@transaction.atomic`, verificación con `user.check_password`, validación con `password_validation.validate_password` y aplicación de hash seguro con `user.set_password`.

---

### Fase 3: Capa de Validación y Formularios (HU-004)
- [x] **Tarea 3.1:** Implementar `UserProfileForm` en `authentication/forms.py` con campos `first_name` y `email`, validación limpia `clean_email()` excluyendo al usuario actual (`exclude(pk=self.user.pk)`).
- [x] **Tarea 3.2:** Implementar `UserPasswordChangeForm` en `authentication/forms.py` con campos `current_password`, `new_password1`, `new_password2`, validando contraseña actual y coincidencia entre claves nuevas con mensajes de error accesibles.

---

### Fase 4: Enrutamiento y Controlador de Vista (HU-004)
- [x] **Tarea 4.1:** Implementar `profile_view` en `authentication/views.py` decorada con `@login_required`:
  - Manejo de GET: Renderizado de datos del usuario, badges de rol en solo lectura (`user.groups.all()`) y ambos formularios.
  - Manejo de POST: Despacho condicional por `action` ('update_profile' o 'change_password').
  - Preservación de sesión tras cambio de clave mediante `update_session_auth_hash`.
  - Notificaciones flash contextuales con `messages.success`.
- [x] **Tarea 4.2:** Registrar ruta `path('perfil/', views.profile_view, name='profile')` en `authentication/urls.py` y alias `path('profile/', views.profile_view, name='profile_alias')`.

---

### Fase 5: Plantillas Django y Cumplimiento de UI/UX (Tailwind 4)
- [x] **Tarea 5.1:** Crear plantilla `authentication/templates/authentication/profile.html` extendiendo de `base.html` con sistema de diseño Stitch TeckStore:
  - Header de perfil con avatar dinámico e insignias de roles en solo lectura.
  - Tarjeta 1: Información personal y formulario de actualización.
  - Tarjeta 2: Seguridad y formulario de cambio de contraseña.
  - Etiquetas accesibles (`<label for="...">`), mensajes de error con `role="alert"` y estilos semánticos (`text-error`, `border-outline-variant`).
- [x] **Tarea 5.2:** Actualizar enlaces en `templates/components/header.html` (menú de usuario "Ver perfil") para que apunten a `{% url 'authentication:profile' %}`.

---

### Fase 6: Bucle TDD, Control de Calidad y Cierre (Fase Green)
- [x] **Tarea 6.1:** Ejecutar suite completa de tests de autenticación (`tests/auth/`) alcanzando 100% de tests en verde (46 tests aprobados / 0 fallos).
- [x] **Tarea 6.2:** Ejecutar verificaciones de Django (`python manage.py check`, `python manage.py makemigrations --check --dry-run`).
- [x] **Tarea 6.3:** Validar flujo interactivo y visualización del perfil.




