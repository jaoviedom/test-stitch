---
trigger: always_on
---

# Módulo: Autenticación, Roles y Permisos (Auth & RBAC de Django)

Este documento especifica la arquitectura formal de control de accesos basada en roles (RBAC) para el proyecto utilizando el subsistema nativo `django.contrib.auth`.

---

## 1. Arquitectura de Datos (Django ORM)

- **Mecanismo base:** Subsistema nativo `django.contrib.auth`.
- **Modelos Principales:**
  - `User` (`django.contrib.auth.models.User`): Representa las cuentas de usuario registradas.
  - `Group` (`django.contrib.auth.models.Group`): Abstracción estándar de Django para modelar los **Roles** del sistema (`usuario`, `vendedor`, `administrador`).
  - `Permission` (`django.contrib.auth.models.Permission`): Permisos granulares asociados a cada modelo mediante `ContentType` o permisos personalizados (`custom permissions`).
- **Múltiples Roles y Permisos Directos:**
  - Un usuario puede pertenecer a **múltiples grupos/roles** simultáneamente a través de la relación Many-to-Many nativa: `user.groups.add(group)` o `user.groups.set([group1, group2])`.
  - Un usuario puede recibir **permisos directos adicionales** independientes de sus grupos mediante `user.user_permissions.add(permission)`.
  - Al evaluar `user.has_perm('app_label.codename')`, Django combina automáticamente los permisos heredados de todos sus grupos más sus permisos directos.

---

## 2. Catálogo Oficial de Grupos y Permisos

### 2.1 Mecanismo de Inicialización
Los roles y permisos se inicializan mediante un comando de gestión de Django (`python manage.py setup_roles` o `python manage.py init_roles`) o una migración de datos (`Data Migration`) en la app `authentication`.

### 2.2 Grupos / Roles Oficiales
1. **`usuario`**:
   - Rol base asignado automáticamente a todo usuario al registrarse (HU-001).
   - Acceso restringido exclusivamente a su panel básico (`/dashboard`) y a la gestión de su perfil propio (`/perfil/`).
   - Sin acceso a catálogo, ventas (POS), reportes ni administración.
2. **`vendedor`**:
   - Operador comercial del punto de venta.
   - Permite consultar catálogo y operar el módulo de ventas (POS).
3. **`administrador`**:
   - Control total del sistema, configuración y gestión de usuarios, roles y permisos (HU-002).

### 2.3 Permisos Oficiales por Módulo (Convención Django: `<app_label>.<codename>`)

- **Autenticación y Usuarios (`authentication` / `auth`):**
  - `auth.view_user`: Consultar listado y detalles de usuarios.
  - `authentication.manage_access`: Asignar o revocar grupos y permisos a otros usuarios (HU-002).
- **Catálogo / Inventario (`inventario` / `catalog`):**
  - `inventario.view_categoria`: Consultar y listar categorías (Requerido para `catalog/HU-003`).
  - `inventario.add_categoria`: Registrar una nueva categoría (Requerido para `catalog/HU-001`).
  - `inventario.change_categoria`: Editar categorías existentes (Requerido para `catalog/HU-002`).
  - `inventario.view_producto`: Consultar y listar productos.
  - `inventario.add_producto`: Crear nuevos productos.
  - `inventario.change_producto`: Modificar productos y actualizar stock.
- **Ventas / POS (`inventario` o `ventas`):**
  - `inventario.access_pos`: Acceso a la interfaz de terminal de punto de venta (POS).
- **Reportes:**
  - `inventario.view_reports`: Visualización de balances y métricas analíticas.

### 2.4 Matriz de Asignación Inicial por Rol / Grupo

| Grupo (Rol) | Permisos Asignados | Alcance Operativo |
| :--- | :--- | :--- |
| **`usuario`** | *Ninguno (`[]`)* | Panel básico (`/dashboard`) y edición de su propio perfil (`/perfil/`). Todo intento de entrar a `/catalog` responde **403 Forbidden**. |
| **`vendedor`** | `inventario.view_categoria`, `inventario.view_producto`, `inventario.access_pos` | Consulta de inventario y realización de cobros/ventas en tienda. |
| **`administrador`** | Todos los permisos anteriores + `authentication.manage_access` + `inventario.add_categoria` + `inventario.change_categoria` + `inventario.view_reports` | Control total, auditoría, asignación de roles y mantenimiento de catálogo. |

---

## 3. Protocolo de Verificación y Uso en el Código

### 3.1 En Vistas de Backend (Django Views)
- **Vistas basadas en funciones (FBV):**
  ```python
  from django.contrib.auth.decorators import login_required, permission_required
  from django.core.exceptions import PermissionDenied

  @login_required
  @permission_required('inventario.view_categoria', raise_exception=True)
  def lista_categorias(request):
      ...
  ```
- **Vistas basadas en clases (CBV):**
  ```python
  from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
  from django.views.generic import ListView

  class CategoriaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
      permission_required = 'inventario.view_categoria'
      raise_exception = True  # Retorna HTTP 403 Forbidden en lugar de redirigir a login
  ```
- **Comprobación manual de grupos o permisos en servicios:**
  ```python
  if not request.user.has_perm('authentication.manage_access'):
      raise PermissionDenied("No tiene permisos para modificar los accesos de este usuario.")
  ```

### 3.2 En Plantillas de Frontend (Django Templates)
Utilizar la variable de contexto `perms` inyectada por el context processor `django.contrib.auth.context_processors.auth`:
```django
{% if perms.inventario.add_categoria %}
<a href="{% url 'inventario:crear_categoria' %}" class="btn-primary">
    Nueva Categoría
</a>
{% endif %}

{% if perms.authentication.manage_access %}
<button type="button" onclick="abrirModalAccesos({{ usuario.id }})">
    Gestionar Roles
</button>
{% endif %}
```

### 3.3 En Pruebas Automatizadas (Pytest-Django / Django TestCase)
- Utilizar fixtures para inyectar usuarios con grupos y permisos:
```python
import pytest
from django.contrib.auth.models import User, Group, Permission
from django.urls import reverse

@pytest.fixture
def usuario_base(db):
    user = User.objects.create_user(username='juan', password='password123')
    grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
    user.groups.add(grupo_usuario)
    return user

@pytest.mark.django_db
def test_usuario_recien_registrado_recibe_403_al_intentar_crear_categoria(client, usuario_base):
    client.force_login(usuario_base)
    response = client.get(reverse('inventario:crear_categoria'))
    assert response.status_code == 403
```
