# language: es
Característica: Registro de usuario con rol base por defecto (HU-001)
  Como visitante de la aplicación
  Quiero registrarme con mi nombre completo, nombre de usuario, correo y contraseña
  Para obtener una cuenta activa con el rol inicial de "usuario" hasta que un administrador me asigne permisos adicionales.

  Antecedentes:
    Dado que el sistema tiene inicializado el grupo de rol "usuario"

  Escenario: Registro exitoso con asignación exclusiva del rol "usuario" y redirección al dashboard
    Dado que soy un visitante no autenticado en la página de registro "/auth/register/"
    Cuando completo el formulario de registro con:
      | campo            | valor            |
      | first_name       | Juan Pérez       |
      | username         | juanperez        |
      | email            | juan@tienda.co   |
      | password1        | Password123!     |
      | password2        | Password123!     |
      | terms            | true             |
    Y envío el formulario de registro
    Entonces mi cuenta de usuario se crea en la base de datos dentro de una transacción atómica
    Y se me asigna exclusivamente el rol/grupo "usuario"
    Y mi sesión queda automáticamente autenticada
    Y soy redirigido a la ruta del dashboard principal.

  Escenario: Intento de registro con nombre de usuario o correo electrónico ya existente
    Dado que existe un usuario previamente registrado con username "juanperez" y email "juan@tienda.co"
    Y soy un visitante no autenticado en "/auth/register/"
    Cuando completo el formulario con el mismo username "juanperez" o email "juan@tienda.co"
    Y envío el formulario de registro
    Entonces no se crea un nuevo usuario en la base de datos
    Y permanezco en la página de registro
    Y visualizo un mensaje de error accesible con atributo 'role="alert"' indicando la duplicidad.

  Escenario: Rechazo de registro cuando las contraseñas no coinciden
    Dado que soy un visitante no autenticado en "/auth/register/"
    Cuando completo el formulario con contraseñas distintas en "password1" y "password2"
    Y envío el formulario de registro
    Entonces no se crea el usuario en la base de datos
    Y el campo de confirmación presenta el atributo 'aria-invalid="true"'
    Y se muestra un mensaje de error accesible con 'role="alert"' indicando que las contraseñas no coinciden.

  Escenario: Validación de campos obligatorios vacíos
    Dado que soy un visitante no autenticado en "/auth/register/"
    Cuando envío el formulario con los campos requeridos vacíos
    Entonces el formulario no es procesado
    Y los campos inválidos presentan el atributo 'aria-invalid="true"'
    Y se muestran mensajes de error con 'role="alert"' según las directrices de accesibilidad WCAG 2.1 AA.

  Escenario: Usuario con rol base "usuario" tiene restringido el acceso al catálogo de categorías
    Dado que acabo de registrarme y poseo únicamente el rol "usuario"
    Cuando intento acceder a la ruta de listar o crear categorías ("/inventario/categorias/")
    Entonces el sistema responde con código de estado HTTP 403 Forbidden.

  Escenario: Atomicidad estricta en el registro y asignación de rol
    Dado que ocurre un fallo imprevisto de base de datos durante la asignación del grupo "usuario"
    Cuando se ejecuta el servicio de registro
    Entonces la transacción de base de datos se revierte completamente (rollback)
    Y no se almacena ningún registro huérfano de usuario en la base de datos.

# -----------------------------------------------------------------------------

Característica: Gestión de múltiples roles y permisos por el Administrador (HU-002)
  Como usuario con rol "administrador"
  Quiero asignar o revocar múltiples roles ("usuario", "vendedor", "administrador") y permisos granulares a cualquier usuario
  Para controlar de forma segura quién puede ver, crear o editar recursos en la tienda TeckStore.

  Antecedentes:
    Dado que los grupos "usuario", "vendedor" y "administrador" están inicializados en el sistema
    Y el permiso oficial "authentication.manage_access" está registrado

  Escenario: Administrador visualiza el listado de usuarios con sus roles y badges
    Dado que estoy autenticado como "administrador" con el permiso "authentication.manage_access"
    Cuando accedo a la ruta de gestión de usuarios "/auth/usuarios/"
    Entonces recibo una respuesta HTTP 200 OK
    Y visualizo la tabla de usuarios con sus nombres, correos y badges de roles asignados.

  Escenario: Asignación de múltiples roles a un usuario por el Administrador
    Dado que estoy autenticado como "administrador" en "/auth/usuarios/"
    Y existe una usuaria "María" que actualmente solo posee el rol "usuario"
    Cuando envío una solicitud para actualizar los roles de "María" seleccionando los grupos "usuario" y "vendedor"
    Entonces los cambios se persisten dentro de una transacción atómica
    Y "María" ahora pertenece simultáneamente a los grupos "usuario" y "vendedor"
    Y "María" adquiere los permisos asociados al rol "vendedor" (ej. "inventario.view_categoria").

  Escenario: Otorgar un permiso granular directo a un usuario
    Dado que "María" tiene asignado el rol "vendedor"
    Y el rol "vendedor" no incluye por defecto el permiso "inventario.add_categoria"
    Cuando el "administrador" le asigna el permiso directo "inventario.add_categoria" a "María"
    Entonces "María" tiene registrado el permiso directo en su cuenta
    Y la comprobación "user.has_perm('inventario.add_categoria')" retorna verdadero.

  Escenario: Revocación de un rol asignado a un usuario
    Dado que un usuario "Carlos" posee los roles "usuario" y "vendedor"
    Cuando el "administrador" actualiza los accesos de "Carlos" dejando únicamente el rol "usuario"
    Entonces el grupo "vendedor" es desvinculado de "Carlos"
    Y "Carlos" ya no posee los permisos asociados al rol "vendedor".

  Escenario: Protección contra escalación de privilegios (Usuario sin permiso es bloqueado)
    Dado que un usuario "Pedro" posee únicamente el rol "vendedor" o "usuario" (sin "authentication.manage_access")
    Cuando intenta acceder a "/auth/usuarios/" o enviar una petición de actualización de roles
    Entonces el sistema rechaza la solicitud con código de estado HTTP 403 Forbidden.

  Escenario: Visitante no autenticado es redirigido a login al intentar acceder a la gestión de usuarios
    Dado que soy un visitante anónimo no autenticado
    Cuando intento acceder a la ruta "/auth/usuarios/"
    Entonces soy redirigido inmediatamente a la página de login con código 302.

  Escenario: Atomicidad en la actualización de roles y permisos
    Dado que ocurre un error imprevisto de base de datos durante la sincronización de permisos directos
    Cuando se ejecuta el servicio de actualización de accesos
    Entonces la transacción se cancela y revierte (rollback)
    Y los roles y permisos del usuario permanecen en su estado previo inalterado.

# -----------------------------------------------------------------------------

Característica: Inicio de Sesión Seguro (HU-003)
  Como usuario registrado en la plataforma (con rol "usuario", "vendedor" o "administrador")
  Quiero autenticarme en el sistema ingresando mis credenciales (nombre de usuario o correo electrónico, y contraseña)
  Para acceder a las funcionalidades y módulos correspondientes a mis roles asignados de manera segura y proteger la información del negocio.

  Antecedentes:
    Dado que existe un usuario registrado con username "carlosr", email "carlos@tienda.co" y contraseña "Password123!"

  Escenario: Inicio de sesión exitoso con nombre de usuario
    Dado que soy un visitante no autenticado en la ruta "/auth/login/"
    Cuando completo el formulario de login con "carlosr" y contraseña "Password123!"
    Y envío el formulario
    Entonces el sistema valida las credenciales y crea una sesión activa para el usuario "carlosr"
    Y soy redirigido al panel principal de la tienda ("/inventario/")
    Y se visualiza un mensaje de bienvenida en la interfaz.

  Escenario: Inicio de sesión exitoso utilizando correo electrónico
    Dado que soy un visitante no autenticado en "/auth/login/"
    Cuando completo el formulario con el correo "carlos@tienda.co" en el campo de identificación y contraseña "Password123!"
    Y envío el formulario
    Entonces el sistema identifica correctamente al usuario y crea la sesión autenticada
    Y soy redirigido al panel principal de la tienda ("/inventario/").

  Escenario: Redirección contextual mediante parámetro "next" (Flujo protegido)
    Dado que intenté acceder a una ruta protegida ("/inventario/productos/") sin estar autenticado
    Y el sistema me redirigió a "/auth/login/?next=/inventario/productos/"
    Cuando ingreso mis credenciales válidas y envío el formulario
    Entonces el sistema me autentica y me redirige a la ruta solicitada ("/inventario/productos/").

  Escenario: Protección contra Open Redirect en parámetro "next"
    Dado que un enlace contiene un parámetro "next" malicioso hacia un dominio externo "https://sitio-malicioso.com"
    Cuando inicio sesión con credenciales válidas
    Entonces el sistema detecta que la URL no es interna y redirige de forma segura a "/inventario/".

  Escenario: Rechazo de credenciales incorrectas o inexistentes
    Dado que me encuentro en "/auth/login/"
    Cuando intento iniciar sesión con un usuario inexistente o contraseña equivocada
    Entonces el sistema rechaza la autenticación
    Y permanezco en "/auth/login/" con código de respuesta HTTP 200
    Y se renderiza un mensaje de error accesible con atributo 'role="alert"' y estilo 'text-rose-600'
    Y el mensaje no revela si el usuario existe o si falló la contraseña para prevenir enumeración de cuentas.

  Escenario: Redirección automática de usuario ya autenticado
    Dado que ya poseo una sesión activa en el sistema
    Cuando intento ingresar a la ruta "/auth/login/"
    Entonces soy redirigido de forma inmediata al panel principal ("/inventario/") sin presentar nuevamente el formulario.

  Escenario: Gestión de persistencia de sesión con "Recordar mi sesión"
    Dado que ingreso credenciales válidas en "/auth/login/"
    Cuando marco la casilla "Recordar mi sesión en este dispositivo" y envío el formulario
    Entonces la cookie de sesión se configura con expiración persistente
    Y si la casilla no es marcada, la sesión se configura para expirar al cerrar el navegador ('session.set_expiry(0)').

# -----------------------------------------------------------------------------

Característica: Consulta y Actualización de Perfil de Usuario (HU-004)
  Como usuario autenticado en la plataforma (con rol "usuario", "vendedor" o "administrador")
  Quiero acceder a la sección "Mi Perfil" desde el menú del usuario en la barra superior o sidebar
  Para consultar mis roles asignados en modo solo lectura y actualizar mi información personal (nombre y correo) o cambiar mi contraseña de forma segura.

  Antecedentes:
    Dado que los grupos de roles "usuario", "vendedor" y "administrador" están configurados en el sistema
    Y existe un usuario registrado y autenticado con username "joseoviedo", first_name "Jose", email "jose@tienda.co"

  Escenario: Acceso permitido para cualquier rol autenticado y visualización de roles en solo lectura
    Dado que estoy autenticado como "joseoviedo" con los roles "usuario" y "vendedor"
    Cuando accedo a la ruta de perfil "/auth/perfil/"
    Entonces recibo una respuesta HTTP 200 OK
    Y visualizo mis datos actuales en el formulario: nombre "Jose" y correo "jose@tienda.co"
    Y visualizo los badges de mis roles asignados ("usuario", "vendedor") en modo de solo lectura
    Y no se permite la edición ni selección de nuevos roles en la interfaz.

  Escenario: Visitante no autenticado es redirigido a login al intentar acceder a su perfil
    Dado que soy un visitante anónimo no autenticado
    Cuando intento acceder a la ruta "/auth/perfil/"
    Entonces el sistema me redirige a "/auth/login/?next=/auth/perfil/" con código de estado HTTP 302.

  Escenario: Actualización exitosa de datos personales (Nombre y Email)
    Dado que estoy autenticado en la ruta de perfil "/auth/perfil/"
    Cuando actualizo mi nombre a "Jose Alonso" y mi correo a "jose.alonso@tienda.co"
    Y envío el formulario de información de perfil
    Entonces mis datos se persisten en la base de datos dentro de una transacción atómica
    Y soy redirigido a "/auth/perfil/"
    Y se muestra un mensaje flash accesible de confirmación exitosa
    Y la interfaz refleja el nombre "Jose Alonso" y el correo "jose.alonso@tienda.co".

  Escenario: Validación de campos obligatorios en el perfil de usuario
    Dado que estoy autenticado en la ruta de perfil "/auth/perfil/"
    Cuando intento enviar el formulario de perfil con el campo de nombre o correo electrónico vacío
    Entonces el sistema rechaza la actualización
    Y permanezco en la página de perfil con código HTTP 200
    Y los campos inválidos presentan el atributo 'aria-invalid="true"'
    Y se muestra un mensaje de error accesible con atributo 'role="alert"'.

  Escenario: Rechazo de actualización cuando el correo electrónico ya pertenece a otra cuenta
    Dado que existe otro usuario registrado con el correo "admin@tienda.co"
    Y estoy autenticado como "joseoviedo" con correo "jose@tienda.co" en "/auth/perfil/"
    Cuando intento cambiar mi correo a "admin@tienda.co"
    Y envío el formulario de perfil
    Entonces el sistema rechaza la actualización indicando que el correo ya está en uso
    Y mi correo en la base de datos permanece inalterado como "jose@tienda.co"
    Y se visualiza un mensaje de error accesible con 'role="alert"'.

  Escenario: Cambio de contraseña exitoso validando contraseña actual y confirmación
    Dado que mi contraseña actual es "Password123!"
    Y me encuentro autenticado en "/auth/perfil/"
    Cuando ingreso mi contraseña actual "Password123!"
    Y defino una nueva contraseña válida "NuevaPassword456!" con su respectiva confirmación "NuevaPassword456!"
    Y envío el formulario de cambio de contraseña
    Entonces mi contraseña se actualiza en la base de datos aplicando un hash criptográfico seguro
    Y mi sesión de usuario se mantiene activa sin desconexión involuntaria ('update_session_auth_hash')
    Y se muestra una notificación accesible de éxito confirmando el cambio de contraseña.

  Escenario: Rechazo de cambio de contraseña cuando la contraseña actual es incorrecta
    Dado que me encuentro autenticado en "/auth/perfil/"
    Cuando ingreso una contraseña actual errónea "ClaveEquivocada1!" y una nueva contraseña "NuevaPassword456!"
    Y envío el formulario de cambio de contraseña
    Entonces el sistema rechaza el cambio de contraseña
    Y se muestra un mensaje de error accesible con atributo 'role="alert"' y estilo de advertencia 'text-rose-600'
    Y mi contraseña anterior permanece activa.

  Escenario: Rechazo de cambio de contraseña cuando las contraseñas nuevas no coinciden
    Dado que me encuentro autenticado en "/auth/perfil/"
    Cuando ingreso mi contraseña actual válida "Password123!"
    Y en nueva contraseña ingreso "NuevaPassword456!" pero en confirmación ingreso "OtraDiferente789!"
    Y envío el formulario de cambio de contraseña
    Entonces el sistema rechaza la solicitud
    Y los campos de nueva contraseña presentan el atributo 'aria-invalid="true"'
    Y se muestra un mensaje de error con 'role="alert"' indicando que las contraseñas no coinciden.

  Escenario: Inmutabilidad de roles y permisos desde el propio perfil (Seguridad RBAC)
    Dado que estoy autenticado con el rol único de "usuario" en "/auth/perfil/"
    Cuando envío una petición HTTP POST inyectando parámetros maliciosos como 'roles=["administrador"]', 'groups=[1, 2]' o 'is_staff=True'
    Entonces el sistema procesa únicamente los campos legítimos de perfil ('first_name', 'email')
    Y mis grupos y permisos en la base de datos permanecen exactamente iguales
    Y no adquiero ningún privilegio administrativo indebido.

  Escenario: Atomicidad estricta en la actualización de perfil y cambio de credenciales
    Dado que ocurre un fallo imprevisto de base de datos durante el guardado de los datos de perfil
    Cuando se ejecuta el servicio de actualización de perfil
    Entonces la transacción de base de datos se revierte completamente (rollback)
    Y no se persisten cambios parciales o inconsistentes en el modelo de usuario.


