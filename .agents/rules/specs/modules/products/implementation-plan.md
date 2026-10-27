# Plan de Implementación: HU-004 Registrar Nuevo Producto

Este plan desglosa la implementación de la Historia de Usuario **HU-004 (Registrar nuevo producto)** siguiendo una metodología estricta de Desarrollo Guiado por Pruebas (TDD) en el stack **Django 5/6 + Python 3.12+ + Tailwind CSS**.

---

## Tareas Atómicas de Implementación

### Tarea 1: Suite de Pruebas Automatizadas (Fase Red)
- [x] Crear el archivo de pruebas en `tests/products/test_product_registration.py`.
- [x] Implementar fixtures con roles (`administrador`, `vendedor`, `usuario`), permisos (`inventario.add_producto`) y categorías base.
- [x] Escribir tests para el flujo principal (creación exitosa con todos los campos e imagen, creación sin imagen con fallback genérico, y verificación de relación 1:N: un producto pertenece a una categoría y `categoria.productos.all()` / `categoria.total_productos` agrupa múltiples productos).
- [x] Escribir tests para validaciones de negocio (unicidad de nombre case-insensitive "El producto ya se encuentra registrado", campos obligatorios, precios/stocks no negativos).
- [x] Escribir tests de control de acceso RBAC (redirección de usuario anónimo, 403 Forbidden para rol `usuario` y `vendedor`, acceso concedido para rol `administrador` o permiso directo).
- [x] Escribir tests de NFR (accesibilidad con atributos `label`, `role="alert"`, `aria-invalid`, y reversión atómica en caso de error).
- [x] Ejecutar suite de pruebas para validar la **Fase Red controlada** (fallo esperado por ausencia de implementación: 17 fallos controlados, 0 errores sintácticos).

### Tarea 2: Configuración Multimedia, Modelo y Migraciones
- [x] Configurar `MEDIA_URL` y `MEDIA_ROOT` en `core/settings.py` y registrar servicio de medios en `core/urls.py` para entorno de desarrollo.
- [x] Implementar el modelo `Producto` en `inventario/models.py` con su relación Many-to-One obligatoria `categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')`, campos (`nombre`, `slug`, `descripcion`, `precio_compra`, `precio_venta`, `stock_actual`, `stock_minimo`, `activo`, `imagen`, timestamps), métodos `clean`, `save` determinista de slug, y propiedades `imagen_url` y `en_stock`.
- [x] Generar y aplicar las migraciones de base de datos (`python manage.py makemigrations inventario` y `python manage.py migrate`).

### Tarea 3: Capa de Servicios y Lógica de Dominio
- [x] Implementar `CrearProductoService` en `inventario/services.py` con decorador `@transaction.atomic`.
- [x] Implementar validaciones de negocio, sanitización de datos, generación de slug y persistencia atómica del modelo `Producto`.
- [x] Gestionar el manejo seguro de archivos de imagen y asignación de imagen genérica por defecto.

### Tarea 4: Capa de Formularios y Validación
- [x] Crear `ProductoForm` en `inventario/forms.py` heredando de `forms.ModelForm`.
- [x] Configurar el queryset de `categoria` ordenado alfabéticamente (`Categoria.objects.filter(activo=True).order_by('nombre')`).
- [x] Implementar métodos `clean_nombre`, `clean_precio_compra`, `clean_precio_venta`, `clean_stock_actual`, `clean_stock_minimo` y `clean_descripcion`.
- [x] Asignar widgets con clases de Tailwind CSS, diseño ergonómico de campos y tipografía `font-mono tabular-nums` para valores numéricos.

### Tarea 5: Enrutamiento, Vistas y Control de Acceso
- [x] Implementar la vista `crear_producto_view` en `inventario/views.py` protegida con `@login_required` y `@permission_required('inventario.add_producto', raise_exception=True)`.
- [x] Procesar solicitudes GET (formulario vacío con select ordenado) y POST multipart/form-data delegando en `CrearProductoService`.
- [x] Configurar mensaje flash de éxito (`messages.success`) accesible y redirección tras guardado exitoso.
- [x] Registrar la ruta `path('productos/crear/', views.crear_producto_view, name='crear_producto')` en `inventario/urls.py`.

### Tarea 6: Plantilla Django y Sistema de Diseño UI/UX
- [x] Crear la plantilla `templates/inventario/producto_form.html` extendiendo de `layouts/base.html`.
- [x] Maquetar el formulario con tarjetas `bg-white border border-slate-200 rounded-xl shadow-xs`, diseño visual alineado a NFR-01 ("Mercado Fresco POS").
- [x] Implementar mensaje de alerta/confirmación con Alpine.js o JavaScript que se desvanece a los 5 segundos con botón de cierre accesible.
- [x] Asegurar etiquetas `<label for="...">` asociadas a cada input y mensajes de error accesibles con `role="alert"` y `aria-invalid="true"`.
- [x] Garantizar el comportamiento inmutable del sidebar drawer sin desplazar el contenedor principal.

### Tarea 7: Verificación de Calidad y Cierre
- [x] Ejecutar la suite completa de pruebas: `tests.products` confirmando **Fase Green (100% aprobado / 17 tests passed)**.
- [x] Ejecutar comprobación del framework: `python manage.py check` (0 errores).
- [x] Comprobar ausencia de migraciones pendientes: `python manage.py makemigrations --check --dry-run` (0 pendientes).
- [x] Ejecutar suite global de pruebas del proyecto (`python manage.py test`) para descartar regresiones.

