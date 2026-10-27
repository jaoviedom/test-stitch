# language: es
Característica: Registrar nueva categoría de productos (HU-001)
  Como administrador del sistema
  Quiero crear una categoría con su nombre y descripción
  Para clasificar los artículos de la tienda de forma organizada.

  Antecedentes:
    Dado que el sistema cuenta con los roles "administrador", "vendedor" y "usuario" configurados
    Y el permiso "inventario.add_categoria" está asignado al rol "administrador"

  # -------------------------------------------------------------------------
  # Flujo Principal y Variaciones Válidas (Camino Feliz)
  # -------------------------------------------------------------------------

  Escenario: Creación exitosa de una categoría con nombre y descripción
    Dado que un usuario autenticado con el rol "administrador" accede a la página de creación de categorías "/inventario/categorias/crear/"
    Cuando completa el formulario con los siguientes datos:
      | campo       | valor                                                      |
      | nombre      | Bebidas y Licores                                          |
      | descripcion | Bebidas frías, jugos naturales, gaseosas y licores varios |
      | activo      | true                                                       |
    Y envía el formulario de creación
    Entonces la categoría es persistida en la base de datos dentro de una transacción atómica
    Y su nombre es "Bebidas y Licores"
    Y su slug generado automáticamente es "bebidas-y-licores"
    Y su estado "activo" es True
    Y el usuario es redirigido a la lista de categorías
    Y visualiza un mensaje de éxito accesible que confirma la creación.

  Escenario: Creación exitosa de una categoría sin descripción (campo opcional)
    Dado que un usuario autenticado con el rol "administrador" se encuentra en "/inventario/categorias/crear/"
    Cuando completa el formulario ingresando únicamente el nombre "Snacks y Golosinas"
    Y envía el formulario de creación
    Entonces la categoría es creada con el nombre "Snacks y Golosinas"
    Y el campo de descripción permanece vacío
    Y su slug generado es "snacks-y-golosinas"
    Y su estado es "activo".

  Escenario: Generación automática de slug único ante nombres con acentos o caracteres especiales
    Dado que un usuario autenticado con el rol "administrador" se encuentra en "/inventario/categorias/crear/"
    Cuando ingresa el nombre "Cafés & Tés Especiales"
    Y confirma el formulario
    Entonces la categoría se guarda con el slug normalizado "cafes-tes-especiales".

  # -------------------------------------------------------------------------
  # Validaciones de Entrada y Reglas de Negocio
  # -------------------------------------------------------------------------

  Escenario: Rechazo de categoría con nombre duplicado (validación case-insensitive)
    Dado que existe previamente una categoría registrada con el nombre "Abarrotes"
    Y un usuario administrador intenta registrar una nueva categoría con el nombre "abarrotes"
    Cuando envía el formulario
    Entonces no se crea ningún registro adicional en la base de datos
    Y permanece en el formulario de creación
    Y el campo "nombre" presenta el atributo 'aria-invalid="true"'
    Y se muestra un mensaje de error accesible con 'role="alert"' indicando "La categoría ya se encuentra registrada".

  Escenario: Validación de campo nombre obligatorio vacío
    Dado que un usuario autenticado con el rol "administrador" se encuentra en "/inventario/categorias/crear/"
    Cuando envía el formulario con el campo "nombre" vacío o solo espacios en blanco
    Entonces no se crea ninguna categoría
    Y el campo "nombre" presenta 'aria-invalid="true"'
    Y se muestra un mensaje de error accesible con 'role="alert"'.

  Escenario: Validación de longitud máxima en nombre y descripción
    Dado que un usuario administrador se encuentra en el formulario de creación
    Cuando ingresa un nombre que supera los 100 caracteres o una descripción superior a 500 caracteres
    Y envía el formulario
    Entonces el formulario es rechazado con errores de validación
    Y se señalan los campos excedidos con 'aria-invalid="true"' y mensaje 'role="alert"'.

  # -------------------------------------------------------------------------
  # Seguridad y Control de Acceso (RBAC)
  # -------------------------------------------------------------------------

  Escenario: Usuario anónimo es redirigido a la pantalla de inicio de sesión
    Dado que un visitante no autenticado intenta acceder a "/inventario/categorias/crear/"
    Cuando realiza la petición GET o POST
    Entonces es redirigido a "/auth/login/?next=/inventario/categorias/crear/".

  Escenario: Bloqueo con HTTP 403 Forbidden para usuario con rol base "usuario"
    Dado que un usuario autenticado pertenece únicamente al rol "usuario" (sin permiso "inventario.add_categoria")
    Cuando intenta acceder por GET o POST a "/inventario/categorias/crear/"
    Entonces el servidor responde con código de estado HTTP 403 Forbidden
    Y no se persiste ningún registro.

  Escenario: Bloqueo con HTTP 403 Forbidden para rol "vendedor" sin permiso de creación
    Dado que un usuario autenticado con el rol "vendedor" intenta acceder o enviar datos a "/inventario/categorias/crear/"
    Cuando efectúa la petición
    Entonces recibe un código de estado HTTP 403 Forbidden
    Y ninguna categoría es creada.

  Escenario: Usuario no administrador pero con permiso directo "inventario.add_categoria"
    Dado que existe un usuario que no es administrador pero tiene asignado directamente el permiso "inventario.add_categoria"
    Cuando accede al formulario y crea una categoría válida "Limpieza y Hogar"
    Entonces la categoría es creada exitosamente en la base de datos.

  # -------------------------------------------------------------------------
  # NFR: Accesibilidad y Transacciones Atómicas
  # -------------------------------------------------------------------------

  Escenario: Accesibilidad de formulario según WCAG 2.1 AA
    Dado que un administrador visualiza el formulario de creación en "/inventario/categorias/crear/"
    Entonces todos los inputs tienen asociado un elemento '<label for="...">':
      | input_id          | label_for         |
      | id_nombre         | id_nombre         |
      | id_descripcion    | id_descripcion    |
      | id_activo         | id_activo         |
    Y la estructura del layout conserva el sidebar drawer inmutable sin desplazar el contenido principal.

  Escenario: Transacción atómica estricta ante fallo inesperado
    Dado que ocurre una excepción crítica durante el proceso de guardado en base de datos
    Cuando el servicio de creación de categoría es invocado
    Entonces todos los cambios se revierten automáticamente (rollback)
    Y no queda ningún registro persistido a medias en la base de datos.


# =============================================================================
# HISTORIA DE USUARIO HU-002: Editar categoría
# =============================================================================

Característica: Editar categoría existente (HU-002)
  Como administrador del sistema
  Quiero actualizar el nombre o descripción de una categoría
  Para corregir errores tipográficos o reclasificar grupos de productos.

  Antecedentes:
    Dado que el sistema cuenta con los roles "administrador", "vendedor" y "usuario" configurados
    Y el permiso "inventario.change_categoria" está asignado al rol "administrador"

  # -------------------------------------------------------------------------
  # Flujo Principal y Variaciones Válidas (Camino Feliz)
  # -------------------------------------------------------------------------

  Escenario: Edición exitosa de datos y recálculo automático de slug
    Dado que existe una categoría con nombre "Lácteos" y descripción "Productos lácteos básicos"
    Y un usuario administrador accede a su formulario de edición "/inventario/categorias/{id}/editar/"
    Cuando actualiza el nombre a "Lácteos y Quesos" y la descripción a "Quesos frescos, madurados y leches"
    Y envía el formulario de actualización
    Entonces los cambios son persistidos en la base de datos dentro de una transacción atómica
    Y el nombre de la categoría pasa a ser "Lácteos y Quesos"
    Y su slug se actualiza automáticamente a "lacteos-y-quesos"
    Y su descripción se actualiza correctamente
    Y el usuario es redirigido al listado de categorías con mensaje de confirmación accesible.

  Escenario: Actualización exitosa manteniendo el mismo nombre (sin conflicto de unicidad)
    Dado que existe una categoría con nombre "Panadería" y descripción vacía
    Y un administrador accede a su formulario de edición
    Cuando conserva el nombre "Panadería" pero añade la descripción "Pan fresco y tostadas" y cambia el estado activo
    Y envía el formulario
    Entonces el registro se actualiza correctamente sin generar error de duplicidad
    Y el slug permanece "panaderia".

  Escenario: Normalización de nuevo slug con tildes y caracteres especiales al editar
    Dado que existe una categoría "Frutas"
    Cuando el administrador edita su nombre a "Frutas & Cítricos Seleccionados"
    Y guarda los cambios
    Entonces el slug se actualiza a "frutas-citricos-seleccionados".

  # -------------------------------------------------------------------------
  # Validaciones de Entrada y Reglas de Negocio
  # -------------------------------------------------------------------------

  Escenario: Rechazo al intentar renombrar a un nombre ya existente en otra categoría (case-insensitive)
    Dado que existen las categorías "Bebidas" y "Snacks"
    Y el administrador edita la categoría "Snacks"
    Cuando intenta cambiar su nombre a "Bebidas" o "bebidas"
    Y envía el formulario
    Entonces la actualización es rechazada
    Y el registro "Snacks" conserva sus datos originales en la base de datos
    Y se muestra el error de validación "La categoría ya se encuentra registrada"
    Y el campo nombre presenta el atributo 'aria-invalid="true"' y mensaje 'role="alert"'.

  Escenario: Rechazo de actualización con nombre vacío o longitud excedida
    Dado que el administrador edita una categoría existente
    Cuando borra el nombre dejando el campo vacío o ingresa más de 100 caracteres en nombre o más de 500 en descripción
    Y envía el formulario
    Entonces los cambios no son guardados
    Y se muestran los errores de validación correspondientes con 'role="alert"' y 'aria-invalid="true"'.

  # -------------------------------------------------------------------------
  # Seguridad y Control de Acceso (RBAC)
  # -------------------------------------------------------------------------

  Escenario: Bloqueo de acceso anónimo a la ruta de edición
    Dado que un visitante no autenticado intenta acceder a "/inventario/categorias/{id}/editar/"
    Cuando realiza la petición GET o POST
    Entonces es redirigido a "/auth/login/?next=/inventario/categorias/{id}/editar/".

  Escenario: Bloqueo con HTTP 403 Forbidden para usuario con rol base "usuario"
    Dado que un usuario autenticado con rol "usuario" (sin permiso "inventario.change_categoria")
    Cuando intenta acceder por GET o enviar POST a "/inventario/categorias/{id}/editar/"
    Entonces el sistema responde con código HTTP 403 Forbidden
    Y ningún cambio es aplicado en la base de datos.

  Escenario: Bloqueo con HTTP 403 Forbidden para rol "vendedor" sin permiso de edición
    Dado que un usuario autenticado con rol "vendedor" intenta editar una categoría
    Cuando envía la petición
    Entonces recibe un código HTTP 403 Forbidden y la categoría permanece inalterada.

  Escenario: Usuario no administrador pero con permiso directo "inventario.change_categoria"
    Dado que un usuario tiene asignado directamente el permiso "inventario.change_categoria"
    Cuando accede al formulario y edita una categoría existente
    Entonces los cambios son procesados y guardados exitosamente.

  Escenario: Respuesta 404 Not Found al intentar editar una categoría inexistente
    Dado que un administrador intenta acceder a "/inventario/categorias/999999/editar/" con un identificador inexistente
    Cuando realiza la petición GET o POST
    Entonces el servidor responde con código de estado HTTP 404 Not Found.

  # -------------------------------------------------------------------------
  # NFR: Accesibilidad y Transacciones Atómicas
  # -------------------------------------------------------------------------

  Escenario: Accesibilidad en el formulario de edición según WCAG 2.1 AA
    Dado que un administrador abre el formulario de edición de una categoría
    Entonces los campos presentan los valores actuales precargados
    Y cada input está vinculado a su elemento '<label for="...">':
      | input_id          | label_for         |
      | id_nombre         | id_nombre         |
      | id_descripcion    | id_descripcion    |
      | id_activo         | id_activo         |
    Y la estructura del layout conserva el sidebar drawer inmutable sin desplazar el contenido.

  Escenario: Transacción atómica estricta durante la edición ante fallo inesperado
    Dado que ocurre un error de persistencia durante la actualización de la categoría
    Cuando el servicio de actualización es ejecutado
    Entonces se realiza un rollback automático de la transacción
    Y los datos de la categoría en la base de datos permanecen exactamente en su estado previo.


# =============================================================================
# HISTORIA DE USUARIO HU-003: Consultar y listar categorías
# =============================================================================

Característica: Consultar y listar categorías (HU-003)
  Como administrador o encargado de inventario
  Quiero ver la lista de categorías existentes y buscar por nombre
  Para verificar la parametrización del catálogo y el total de productos asociados.

  Antecedentes:
    Dado que el sistema cuenta con los roles "administrador", "vendedor" y "usuario" configurados
    Y el permiso "inventario.view_categoria" está asignado a los roles "administrador" y "vendedor"

  # -------------------------------------------------------------------------
  # Flujo Principal y Visualización Paginada
  # -------------------------------------------------------------------------

  Escenario: Visualización paginada de categorías con columnas requeridas
    Dado que existen 15 categorías registradas en el sistema ordenadas alfabéticamente
    Y un usuario con rol "administrador" accede a "/inventario/categorias/"
    Cuando visualiza la pantalla del catálogo de categorías
    Entonces el sistema renderiza una tabla paginada mostrando un máximo de 10 categorías en la primera página
    Y cada fila contiene: Nombre, Slug URL, Descripción, Conteo de productos asociados, Estado ("Activa" / "Inactiva") y Acciones
    Y la interfaz presenta los controles de paginación accesibles (Página 1 de 2, botón Siguiente habilitado).

  Escenario: Navegación a la segunda página del catálogo
    Dado que existen 15 categorías registradas en el catálogo
    Y el usuario se encuentra en "/inventario/categorias/?page=2"
    Cuando visualiza la tabla
    Entonces se listan las 5 categorías restantes
    Y el control de paginación indica "Página 2 de 2" con el botón Anterior habilitado.

  # -------------------------------------------------------------------------
  # Búsqueda por Texto
  # -------------------------------------------------------------------------

  Escenario: Búsqueda exitosa por nombre de categoría (filtro por término clave)
    Dado que existen las categorías "Bebidas", "Abarrotes", "Lácteos y Quesos" y "Bebidas Alcohólicas"
    Y el usuario ingresa el término "bebidas" en el buscador de categorías
    Cuando se ejecuta la búsqueda enviando el parámetro "q=bebidas"
    Entonces la tabla muestra únicamente las categorías cuyo nombre o descripción coinciden con el término ("Bebidas" y "Bebidas Alcohólicas")
    Y las categorías no coincidentes ("Abarrotes", "Lácteos y Quesos") quedan excluidas del resultado.

  Escenario: Búsqueda sin coincidencias presenta estado vacío amigable
    Dado que existen categorías en el sistema
    Y el usuario busca el término "ElectrodomésticosInexistentes"
    Cuando se procesa la consulta en "/inventario/categorias/?q=ElectrodomésticosInexistentes"
    Entonces la tabla no muestra registros
    Y se visualiza un estado vacío descriptivo con mensaje "No se encontraron categorías que coincidan con su búsqueda"
    Y se ofrece un enlace o botón para "Limpiar búsqueda" y volver al listado completo.

  # -------------------------------------------------------------------------
  # Seguridad y Control de Acceso (RBAC)
  # -------------------------------------------------------------------------

  Escenario: Usuario anónimo es redirigido a login al intentar listar categorías
    Dado que un visitante no autenticado intenta acceder a "/inventario/categorias/"
    Cuando realiza la petición GET
    Entonces es redirigido a "/auth/login/?next=/inventario/categorias/".

  Escenario: Bloqueo con HTTP 403 Forbidden para usuario con rol base "usuario"
    Dado que un usuario autenticado pertenece únicamente al rol "usuario" (sin permiso "inventario.view_categoria")
    Cuando intenta acceder por GET a "/inventario/categorias/"
    Entonces el servidor responde con código de estado HTTP 403 Forbidden
    Y no tiene acceso a la información del catálogo.

  Escenario: Acceso permitido para usuario con rol "vendedor"
    Dado que un usuario autenticado pertenece al rol "vendedor" (con permiso "inventario.view_categoria")
    Cuando accede por GET a "/inventario/categorias/"
    Entonces la respuesta tiene código de estado HTTP 200 OK
    Y visualiza el listado de categorías
    Y los botones de modificación (Nueva Categoría / Editar) se encuentran ocultos según sus permisos.

  Escenario: Usuario con permiso directo "inventario.view_categoria" puede listar
    Dado que existe un usuario con el permiso directo "inventario.view_categoria"
    Cuando accede al listado de categorías
    Entonces recibe una respuesta HTTP 200 OK y visualiza las categorías.

  # -------------------------------------------------------------------------
  # NFR: Rendimiento (Prevención N+1) y Accesibilidad WCAG 2.1 AA
  # -------------------------------------------------------------------------

  Escenario: Eficiencia en consultas ORM y prevención de consultas N+1
    Dado que existen múltiples categorías registradas
    Cuando un usuario autorizado consulta la vista "/inventario/categorias/"
    Entonces el número de consultas SQL ejecutadas por Django no se incrementa linealmente con el número de filas mostradas.

  Escenario: Accesibilidad en buscador y paginación según WCAG 2.1 AA
    Dado que un usuario autorizado visualiza la vista de catálogo de categorías
    Entonces el campo de búsqueda cuenta con un '<label for="search-input">' o atributo accesible
    Y los controles de paginación tienen atributos 'aria-label' descriptivos ("Página anterior", "Página siguiente")
    Y las cifras numéricas y códigos utilizan la tipografía 'font-mono tabular-nums'.
