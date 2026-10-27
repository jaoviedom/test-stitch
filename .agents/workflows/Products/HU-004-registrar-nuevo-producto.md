---
description: Registrar nuevo producto
---

# HU-004: Registrar nuevo producto

## Historia de Usuario

Como administrador del sistema
Quiero crear un producto con su nombre, descripción, precio_compra, precio_venta, stock_actual, stock_minimo, estado e imagen (opcional)
Para clasificar los artículos de la tienda de forma organizada.

---

## Reglas de Negocio
- El `nombre` es obligatorio, único (case-insensitive) y con longitud máxima de 100 caracteres.
- Los precios no deben presentarse con decimales.
- Cuando se escriban los precios se deben ir poniendo un punto (.) como separadores de miles automáticamente.
- La `descripción` es opcional, con un máximo de 500 caracteres.
- La imagen se guarda en la carpeta `/media/` y en la base de datos se guarda el enlace.
- La `imagen` es opcional. Si no se pasa una, se debe guardar el enlace a una genèrica.
- El sistema debe generar automáticamente un `slug` único y amigable para URL a partir del nombre (ej. "Jabón rey" -> "jabon-rey").
- El estado por defecto al crear es `activo` (booleano).
- El estado es `activo` (booleano) si hay unidades en sotck.
- Se deben presentar las categorìas ordenadas alfabèticamente en un select con autocomplete.
- **Seguridad y Permisos (RBAC):** Solo usuarios autenticados con el rol `administrador` o con el permiso explícito `categories.create` pueden acceder a la ruta y ejecutar la creación de categorías. Usuarios con rol `usuario` o `vendedor` (sin dicho permiso) reciben `403 Forbidden`.


---

## Criterios de Aceptación

### Escenario 1: Creación exitosa

Dado que el usuario administrador accede al formulario de creación de productos por medio del menú en el sidebar,
Cuando ingresa un nombre, descripción, precio_compra, precio_venta, stock_actual, stock_minimo, estado e imagen (opcional) válidos y no registrado previamente (ej. "Coca Cola") y confirma el guardado,
Entonces el sistema persiste el producto con estado "Activo", muestra una miniatura de la imagen ingresada y retorna un mensaje de confirmación que se desvanece a los 5 segundos y tiene un botón para cerrarlo.

### Escenario 2: Nombre duplicado

Dado que ya existe un producto llamado "Coca cola x 350",
Cuando el usuario intenta registrar otra categoría con el nombre "coca cola x 350" (sin distinguir mayúsculas/minúsculas),
Entonces el sistema cancela la operación y muestra el error "El producto ya se encuentra registrado".

### Scenario 3: Bloqueo de creación de producto para rol "usuario" o "vendedor" sin permiso

Dado que un usuario autenticado con el rol "usuario" (sin permiso `categories.create`)
Cuando intenta acceder a la vista o ejecutar la acción de crear producto
Entonces recibe una respuesta 403 Forbidden y no se persiste ningún registro.