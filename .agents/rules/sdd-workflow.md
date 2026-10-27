---
trigger: always_on
---

# Reglas de Orquestación SDD y Gestión de Artefactos (Django Fullstack)

Este documento define el protocolo formal mediante el cual el agente mapea las Historias de Usuario hacia artefactos de especificación, suites de prueba en Pytest/Django y código de producción en el stack **Django 5/6 + Python 3.12+ + Tailwind CSS**, incluyendo la gestión de compuertas y actualización retroactiva (Retrofit).

---

## 1. Mapa de Rutas y Artefactos SDD

### 1.1 Entradas
- **Historias de Usuario (HU):** `.agents/workflows/{modulo}/HU-{id}-{slug}.md`
- **Restricciones No Funcionales (NFR):** `.agents/rules/nfr/*.md` (Accesibilidad WCAG 2.1 AA, UI/UX SaaS, seguridad CSRF/RBAC y prevención N+1).

### 1.2 Salida de Compuerta 1 (Especificación Formal y Contratos)
- `.agents/rules/specs/modules/{modulo}/spec.acceptance.feature` (Criterios de aceptación en sintaxis Gherkin).
- `.agents/rules/specs/modules/{modulo}/spec.contract.yaml` (Contrato técnico formal: modelos Django ORM, servicios/actions, rutas `urls.py`, formularios `forms.py`, vistas y plantillas).
- `.agents/rules/specs/modules/{modulo}/implementation-plan.md` (Plan atómico de tareas con verificación paso a paso).

### 1.3 Salida de Compuerta 2 (Suite de Pruebas - Fase Red)
- `tests/{modulo}/test_{nombre}.py` o `<app>/tests/test_{nombre}.py` (Pruebas unitarias y de integración escritas con `pytest-django` o `TestCase` de Django).

### 1.4 Salida de Compuerta 3 (Implementación Vertical - Fase Green)
- **Modelos y Migraciones:** `<app>/models.py` y migraciones en `<app>/migrations/` aplicadas con `python manage.py migrate`.
- **Capa de Dominio:** Servicios y Acciones bajo `<app>/services.py` o `<app>/actions/` protegidas con `@transaction.atomic`.
- **Validación de Formularios:** `<app>/forms.py` (`Form` o `ModelForm`).
- **Enrutamiento y Vistas:** `<app>/urls.py`, `<app>/views.py` (decoradores de autenticación y permisos) y registro en `core/urls.py`.
- **Plantillas Django:** `<app>/templates/<app>/` extendiendo layouts maestros de `inventario/templates/layouts/base.html` o `authentication/templates/layouts/auth.html`.

---

## 2. Protocolo de Compuertas de Aprobación (Human-in-the-Loop)

El agente debe detener su ejecución y solicitar aprobación explícita al usuario en cada compuerta antes de avanzar:

1. **Compuerta 1 (Spec & Plan):**
   - El agente genera la spec Gherkin, el contrato técnico y el implementation plan.
   - **DETENCIÓN OBLIGATORIA:** Espera aprobación ("Aprobado") antes de escribir cualquier prueba.
2. **Compuerta 2 (Tests en Fase Red):**
   - El agente escribe las pruebas cubriendo los escenarios Gherkin y NFRs.
   - Ejecuta `pytest` o `python manage.py test` para confirmar el fallo controlado por ausencia de código.
   - **DETENCIÓN OBLIGATORIA:** Presenta el reporte de fallo esperado y espera aprobación antes de tocar código de producción.
3. **Compuerta 3 (Implementación y Cierre en Verde):**
   - El agente implementa modelos, servicios, formularios, vistas y templates hasta lograr 100% de tests en verde.
   - Ejecuta verificación de calidad (`python manage.py check`, `python manage.py makemigrations --check --dry-run`).

---

## 3. Protocolo de Evolución y Retrofit (Actualización de HUs Implementadas)

Cuando se introduzca un cambio transversal de arquitectura (por ejemplo: Grupos, Permisos y RBAC en `authentication`) que afecte a módulos o Historias de Usuario ya implementadas (por ejemplo: `inventario` o `catalog`):

1. **Secuencia de Ejecución:**
   - Primero se completa el ciclo SDD completo (Compuertas 1, 2 y 3) para el módulo base (`authentication`).
2. **Re-apertura Controlada (Modo Retrofit):**
   - Se agregan los nuevos criterios de aceptación (validación de grupos/permisos `has_perm`, bloqueo con `Http403` / `PermissionDenied` o redirección de login) en el archivo `HU-{id}-{slug}.md` correspondiente.
   - Al ejecutar el ciclo sobre la HU existente:
     - **En Compuerta 1:** El agente actualiza `spec.acceptance.feature`, `spec.contract.yaml` e `implementation-plan.md` preservando los escenarios funcionales previos válidos.
     - **En Compuerta 2 (Excepción a Inmutabilidad):** Se autoriza la actualización de los fixtures (`conftest.py`) o métodos `setUp()` de las pruebas existentes (inyectando usuarios autenticados, grupos y permisos requeridos) y se añaden las nuevas pruebas de autorización.
     - **En Compuerta 3:** El agente actualiza vistas (decoradores `@login_required`, `@permission_required` o `PermissionRequiredMixin`) y plantillas (`{% if perms.app.action %}`) hasta que toda la suite vuelva a Fase Green.