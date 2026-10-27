---
description: Este workflow coordina la ejecución secuencial de los workflows 01, 02 y 03, requiriendo validación humana obligatoria antes de avanzar entre fases.
---

# Master Workflow: Spec-Driven Development Orquestado (Human-in-the-Loop) - Django

Este workflow coordina la ejecución secuencial de los workflows requiriendo validación humana obligatoria antes de avanzar entre fases en proyectos Django.

---

## Parámetros de Entrada
- **Módulo:** `.agents/rules/specs/modules/{modulo}/`
- **Historia:** `HU-{id}-{slug}.md`

---

## Protocolo de Orquestación

### COMPUERTA 1: Formalización de Especificaciones
1. Ejecuta internamente el workflow `.agents/workflows/01-spec-to-plan.md`.
2. Una vez creados los archivos (`spec.acceptance.feature`, `spec.contract.yaml`, `implementation-plan.md`), **DETÉN LA EJECUCIÓN**.
3. Muestra al desarrollador el siguiente bloque de aprobación:

   > **Compuerta 1 completada:**
   > - Escenarios Gherkin generados: `[Número de escenarios]`
   > - Contratos/Endpoints definidos: `[Listado de rutas urls.py, vistas y servicios]`
   > - Plan de tareas desglosado: `.agents/rules/specs/modules/{modulo}/implementation-plan.md`
   > 
   > 👉 **¿Apruebas la especificación y el plan para redactar los tests? (Responde "Aprobado" para continuar o indica los cambios requeridos).**

4. **Regla de espera:** NO generes pruebas ni modifiques código de producción hasta que el usuario responda explícitamente con su aprobación.

---

### COMPUERTA 2: Pruebas y Validación Fase Red
*(Se dispara únicamente tras recibir la aprobación de la Compuerta 1)*

1. Ejecuta internamente el workflow `.agents/workflows/02-plan-to-tests.md`.
2. Crea los tests con Pytest o Django TestCase y ejecuta `pytest` o `python manage.py test` en la terminal.
3. Verifica que fallen por ausencia de código (fase roja controlada).
4. **DETÉN LA EJECUCIÓN** y presenta el reporte de compuerta:

   > **Compuerta 2 completada (Fase Red):**
   > - Archivo de pruebas: `tests/{modulo}/test_{nombre}.py` o `<app>/tests/test_{nombre}.py`
   > - Pruebas ejecutadas: `[X fallidas esperadas]`
   > - Causa del fallo: `[Ruta inexistente / Servicio no encontrado / Modelo pendiente / etc.]`
   > 
   > 👉 **¿Apruebas la suite de pruebas para proceder con la implementación en código de producción? (Responde "Aprobado" para continuar).**

5. **Regla de espera:** NO crees modelos, migraciones, vistas ni formularios de producción hasta recibir la aprobación.

---

### COMPUERTA 3: Implementación, Green y Cierre
*(Se dispara únicamente tras recibir la aprobación de la Compuerta 2)*

1. Ejecuta internamente el workflow `.agents/workflows/03-implementation.md`.
2. Implementa base de datos (migraciones), servicios/acciones, formularios, vistas y plantillas Django hasta que todos los tests estén en verde.
3. Ejecuta formateo y verificación de calidad (`python manage.py check`, `python manage.py makemigrations --check --dry-run`).
4. Presenta el informe final de cierre:

   > **Ciclo SDD Completado con Éxito (Fase Green):**
   > - Pruebas en verde: `[X pruebas pasadas / 0 fallos]`
   > - Django Check & Migraciones: `[Sin errores / al día]`
   > - Archivos modificados/creados: `[Lista resumida]`
   > - Sugerencia de commit: `feat({modulo}): implement {titulo} (US-{id})`