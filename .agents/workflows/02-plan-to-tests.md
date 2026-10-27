---
description: Workflow 02 - Plan de Implementación a Suite de Pruebas (Fase Red) para Django
---

# Workflow 02: Plan a Pruebas (Plan to Tests) - Django

Este workflow toma las especificaciones y el contrato técnico formalmente aprobados en la **Compuerta 1** y los traduce en una suite integral de pruebas automatizadas con **Pytest-Django** (o `TestCase` de Django), estableciendo una **Fase Roja controlada y verificable** antes de crear cualquier código de producción.

---

## 1. Documentación Mandatoria a Consultar

Antes de redactar cualquier test, el agente **DEBE** consultar y cumplir:
1. [.agents/rules/django-fullstack.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/django-fullstack.md): Sección 4 (*Estándar de Testing Pytest-Django / Django TestCase*) y Sección 1.1 (*Inmutabilidad de Pruebas*).
2. [.agents/rules/sdd-workflow.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/sdd-workflow.md): Sección 2 (*Compuerta 2: Pruebas y Validación Fase Red*).
3. [.agents/rules/specs/auth.md](file:///Users/joseoviedo/Django%20projects/tienda-sdd/.agents/rules/specs/auth.md): Matriz de grupos (`Group`), permisos (`Permission`) y respuestas esperadas (`403 Forbidden`).
4. Artefactos aprobados en la Compuerta 1 bajo `.agents/rules/specs/modules/{modulo}/`:
   - `spec.acceptance.feature` (Escenarios Gherkin).
   - `spec.contract.yaml` (Contratos técnicos de modelos, servicios, rutas y vistas).
   - `implementation-plan.md` (Checklist de tareas).

---

## 2. Entradas y Salidas

### Entradas
- `.agents/rules/specs/modules/{modulo}/spec.acceptance.feature`
- `.agents/rules/specs/modules/{modulo}/spec.contract.yaml`
- `.agents/rules/specs/modules/{modulo}/implementation-plan.md`

### Salidas
Archivos de prueba creados o actualizados bajo `tests/{modulo}/` o `<app>/tests/`:
1. **`test_services.py`**: Pruebas unitarias para la capa de dominio (servicios y acciones atómicas).
2. **`test_views.py`**: Pruebas de integración para rutas HTTP, respuestas, validaciones de formularios y renderizado.
3. **`test_security.py`** (o integrado en `test_views.py`): Pruebas de autorización RBAC (autenticación obligatoria y comprobación de permisos `has_perm`).
4. **Reporte de Fase Roja:** Salida de terminal con fallos esperados por ausencia de implementación.

---

## 3. Protocolo de Redacción de Pruebas

### 3.1 Cobertura de Escenarios Gherkin (Mapeo 1 a 1)
Cada escenario de `spec.acceptance.feature` debe contar con al menos una función de prueba descriptiva en la suite:
- Nombres de tests explícitos en minúsculas y con prefijo `test_` en español o inglés técnico coherente: `test_crear_categoria_exitosamente_con_usuario_administrador()`.
- Estructura AAA estricta (Arrange, Act, Assert).

### 3.2 Inclusión Obligatoria de Aserciones de NFR (Al menos 2)
Toda suite de pruebas debe incorporar de manera obligatoria al menos **2 aserciones de Requerimientos No Funcionales**:
1. **Seguridad / RBAC:**
   - Usuario anónimo recibe redirección `302 Found` al login (`/auth/login/?next=...`).
   - Usuario autenticado sin el permiso requerido recibe respuesta HTTP `403 Forbidden`.
2. **Accesibilidad WCAG / Integridad:**
   - Comprobar que en respuestas con error de validación el HTML contenga atributos de accesibilidad (`role="alert"` o `aria-invalid="true"`).
   - Comprobar la atomicidad de la base de datos (rollback ante excepciones).

### 3.3 Fixtures y Convenciones con Pytest-Django
- Marcar los tests con `@pytest.mark.django_db`.
- Crear o utilizar fixtures de usuario con roles asignados:
  ```python
  import pytest
  from django.contrib.auth.models import User, Group

  @pytest.fixture
  def usuario_vendedor(db):
      user = User.objects.create_user(username='vendedor1', password='password123')
      grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')
      user.groups.add(grupo_vendedor)
      return user
  ```
- Para pruebas de vistas, utilizar el cliente de Django autenticado: `client.force_login(usuario)`.
- Emplear siempre `reverse('app_name:nombre_ruta')` para validar el enrutamiento desacoplado.

---

## 4. Ejecución y Validación de la Fase Roja

Una vez redactada la suite de pruebas:
1. **Ejecutar la suite en la terminal:**
   ```bash
   pytest tests/{modulo}/ -v
   # o alternativamente:
   python manage.py test tests.{modulo}
   ```
2. **Verificar la naturaleza del fallo (Fase Roja Controlada):**
   - Los tests **DEBEN FALLAR** únicamente por ausencia de la implementación productiva (ej. `ImportError: cannot import name 'CrearCategoriaService'`, `NoReverseMatch`, `AssertionError: 404 != 200`, etc.).
   - **PROHIBIDO:** No se aceptan fallos causados por errores sintácticos en el propio archivo de test (ej. `SyntaxError`, `IndentationError` o aserciones mal construidas).

---

## 5. Detención Obligatoria (Compuerta 2 - Human-in-the-Loop)

Una vez confirmada la Fase Roja en la terminal, el agente **TIENE PROHIBIDO** crear modelos, migraciones, formularios, vistas o servicios de producción. Debe detenerse inmediatamente y presentar el reporte de compuerta:

> **Compuerta 2 completada (Fase Red):**
> - **Módulo:** `{modulo}`
> - **Archivos de prueba creados:** `tests/{modulo}/test_*.py`
> - **Pruebas ejecutadas:** `[X fallidas esperadas / 0 errores de sintaxis]`
> - **Causas del fallo controlado:** `[Servicio inexistente / Ruta pendiente / Código HTTP no coincide por falta de vista]`
> - **Aserciones NFR validadas:** `[Control de acceso 403 Forbidden y atributos accesibles de formulario]`
> 
> 👉 **¿Apruebas la suite de pruebas para proceder con la implementación vertical (Fase Green)? (Responde "Aprobado" para continuar).**
