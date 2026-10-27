---
description: Workflow 01 - Formalización de Especificaciones a Plan de Implementación (Spec to Plan) para Django
---

# Workflow 01: Especificación a Plan de Implementación (Spec to Plan) - Django

Este workflow transforma una Historia de Usuario inicial en artefactos formales de especificación, contratos técnicos y un plan atómico de implementación guiado por TDD para el stack **Django 5/6 + Python 3.12+ + Tailwind CSS**.

---

## 1. Documentación Mandatoria a Consultar

Antes de generar o modificar cualquier artefacto de especificación, el agente **DEBE** leer y contrastar:
1. [.agents/rules/django-fullstack.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/django-fullstack.md): Estándares arquitectónicos, tipado, convenciones de Django ORM, formularios, servicios y testing.
2. [.agents/rules/sdd-workflow.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/sdd-workflow.md): Reglas de compuertas, protocolo de aprobación humana y ciclo de retrofit.
3. [.agents/rules/specs/auth.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/specs/auth.md): Catálogo oficial de grupos (`Group`), permisos (`<app_label>.<codename>`) y matriz RBAC.
4. [.agents/rules/nfr/01-ui-ux-system.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/nfr/01-ui-ux-system.md): Restricciones no funcionales de UI/UX, tokens semánticos de Tailwind, layout maestro y accesibilidad WCAG 2.1 AA.
5. Archivo de Historia de Usuario de entrada: `.agents/workflows/{modulo}/HU-{id}-{slug}.md`.

---

## 2. Entradas y Salidas

### Entradas
- Archivo de Historia de Usuario: `.agents/workflows/{modulo}/HU-{id}-{slug}.md`.
- Reglas de negocio y criterios de aceptación iniciales provistos por el usuario.

### Salidas (Artefactos Formales a Generar en `.agents/rules/specs/modules/{modulo}/`)
1. **`spec.acceptance.feature`**: Criterios de aceptación detallados en sintaxis Gherkin (Given-When-Then).
2. **`spec.contract.yaml`**: Contrato técnico formal para Django (modelos, servicios, formularios, URLs, vistas, permisos y componentes de plantilla).
3. **`implementation-plan.md`**: Plan de tareas desglosado paso a paso con enfoque TDD estricto (Red -> Green -> Refactor).

---

## 3. Protocolo de Ejecución Paso a Paso

### Paso 1: Análisis de Requisitos y Mapeo de Dominio
- Extraer los actores principales, precondiciones y reglas de negocio de la Historia de Usuario.
- Identificar los grupos/roles y permisos necesarios consultando [.agents/rules/specs/auth.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/specs/auth.md).
- Definir qué aplicación de Django alojará la funcionalidad (`authentication`, `inventario`, etc.).

### Paso 2: Redacción de Escenarios Gherkin (`spec.acceptance.feature`)
- Redactar escenarios exhaustivos cubriendo:
  - **Flujo principal (Camino feliz):** Ejecución exitosa de la acción con usuario autorizado.
  - **Validaciones de formulario:** Errores de campos obligatorios, formatos inválidos o duplicidad.
  - **Autorización RBAC:** Intento de acceso de usuarios anónimos (redirección a login) y usuarios autenticados sin el permiso correspondiente (respuesta `403 Forbidden`).
  - **Casos de borde y NFR:** Estados vacíos (*empty states*), atributos de accesibilidad (`role="alert"`, `aria-invalid`) y persistencia atómica.

### Paso 3: Especificación del Contrato Técnico (`spec.contract.yaml`)
El contrato debe estructurarse obligatoriamente bajo los siguientes apartados:
- **`models`**:
  - Nombre del modelo, tabla `db_table` y campos con sus tipos (`CharField`, `ForeignKey`, `DecimalField`, etc.).
  - Opciones de campo: `null`, `blank`, `on_delete`, `choices`, `db_index`.
  - Métodos requeridos: `__str__()` y `clean()` si aplica validación a nivel de modelo.
- **`services`**:
  - Clase o función de servicio en `<app>/services.py` o `<app>/actions/`.
  - Parámetros estrictamente tipados y valor de retorno.
  - Decorador `@transaction.atomic` explícito en operaciones con mutaciones o auditoría.
- **`forms`**:
  - Clase de formulario (`Form` o `ModelForm`) en `<app>/forms.py`.
  - Métodos de validación limpia: `clean_<campo>()` y `clean()`.
- **`routing_and_views`**:
  - `urls.py`: `app_name`, ruta `path('...', ...)` y nombre semántico `name='...'`.
  - Vista (FBV o CBV): Decoradores de control de acceso (`@login_required`, `@permission_required('...', raise_exception=True)`) o mixins equivalentes.
- **`templates`**:
  - Plantilla principal extendiendo `layouts/base.html` o `layouts/auth.html`.
  - Componentes UI, tokens semánticos de Tailwind CSS y manejo de mensajes flash (`messages`).

### Paso 4: Elaboración del Plan de Implementación (`implementation-plan.md`)
Desglosar el plan en tareas atómicas y secuenciales con cajas de verificación (`- [ ]`):
- **Tarea 1: Suite de Pruebas (Fase Red):**
  - Definir archivo de tests en `tests/{modulo}/test_{nombre}.py` o `<app>/tests/`.
  - Mapear cada escenario Gherkin a un test Pytest / Django TestCase.
- **Tarea 2: Modelos y Migraciones:**
  - Crear/actualizar modelos y generar migraciones (`makemigrations`).
- **Tarea 3: Capa de Servicios / Dominio:**
  - Implementar funciones o acciones de negocio protegidas con transacciones.
- **Tarea 4: Capa de Formularios y Validación:**
  - Implementar y probar validaciones en `forms.py`.
- **Tarea 5: Vistas, Rutas y Control de Acceso:**
  - Implementar vistas, registrar URLs y aplicar restricciones de permisos.
- **Tarea 6: Plantillas Django y Estilos Tailwind:**
  - Crear o adaptar templates con accesibilidad y diseño SaaS.
- **Tarea 7: Verificación de Calidad y Cierre:**
  - Ejecutar `python manage.py check`, verificar migraciones y correr suite de tests en verde.

---

## 4. Detención Obligatoria (Compuerta 1 - Human-in-the-Loop)

Al completar la redacción de los 3 artefactos (`spec.acceptance.feature`, `spec.contract.yaml`, `implementation-plan.md`), el agente **TIENE PROHIBIDO** crear archivos de prueba o código de producción. Debe detenerse y presentar al usuario el reporte de compuerta:

> **Compuerta 1 completada (Especificación & Plan):**
> - **Módulo:** `{modulo}`
> - **Escenarios Gherkin:** `[Número de escenarios]` en `spec.acceptance.feature`
> - **Contrato Técnico:** Rutas, modelos y servicios definidos en `spec.contract.yaml`
> - **Plan de Implementación:** `[Número de tareas]` en `implementation-plan.md`
> 
> 👉 **¿Apruebas la especificación y el plan para redactar los tests de la Fase Red? (Responde "Aprobado" para continuar o indica los cambios requeridos).**