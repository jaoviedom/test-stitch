---
trigger: always_on
---

# Django Fullstack & SDD Agent Guidelines

Este documento define los estándares arquitectónicos, convenciones de código y el protocolo operativo que el agente debe cumplir estrictamente en este proyecto (**Django 5/6 + Python 3.12+ + Django Templates / Tailwind CSS + Pytest-Django**).

---

## 1. Principios Operativos y Protocolo SDD Agéntico

### 1.1 Filosofía Base

- **Spec First, Code Later:** Ningún archivo productivo (`<app>/`, `templates/`, `static/`, `core/`) se crea o modifica sin una especificación formal aprobada en `.agents/rules/specs/` (Gherkin/Contratos).
- **TDD Estricto:** La fase roja es mandatoria. Primero se redactan los tests en Pytest / Django TestCase reflejando los criterios de aceptación; luego se ejecutan para confirmar el fallo, y finalmente se implementa el código mínimo necesario.
- **Inmutabilidad de Pruebas:** Una vez aprobada la suite de pruebas contra la especificación, el agente **tiene prohibido modificar las aserciones de los tests** para forzar un pase. El código de producción es el que debe corregirse.
- **Atomicidad y Verificabilidad:** Cada paso del `implementation-plan.md` debe verificarse en la terminal antes de continuar con la siguiente tarea.

### 1.2 Ciclo de Ejecución Agéntico (Paso a Paso Obligatorio)

Cada vez que se solicite desarrollar o modificar una funcionalidad, el agente debe ejecutar secuencialmente estas 4 fases:
1. **Fase 1 - Contrato Técnico & UI:** Si el archivo en `specs/` solo contiene la Historia de Usuario y los escenarios Gherkin, el agente debe proponer y completar primero la sección **"Contrato Técnico & UI"** dentro de la spec (modelos, servicios/actions, rutas `urls.py`, formularios, vistas, componentes UI y reglas de `.agents/rules/nfr/`) antes de tocar código.
2. **Fase 2 - Spec-to-Test (Fase Roja):** Crear o actualizar el archivo de pruebas en `tests/` o `<app>/tests/` cubriendo todos los escenarios Gherkin y al menos **2 aserciones de NFR** (ej. atributos HTML de accesibilidad `role="alert"`, autorización RBAC/permisos de Django y prevención de consultas N+1 o transacciones atómicas). Ejecutar `pytest` o `python manage.py test` para confirmar que falla.
3. **Fase 3 - Implementación Vertical (Fase Verde):** Escribir Migraciones (`python manage.py makemigrations`), Modelos, Servicios/Actions (`<app>/services.py` o `<app>/actions/`), Forms (`<app>/forms.py`), Vistas y Plantillas Django reutilizando los layouts maestros de `templates/layouts/`.
4. **Fase 4 - Auto-Verificación y Cierre:** Ejecutar las herramientas de control de calidad en la terminal integrada (Sección 5) en bucle cerrado hasta obtener 0 errores.

---

## 2. Convenciones de Backend (Django & Python)

### Tipado y Estilo
- Python 3.11/3.12+ con anotaciones de tipo completas en parámetros, funciones y retornos (`def execute(...) -> Product:`).
- Seguir las directrices de PEP 8 y buenas prácticas de la comunidad Django.
- Sin lógica de negocio pesada en Vistas (`views.py`); delegar inmediatamente a clases o funciones de Servicio/Acción en `<app>/services.py` o `<app>/actions/`.

### Arquitectura de Capas
- **Routing:** Rutas modularizadas en cada app (`<app>/urls.py`) con `app_name = '<app>'` y nombres explícitos y consistentes (`path('...', view, name='nombre_ruta')`).
- **Forms / Validation:** Toda validación de entrada ocurre en clases dedicadas (`forms.py` o Form Requests/Serializers) usando validaciones limpias:
  ```python
  from django import forms

  class UpdateStockForm(forms.Form):
      stock = forms.IntegerField(min_value=0, required=True)
      reason = forms.CharField(max_length=255, min_length=3, required=True)

      def clean_stock(self) -> int:
          stock = self.cleaned_data['stock']
          return stock
  ```

- **Services / Actions (Capa de Dominio):** Funciones o clases con una única responsabilidad bajo `<app>/services.py` o `<app>/actions/`. Toda operación con efectos colaterales o auditoría debe ejecutarse bajo `@transaction.atomic`:

```python
from django.db import transaction
from django.contrib.auth.models import User
from inventario.models import Product, InventoryLog

class UpdateProductStockAction:
    @staticmethod
    @transaction.atomic
    def execute(product: Product, new_stock: int, reason: str, user: User) -> Product:
        product.stock = new_stock
        if new_stock == 0:
            product.status = 'out_of_stock'
        product.save(update_fields=['stock', 'status'])

        InventoryLog.objects.create(
            product=product,
            new_stock=new_stock,
            reason=reason,
            adjusted_by=user,
        )
        return product
```

#### Modelos de Django ORM:
- Definir siempre `__str__()` descriptivo y legible.
- Especificar `on_delete` explícito en claves foráneas (`CASCADE`, `PROTECT`, `SET_NULL`).
- Definir `related_name` semántico en relaciones ManyToOne y ManyToMany.
- Utilizar `choices` o `models.TextChoices` para estados o tipos finitos.
- Prohibidas consultas N+1 en bucles: forzar `select_related(...)` para ForeignKey/OneToOne y `prefetch_related(...)` para ManyToMany/Reverse relations.

---

## 3. Convenciones de Frontend (Django Templates + Tailwind CSS)

### Cumplimiento Mandatorio de UI/UX
Toda interfaz gráfica y plantilla debe cumplir con el sistema de diseño moderno para retail / POS SaaS:
- **Layouts Maestros:**
  - Aplicación principal (Dashboard, Inventario, Ventas, Reportes): heredar de `templates/layouts/base.html` o `inventario/templates/layouts/base.html`.
  - Autenticación (Login, Registro, Recuperación de contraseña): heredar de `authentication/templates/layouts/auth.html` (centrado, sin sidebar ni topbar).
- **Patrón Sidebar:** Sidebar retráctil moderno con soporte off-canvas móvil mediante drawer y overlay desenfocado (`backdrop-blur`).
- **Paleta Semántica:**
  - Primarios / Acción positiva: `brand` / `indigo` / `emerald`.
  - Alertas y advertencias: `amber`.
  - Mermas / Destructivo / Peligro: `rose`.
  - Estructura y fondos: `slate` / `zinc`.
- **Tipografía Numérica:** Uso obligatorio de `font-mono tabular-nums` en precios, códigos SKU/EAN y totales monetarios.
- **Seguridad en Formularios:** Todo formulario con método POST debe incluir obligatoriamente el token `{% csrf_token %}`.
- **Mensajería:** Renderizar siempre el framework de alertas de Django (`{% if messages %} ... {% endif %}`) con los colores semánticos correspondientes (`success`, `error`, `warning`, `info`).

### Accesibilidad (WCAG 2.1 AA)
- Todos los inputs asociados a un `<label for="...">`.
- Manejo accesible de errores: `<p role="alert" class="text-rose-600 text-xs mt-1" aria-live="polite">{{ form.campo.errors.0 }}</p>`.
- Atributo `aria-invalid="true"` en campos con error de validación.

---

## 4. Estándar de Testing (Pytest-Django / Django TestCase)
- **Ubicación:** `tests/` en la raíz o `<app>/tests/`.
- Uso de fixtures o decorador `@pytest.mark.django_db` para pruebas que interactúan con la base de datos.
- Estructura AAA (Arrange, Act, Assert):

```python
import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Group
from inventario.models import Product, InventoryLog

@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(username='admin', email='admin@tienda.com', password='password123')
    admin_group, _ = Group.objects.get_or_create(name='admin')
    user.groups.add(admin_group)
    return user

@pytest.mark.django_db
def test_updates_product_stock_and_creates_inventory_audit_record(client, admin_user):
    product = Product.objects.create(name='Laptop Pro', stock=10, status='in_stock')

    client.force_login(admin_user)
    response = client.post(
        reverse('inventario:actualizar_stock', kwargs={'pk': product.pk}),
        data={'stock': 0, 'reason': 'Venta en tienda'}
    )

    assert response.status_code in [200, 302]
    product.refresh_from_db()
    assert product.stock == 0
    assert product.status == 'out_of_stock'

    audit_exists = InventoryLog.objects.filter(
        product=product,
        new_stock=0,
        adjusted_by=admin_user,
    ).exists()
    assert audit_exists is True
```

---

## 5. Control de Calidad y Cierre de Tarea
Antes de dar por terminada una tarea en el checklist, el agente debe ejecutar y aprobar en la terminal integrada:
1. Verificación de Django: `python manage.py check`
2. Migraciones aplicadas: `python manage.py makemigrations --check --dry-run`
3. Suite de pruebas: `pytest` o `python manage.py test`
4. Formato y linting (si están configurados): `ruff check` / `flake8` y `black --check .` / `ruff format --check`

---

## 6. Prohibiciones Explícitas para el Agente
1. NO inventar rutas, modelos ni campos de base de datos que no estén respaldados por la especificación (`spec.contract.yaml` o `spec.acceptance.feature`).
2. NO omitir `@transaction.atomic` en mutaciones que involucren más de un modelo o registros de auditoría.
3. NO permitir consultas N+1 en vistas o endpoints; usar siempre `select_related` y `prefetch_related`.
4. NO dar por buena una tarea si hay tests en rojo, errores en `manage.py check` o migraciones pendientes.