# Plan de Implementación: HU-003 Consultar y Listar Categorías

Este plan describe las tareas atómicas y secuenciales requeridas para implementar la funcionalidad de consulta, búsqueda y paginación del catálogo de categorías en TeckStore bajo la metodología Spec-Driven Development (SDD) y TDD estricto.

---

## 1. Información General
- **Módulo:** `catalog`
- **Historia de Usuario:** `HU-003: Consultar y listar categorías`
- **Aplicación Django:** `inventario`
- **Permiso Requerido:** `inventario.view_categoria`
- **Especificación Gherkin:** `.agents/rules/specs/modules/catalog/spec.acceptance.feature`
- **Contrato Técnico:** `.agents/rules/specs/modules/catalog/spec.contract.yaml`

---

## 2. Tareas de Implementación

### Tarea 1: Suite de Pruebas Automatizadas (Fase Red para HU-003)
- [x] **1.1** Crear el archivo de pruebas `tests/catalog/test_category_listing.py` con fixtures para los roles `administrador`, `vendedor`, `usuario` y usuario con permiso directo `inventario.view_categoria`.
- [x] **1.2** Codificar pruebas unitarias y de integración para cada escenario Gherkin de HU-003:
  - `test_servicio_listar_categorias_retorna_ordenadas_por_nombre`: Verifica retorno ordenado alfabéticamente.
  - `test_servicio_listar_categorias_filtra_por_busqueda`: Comprueba filtrado case-insensitive por nombre y descripción.
  - `test_servicio_busqueda_sin_coincidencias_retorna_vacio`: Comprueba QuerySet vacío ante término inexistente.
  - `test_vista_listado_paginado_primera_pagina`: Con 15 categorías, la primera página muestra 10 y `has_next() is True`.
  - `test_vista_listado_paginado_segunda_pagina`: Petición con `?page=2` muestra las 5 categorías restantes y `has_previous() is True`.
  - `test_vista_busqueda_por_parametro_q`: Petición con `?q=bebidas` filtra y muestra solo las coincidencias.
  - `test_vista_busqueda_sin_resultados_muestra_estado_vacio`: Verifica mensaje amigable y enlace de limpiar búsqueda.
  - `test_paginacion_preserva_parametro_de_busqueda_en_enlaces`: Comprueba que los links de página incluyan `q=...&page=...`.
  - `test_usuario_anonimo_redirigido_al_login_al_listar`: Redirección 302 a `/auth/login/?next=/inventario/categorias/`.
  - `test_usuario_rol_usuario_recibe_403_forbidden`: Bloqueo estricto con HTTP 403 Forbidden para rol base.
  - `test_usuario_rol_vendedor_puede_listar_categorias`: Acceso permitido con HTTP 200 OK y botones de gestión ocultos.
  - `test_usuario_con_permiso_directo_view_categoria_puede_listar`: Acceso permitido para usuario con permiso directo.
  - `test_nfr_prevencion_n_plus_one_queries`: Verifica número constante y eficiente de queries ORM.
  - `test_nfr_accesibilidad_buscador_y_paginacion`: Verifica presencia de `<label for="search-input">`, atributos `aria-label` en paginador y clases `tabular-nums`.
- [x] **1.3** Ejecutar la suite con `python manage.py test tests.catalog.test_category_listing` y confirmar el fallo esperado en Fase Roja.

### Tarea 2: Capa de Dominio (Servicio de Consulta)
- [x] **2.1** Implementar la clase `ListarCategoriasService` en `inventario/services.py` con su método estático `get_queryset(query: str = "")`.
- [x] **2.2** Aplicar filtrado con `Q(nombre__icontains=query) | Q(descripcion__icontains=query)` si se proporciona un término de búsqueda.
- [x] **2.3** Asegurar el ordenamiento consistente por `nombre`.

### Tarea 3: Controlador y Vista de Listado
- [x] **3.1** Actualizar `categorias_view` en `inventario/views.py` protegiéndola con `@login_required` y `@permission_required('inventario.view_categoria', raise_exception=True)`.
- [x] **3.2** Extraer parámetros `q` y `page` de `request.GET`.
- [x] **3.3** Integrar `django.core.paginator.Paginator` configurado en 10 elementos por página y capturar `InvalidPage` / `EmptyPage`.
- [x] **3.4** Pasar al contexto: `page_obj`, `categorias`, `q`, `total_categorias`, `active_nav`.

### Tarea 4: Plantillas Django y Frontend UI/UX
- [x] **4.1** Actualizar `templates/inventario/categoria_list.html` incorporando el formulario de búsqueda accesible (`<form method="get">`, input con `id="search-input"`, `name="q"`, `<label for="search-input">`, botón de enviar y botón de limpiar si `q` está presente).
- [x] **4.2** Añadir columna "Total Productos" con formato `tabular-nums`.
- [x] **4.3** Implementar bloque de navegación de páginas accesible con botones anterior/siguiente (`aria-label`) preservando el parámetro `q`.
- [x] **4.4** Añadir mensaje y estado vacío específico para búsquedas sin coincidencias.

### Tarea 5: Verificación de Calidad y Cierre en Verde
- [x] **5.1** Ejecutar la suite de pruebas del módulo: `python manage.py test tests.catalog` hasta obtener 100% de tests en verde.
- [x] **5.2** Ejecutar la verificación de Django: `python manage.py check`.
- [x] **5.3** Verificar que no existan migraciones pendientes: `python manage.py makemigrations --check --dry-run`.
- [x] **5.4** Ejecutar la suite global del proyecto: `python manage.py test` para descartar regresiones.
