---
description: Inicio de sesión
---

# HU-003: Inicio de Sesión Seguro (Login)

## Historia de Usuario
**Como** usuario registrado en la plataforma (con rol `usuario`, `vendedor` o `administrador`)  
**Quiero** autenticarme en el sistema ingresando mis credenciales (nombre de usuario o correo electrónico, y contraseña)  
**Para** acceder a las funcionalidades y módulos correspondientes a mis roles asignados de manera segura y proteger la información del negocio.

---

## Criterios de Aceptación (Gherkin)

Scenario: Inicio de sesión exitoso con nombre de usuario
  Given que soy un visitante no autenticado en la ruta "/auth/login/"
  And existe una cuenta registrada con nombre de usuario "carlosr" y contraseña válida "Password123!"
  When completo el formulario con "carlosr" y "Password123!"
  Then el sistema valida las credenciales y crea una sesión activa para el usuario "carlosr"
  And soy redirigido al panel principal de la tienda ("/inventario/")
  And se visualiza un mensaje de bienvenida en la interfaz.

Scenario: Inicio de sesión exitoso utilizando correo electrónico
  Given que soy un visitante no autenticado en "/auth/login/"
  And existe una cuenta registrada con correo "carlos@tienda.co", nombre de usuario "carlosr" y contraseña "Password123!"
  When ingreso "carlos@tienda.co" en el campo de identificación y "Password123!" en la contraseña
  Then el sistema identifica correctamente al usuario y crea la sesión autenticada
  And soy redirigido al panel principal de la tienda ("/inventario/").

Scenario: Redirección contextual mediante parámetro "next" (Flujo protegido)
  Given que intenté acceder a una ruta protegida ("/inventario/productos/") sin estar autenticado
  And el sistema me redirigió a "/auth/login/?next=/inventario/productos/"
  When ingreso mis credenciales válidas y envío el formulario
  Then el sistema me autentica y me redirige a la ruta solicitada ("/inventario/productos/").

Scenario: Protección contra Open Redirect en parámetro "next"
  Given que un enlace externo contiene un parámetro malicioso "/auth/login/?next=https://sitio-malicioso.com"
  When inicio sesión con credenciales válidas
  Then el sistema detecta que la URL no es interna y redirige de forma segura a "/inventario/".

Scenario: Rechazo de credenciales incorrectas o inexistentes
  Given que me encuentro en "/auth/login/"
  When intento iniciar sesión con un usuario inexistente o contraseña equivocada
  Then el sistema rechaza la autenticación
  And permanezco en "/auth/login/" con código de respuesta HTTP 200
  And se renderiza un mensaje de error accesible con `role="alert"` y estilo `text-rose-600`
  And el mensaje no revela si el usuario existe o si falló la contraseña (prevención de enumeración de cuentas).

Scenario: Redirección automática de usuario ya autenticado
  Given que ya poseo una sesión activa en el sistema
  When intento ingresar a la ruta "/auth/login/"
  Then soy redirigido de forma inmediata al panel principal ("/inventario/") sin presentar nuevamente el formulario.

Scenario: Gestión de persistencia de sesión con "Recordar mi sesión"
  Given que ingreso credenciales válidas en "/auth/login/"
  When marco la casilla "Recordar mi sesión en este dispositivo" y envío el formulario
  Then la cookie de sesión se configura para persistir durante el periodo extendido del sistema
  And si la casilla no es marcada, la sesión se configura para expirar al cerrar el navegador (`session.set_expiry(0)`).

---

## Directrices Técnicas y Restricciones NFR (Para Compuerta 1)

1. **Rutas y Vistas (Django Backend):**
   - Ruta: `path('login/', views.login_view, name='login')` en `authentication/urls.py` (con resolución inversa `authentication:login`).
   - Controlador: `login_view(request: HttpRequest) -> HttpResponse` en `authentication/views.py`.
   - Soporte de autenticación dual (por `username` o por `email`) mediante resolución previa en el servicio de autenticación o backend personalizado.
   - Validación estricta del parámetro `next` mediante `django.utils.http.url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()})`.
   - Redirección preventiva: Si `request.user.is_authenticated` es verdadero al inicio de la petición, redirigir a `inventario:dashboard`.

2. **Capa de Dominio y Servicios (`authentication/services.py`):**
   - Servicio desacoplado: `AuthenticateUserService.execute(identifier: str, password: str, request: HttpRequest = None) -> Optional[User]`.
   - Manejo de búsqueda indiferente a mayúsculas/minúsculas para username o email (`User.objects.filter(...)`) y llamada a `django.contrib.auth.authenticate`.

3. **Capa de Formulario y Validación (`authentication/forms.py`):**
   - Clase `LoginForm(forms.Form)`.
   - Campos:
     - `username`: `forms.CharField` (label "Usuario o Correo", requerido, widget accesible con placeholder e ícono de usuario).
     - `password`: `forms.CharField` (label "Contraseña", requerido, widget `PasswordInput`).
     - `remember_me`: `forms.BooleanField` (label "Recordar mi sesión en este dispositivo", requerido `False`).
   - Validación de limpieza (`clean`) con asignación de mensajes accesibles en `non_field_errors`.

4. **Cumplimiento UI/UX (`01-ui-ux-system.md` - Paleta Mercado Fresco POS) y Accesibilidad (WCAG 2.1 AA):**
   - Plantilla: `authentication/templates/authentication/login.html` extendiendo de `layouts/auth.html`.
   - Formulario con token de seguridad `{% csrf_token %}` obligatorio.
   - Labels explícitos vinculados mediante atributo `for` a los `id` de los inputs (`id_username`, `id_password`, `remember_me`).
   - Mensajería de error con contenedor accesible `role="alert"`, `aria-live="polite"` y estilos semánticos `bg-rose-50 border border-rose-200 text-rose-800`.
   - Botón principal de acción con gradiente y token primario de diseño, y enlace accesible hacia el registro (`authentication:register`).
