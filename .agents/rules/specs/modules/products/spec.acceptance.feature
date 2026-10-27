# language: es
Característica: Registrar nuevo producto en el catálogo (HU-004)
  Como administrador del sistema
  Quiero crear un producto con su nombre, categoría, descripción, precio_compra, precio_venta, stock_actual, stock_minimo, estado e imagen (opcional)
  Para clasificar y gestionar los artículos de la tienda de forma organizada en el inventario.

  Antecedentes:
    Dado que el sistema cuenta con los roles "administrador", "vendedor" y "usuario" configurados
    Y el permiso "inventario.add_producto" está asignado al rol "administrador"
    Y existen categorías activas registradas ("Bebidas", "Abarrotes", "Lácteos") en el sistema

  # -------------------------------------------------------------------------
  # Flujo Principal y Variaciones Válidas (Camino Feliz)
  # -------------------------------------------------------------------------

  Escenario: Creación exitosa de un producto con todos los campos obligatorios y opcionales
    Dado que un usuario autenticado con el rol "administrador" accede a la página de creación de productos "/inventario/productos/crear/"
    Cuando completa el formulario con los siguientes datos:
      | campo         | valor                                             |
      | nombre        | Coca Cola 1.5L                                    |
      | categoria     | Bebidas                                           |
      | descripcion   | Gaseosa sabor cola original botella pet no retornable |
      | precio_compra | 3500.00                                           |
      | precio_venta  | 4500.00                                           |
      | stock_actual  | 24                                                |
      | stock_minimo  | 6                                                 |
      | activo        | true                                              |
    Y adjunta una imagen válida "cocacola.jpg"
    Y envía el formulario de creación
    Entonces el producto es persistido en la base de datos dentro de una transacción atómica
    Y su nombre es "Coca Cola 1.5L"
    Y su slug generado automáticamente es "coca-cola-15l"
    Y su categoría asociada es "Bebidas"
    Y su precio de compra es 3500.00 y precio de venta es 4500.00
    Y su stock actual es 24 y stock mínimo es 6
    Y su estado "activo" es True
    Y su imagen queda almacenada en el directorio de medios
    Y el usuario es redirigido a la lista de productos o catálogo
    Y visualiza un mensaje de confirmación que se desvanece a los 5 segundos con botón para cerrarlo.

  Escenario: Creación exitosa de un producto sin imagen (asigna imagen genérica por defecto)
    Dado que un usuario autenticado con el rol "administrador" se encuentra en "/inventario/productos/crear/"
    Cuando completa el formulario ingresando los datos del producto "Arroz Diana 1kg" con categoría "Abarrotes" sin adjuntar ningún archivo de imagen
    Y envía el formulario de creación
    Entonces el producto es creado exitosamente en la base de datos
    Y la propiedad de imagen del producto resuelve al enlace de la imagen genérica predeterminada
    Y su slug generado es "arroz-diana-1kg".

  Escenario: Creación exitosa de un producto sin descripción (campo opcional)
    Dado que un usuario administrador se encuentra en "/inventario/productos/crear/"
    Cuando ingresa los campos requeridos para el producto "Azúcar Manuelita 1kg" dejando el campo descripción en blanco
    Y envía el formulario de creación
    Entonces el producto es creado con la descripción vacía y sin errores de validación.

  Escenario: Generación automática de slug único ante nombres con acentos o caracteres especiales
    Dado que un usuario administrador ingresa el nombre "Café Sello Rojo & Canela 500g"
    Cuando confirma la creación del producto
    Entonces el producto se guarda con el slug normalizado "cafe-sello-rojo-canela-500g".

  Escenario: Estado activo por defecto y consistencia con existencias de stock
    Dado que un usuario administrador accede al formulario de creación
    Cuando se renderiza el formulario
    Entonces el campo de estado "activo" viene marcado como True por defecto
    Y al registrar un producto con stock_actual mayor a 0, el producto se persiste en estado activo.

  Escenario: Despliegue de categorías ordenadas alfabéticamente en el select de asociación
    Dado que existen las categorías registradas "Lácteos", "Abarrotes", "Carnes" y "Bebidas"
    Cuando el usuario administrador abre el selector de categorías en el formulario
    Entonces las opciones se presentan ordenadas alfabéticamente: "Abarrotes", "Bebidas", "Carnes", "Lácteos".

  Escenario: Relación de pertenencia 1:N entre categoría y múltiples productos
    Dado que existe la categoría "Bebidas" registrada en el sistema
    Cuando el administrador registra los productos "Coca Cola 1.5L" y "Jugo de Naranja 1L" asignados a la categoría "Bebidas"
    Entonces ambos productos pertenecen a la categoría "Bebidas" mediante su clave foránea "categoria"
    Y la categoría "Bebidas" contiene a ambos productos a través de su relación inversa "productos.all()"
    Y la propiedad "total_productos" de la categoría refleja exactamente 2 productos asociados.

  # -------------------------------------------------------------------------
  # Validaciones de Entrada y Reglas de Negocio
  # -------------------------------------------------------------------------

  Escenario: Rechazo de producto con nombre duplicado (validación case-insensitive)
    Dado que ya existe un producto registrado con el nombre "Coca cola x 350"
    Cuando el usuario intenta registrar otro producto con el nombre "coca cola x 350"
    Y envía el formulario
    Entonces la operación es cancelada y no se persiste ningún registro duplicado
    Y el campo "nombre" presenta el atributo 'aria-invalid="true"'
    Y se muestra el mensaje de error con 'role="alert"' indicando "El producto ya se encuentra registrado".

  Escenario: Rechazo de producto sin nombre obligatorio
    Dado que un administrador se encuentra en el formulario de creación
    Cuando intenta enviar el formulario dejando el campo "nombre" vacío o con espacios en blanco
    Entonces el formulario es rechazado
    Y el campo "nombre" es marcado con 'aria-invalid="true"'
    Y se muestra un mensaje de error accesible con 'role="alert"'.

  Escenario: Rechazo de producto sin categoría asignada
    Dado que un administrador se encuentra en el formulario de creación
    Cuando envía el formulario sin seleccionar una categoría
    Entonces el formulario no es procesado
    Y el campo "categoria" presenta error de validación 'role="alert"'.

  Escenario: Validación de precios y stocks no negativos
    Dado que un usuario ingresa un precio de compra negativo (-500.00), precio de venta negativo (-1000.00) o stock negativo (-5)
    Cuando intenta guardar el producto
    Entonces el sistema rechaza los valores negativos
    Y los campos afectados se marcan con 'aria-invalid="true"' mostrando sus correspondientes mensajes de error.

  Escenario: Validación de longitud máxima en nombre y descripción
    Dado que un usuario ingresa un nombre con más de 100 caracteres o una descripción con más de 500 caracteres
    Cuando envía el formulario
    Entonces el sistema rechaza los datos y no persiste el registro.

  # -------------------------------------------------------------------------
  # Seguridad y Control de Acceso (RBAC)
  # -------------------------------------------------------------------------

  Escenario: Usuario anónimo es redirigido a la pantalla de inicio de sesión
    Dado que un visitante no autenticado intenta acceder a "/inventario/productos/crear/"
    Cuando realiza la petición GET o POST
    Entonces es redirigido a "/auth/login/?next=/inventario/productos/crear/".

  Escenario: Bloqueo con HTTP 403 Forbidden para usuario con rol base "usuario"
    Dado que un usuario autenticado pertenece únicamente al rol "usuario" (sin permiso "inventario.add_producto")
    Cuando intenta acceder por GET o POST a "/inventario/productos/crear/"
    Entonces el servidor responde con código de estado HTTP 403 Forbidden
    Y no se persiste ningún registro.

  Escenario: Bloqueo con HTTP 403 Forbidden para rol "vendedor" sin permiso de creación de producto
    Dado que un usuario autenticado con el rol "vendedor" intenta acceder o enviar datos a "/inventario/productos/crear/"
    Cuando efectúa la petición GET o POST
    Entonces recibe un código de estado HTTP 403 Forbidden
    Y ningún producto es creado.

  Escenario: Usuario no administrador pero con permiso directo "inventario.add_producto"
    Dado que existe un usuario que no es administrador pero tiene asignado directamente el permiso "inventario.add_producto"
    Cuando accede al formulario y crea un producto válido "Leche Entera 1L"
    Entonces el producto es creado exitosamente en la base de datos.

  # -------------------------------------------------------------------------
  # Criterios No Funcionales (NFR): Accesibilidad, UI/UX y Transaccionalidad
  # -------------------------------------------------------------------------

  Escenario: Accesibilidad de formulario de producto según WCAG 2.1 AA
    Dado que un administrador visualiza el formulario de creación en "/inventario/productos/crear/"
    Entonces todos los inputs tienen asociado un elemento '<label for="...">':
      | input_id          | label_for         |
      | id_nombre         | id_nombre         |
      | id_categoria      | id_categoria      |
      | id_precio_compra  | id_precio_compra  |
      | id_precio_venta   | id_precio_venta   |
      | id_stock_actual   | id_stock_actual   |
      | id_stock_minimo   | id_stock_minimo   |
      | id_descripcion    | id_descripcion    |
      | id_activo         | id_activo         |
      | id_imagen         | id_imagen         |
    Y los campos numéricos de precios y stock implementan la clase tipográfica 'font-mono tabular-nums'
    Y el layout conserva el sidebar drawer inmutable sin empujar el contenedor principal.

  Escenario: Transacción atómica estricta ante fallo inesperado
    Dado que ocurre una excepción durante el proceso de guardado del producto o su imagen
    Cuando el servicio CrearProductoService es ejecutado
    Entonces se ejecuta un rollback completo de la transacción
    Y la base de datos permanece en un estado íntegro sin registros huérfanos.
