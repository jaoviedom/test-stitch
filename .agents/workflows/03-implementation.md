---
description: Workflow 03 - Implementación, Green y Cierre de Tarea para Django Fullstack
---

# Workflow 03: Implementación (Fase Green) y Cierre de Calidad - Django

Este workflow guía la **implementación vertical** en código de producción para transformar la suite de pruebas de la Fase Roja (Compuerta 2) en **Fase Verde (100% aprobada)**, asegurando la calidad estática, la integridad arquitectónica y el cumplimiento estricto de las especificaciones aprobadas.

---

## 1. Principios Mandatorios de Implementación

1. **Inmutabilidad de Pruebas:**
   - **ESTÁ ESTRICTAMENTE PROHIBIDO modificar o relajar las aserciones de los tests** para forzar un pase. El código de producción es el único que debe ajustarse y corregirse.
2. **Código Mínimo Necesario:**
   - No crear rutas, modelos, campos ni funciones que no estén estrictamente respaldados por el contrato técnico (`spec.contract.yaml`) y requeridos por las pruebas.
3. **Atomicidad de Base de Datos:**
   - Toda mutación que involucre múltiples modelos o registros de auditoría debe ejecutarse bajo `@transaction.atomic`.
4. **Prevención de Consultas N+1:**
   - Prohibido iterar sobre relaciones foráneas o muchos a muchos sin `select_related()` o `prefetch_related()`.

---

## 2. Documentación Mandatoria a Consultar

Antes y durante la implementación, el agente debe contrastar:
1. [.agents/rules/django-fullstack.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/django-fullstack.md): Convenciones de tipado, ORM, servicios, formularios, vistas y Tailwind CSS.
2. [.agents/rules/sdd-workflow.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/sdd-workflow.md): Ciclo de cierre y calidad.
3. [.agents/rules/specs/auth.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/specs/auth.md): Catálogo de permisos oficiales `<app_label>.<codename>` y control de accesos.
4. [.agents/rules/nfr/01-ui-ux-system.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/nfr/01-ui-ux-system.md): Layouts maestros, tokens semánticos, `font-mono tabular-nums` y accesibilidad WCAG 2.1 AA.
5. Artefactos aprobados bajo `.agents/rules/specs/modules/{modulo}/`:
   - `spec.contract.yaml` (Contrato técnico formal).
   - `implementation-plan.md` (Checklist de tareas).

---

## 3. Protocolo de Implementación Vertical (Paso a Paso)

El agente debe ejecutar de forma secuencial y atómica los siguientes pasos:

### Paso 1: Persistencia (Modelos y Migraciones)
- Crear o actualizar modelos en `<app>/models.py` respetando los campos, tipos y constraints definidos en `spec.contract.yaml`.
- Definir `__str__()` descriptivo, `on_delete` explícito en claves foráneas y `related_name` semántico.
- Generar y aplicar migraciones:
  ```bash
  python manage.py makemigrations <app>
  python manage.py migrate
  ```

### Paso 2: Capa de Dominio (Servicios / Actions)
- Implementar la lógica de negocio en `<app>/services.py` o `<app>/actions/`.
- Aplicar tipado estricto en parámetros y retorno:
  ```python
  from django.db import transaction
  from django.contrib.auth.models import User
  from inventario.models import Categoria

  class CrearCategoriaService:
      @staticmethod
      @transaction.atomic
      def execute(nombre: str, descripcion: str, creado_por: User) -> Categoria:
          categoria = Categoria.objects.create(
              nombre=nombre,
              descripcion=descripcion,
          )
          return categoria
  ```

### Paso 3: Validación de Entrada (Formularios)
- Crear o actualizar clases de formulario en `<app>/forms.py` (`Form` o `ModelForm`).
- Implementar validaciones limpias en `clean_<campo>()` y `clean()`:
  ```python
  from django import forms
  from inventario.models import Categoria

  class CategoriaForm(forms.ModelForm):
      class Meta:
          model = Categoria
          fields = ['nombre', 'descripcion']

      def clean_nombre(self) -> str:
          nombre = self.cleaned_data['nombre'].strip()
          if Categoria.objects.filter(nombre__iexact=nombre).exists():
              raise forms.ValidationError("Ya existe una categoría con este nombre.")
          return nombre
  ```

### Paso 4: Enrutamiento y Vistas
- Registrar URLs modularizadas en `<app>/urls.py` con `app_name = '<app>'` y verificar su inclusión en `core/urls.py`.
- Implementar vistas en `<app>/views.py` protegiendo el acceso:
  ```python
  from django.contrib.auth.decorators import login_required, permission_required
  from django.shortcuts import render, redirect

  @login_required
  @permission_required('inventario.add_categoria', raise_exception=True)
  def crear_categoria(request):
      # Lógica de vista delegando en formulario y servicio
      ...
  ```
- Optimizar consultas con `select_related(...)` y `prefetch_related(...)` para evitar N+1.

### Paso 5: Plantillas Django y Cumplimiento de UI/UX
- Crear plantillas en `<app>/templates/<app>/` heredando de los layouts maestros:
  - Aplicación principal: `{% extends "layouts/base.html" %}`.
  - Autenticación: `{% extends "layouts/auth.html" %}`.
- Cumplimiento de NFRs:
  - Formulario con token de seguridad: `{% csrf_token %}`.
  - Accesibilidad de errores: `<p role="alert" class="text-rose-600 text-xs mt-1" aria-live="polite">{{ form.campo.errors.0 }}</p>`.
  - Atributo `aria-invalid="true"` en campos con error.
  - Renderizado del framework de mensajes de Django (`messages`).

---

## 4. Bucle TDD: Iteración hasta Fase Verde

1. Ejecutar la suite de pruebas del módulo en terminal:
   ```bash
   pytest tests/{modulo}/ -v
   # o alternativamente:
   python manage.py test tests.{modulo}
   ```
2. Analizar fallos residuales y refactorizar **únicamente el código de producción**.
3. Repetir hasta obtener **100% de tests aprobados (Fase Green)** sin excepciones ni omisiones.

---

## 5. Control de Calidad y Cierre de Tarea

Antes de dar por completado el workflow, el agente debe ejecutar en la terminal integrada:
1. **Integridad de Django:**
   ```bash
   python manage.py check
   ```
2. **Verificación de migraciones pendientes:**
   ```bash
   python manage.py makemigrations --check --dry-run
   ```
3. **Ejecución total de la suite de pruebas:**
   ```bash
   pytest
   ```
4. **Formato y Linting (si están configurados):**
   ```bash
   ruff check .
   ruff format --check .
   ```

---

## 6. Informe Final de Cierre (Compuerta 3)

Una vez aprobadas todas las verificaciones, presentar al usuario el resumen de entrega:

> **Ciclo SDD Completado con Éxito (Fase Green):**
> - **Módulo:** `{modulo}`
> - **Pruebas en verde:** `[X pasadas / 0 fallidas]`
> - **Django Check & Migraciones:** `[0 errores / 0 migraciones pendientes]`
> - **Archivos creados/modificados:**
>   - Modelos: `<app>/models.py`
>   - Servicios: `<app>/services.py`
>   - Formularios: `<app>/forms.py`
>   - Vistas y Rutas: `<app>/views.py`, `<app>/urls.py`
>   - Plantillas: `<app>/templates/<app>/...`
> - **Sugerencia de Commit:** `feat({modulo}): implement {funcionalidad} (US-{id})`
