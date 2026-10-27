import io
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from inventario.models import Categoria


class ProductRegistrationUnitAndServiceTests(TestCase):
    """
    Pruebas unitarias para la capa de dominio, modelo Producto y servicio CrearProductoService (HU-004)
    """

    def setUp(self):
        # Categoría base para asignación obligatoria en pruebas
        self.categoria_bebidas = Categoria.objects.create(
            nombre="Bebidas",
            descripcion="Bebidas frías y gaseosas",
            activo=True,
        )
        self.categoria_abarrotes = Categoria.objects.create(
            nombre="Abarrotes",
            descripcion="Granos y víveres",
            activo=True,
        )

    def test_servicio_crear_producto_con_todos_los_campos_e_imagen(self):
        """
        Escenario: Creación exitosa de producto con todos los campos obligatorios, opcionales e imagen
        """
        from inventario.models import Producto
        from inventario.services import CrearProductoService

        imagen_dummy = SimpleUploadedFile(
            name="cocacola.jpg",
            content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
            content_type="image/jpeg",
        )

        producto = CrearProductoService.execute(
            nombre="Coca Cola 1.5L",
            categoria=self.categoria_bebidas,
            precio_compra=Decimal("3500.00"),
            precio_venta=Decimal("4500.00"),
            stock_actual=24,
            stock_minimo=6,
            descripcion="Gaseosa sabor cola original botella pet no retornable",
            activo=True,
            imagen=imagen_dummy,
        )

        self.assertIsNotNone(producto.pk)
        self.assertEqual(producto.nombre, "Coca Cola 1.5L")
        self.assertEqual(producto.slug, "coca-cola-15l")
        self.assertEqual(producto.categoria, self.categoria_bebidas)
        self.assertEqual(producto.precio_compra, Decimal("3500.00"))
        self.assertEqual(producto.precio_venta, Decimal("4500.00"))
        self.assertEqual(producto.stock_actual, 24)
        self.assertEqual(producto.stock_minimo, 6)
        self.assertTrue(producto.activo)
        self.assertTrue(producto.en_stock)
        self.assertTrue(bool(producto.imagen))

        # Verificar persistencia en base de datos
        db_producto = Producto.objects.get(pk=producto.pk)
        self.assertEqual(db_producto.nombre, "Coca Cola 1.5L")
        self.assertEqual(db_producto.slug, "coca-cola-15l")
        self.assertEqual(db_producto.categoria, self.categoria_bebidas)

    def test_servicio_crear_producto_sin_imagen_resuelve_imagen_generica(self):
        """
        Escenario: Creación de producto sin imagen resuelve a enlace genérico por defecto
        """
        from inventario.models import Producto
        from inventario.services import CrearProductoService

        producto = CrearProductoService.execute(
            nombre="Arroz Diana 1kg",
            categoria=self.categoria_abarrotes,
            precio_compra=Decimal("4200.00"),
            precio_venta=Decimal("5000.00"),
            stock_actual=50,
            stock_minimo=10,
        )

        self.assertIsNotNone(producto.pk)
        self.assertEqual(producto.nombre, "Arroz Diana 1kg")
        self.assertEqual(producto.slug, "arroz-diana-1kg")
        self.assertFalse(bool(producto.imagen))
        # Verifica la propiedad imagen_url con fallback
        self.assertIn("default-product", producto.imagen_url)

    def test_servicio_crear_producto_sin_descripcion_opcional(self):
        """
        Escenario: Creación de producto dejando el campo de descripción vacío
        """
        from inventario.services import CrearProductoService

        producto = CrearProductoService.execute(
            nombre="Azúcar Manuelita 1kg",
            categoria=self.categoria_abarrotes,
            precio_compra=Decimal("3800.00"),
            precio_venta=Decimal("4600.00"),
            stock_actual=15,
            stock_minimo=5,
        )

        self.assertIsNotNone(producto.pk)
        self.assertEqual(producto.descripcion, "")
        self.assertEqual(producto.slug, "azucar-manuelita-1kg")

    def test_servicio_slug_normalizado_con_caracteres_especiales(self):
        """
        Escenario: Normalización correcta de caracteres especiales y tildes en el slug del producto
        """
        from inventario.services import CrearProductoService

        producto = CrearProductoService.execute(
            nombre="Café Sello Rojo & Canela 500g",
            categoria=self.categoria_abarrotes,
            precio_compra=Decimal("12000.00"),
            precio_venta=Decimal("15500.00"),
            stock_actual=10,
            stock_minimo=2,
        )

        self.assertEqual(producto.slug, "cafe-sello-rojo-canela-500g")

    def test_servicio_rechazo_nombre_duplicado_case_insensitive(self):
        """
        Escenario: Rechazo de producto duplicado case-insensitive con mensaje exacto
        """
        from inventario.services import CrearProductoService

        CrearProductoService.execute(
            nombre="Coca cola x 350",
            categoria=self.categoria_bebidas,
            precio_compra=Decimal("2000.00"),
            precio_venta=Decimal("2500.00"),
        )

        with self.assertRaises(ValidationError) as ctx:
            CrearProductoService.execute(
                nombre="coca cola x 350",
                categoria=self.categoria_bebidas,
                precio_compra=Decimal("2000.00"),
                precio_venta=Decimal("2500.00"),
            )

        self.assertIn("El producto ya se encuentra registrado", str(ctx.exception))

    def test_servicio_rechazo_precios_o_stock_negativos(self):
        """
        Escenario: Validación de rechazo de precios o stocks negativos
        """
        from inventario.services import CrearProductoService

        with self.assertRaises(ValidationError):
            CrearProductoService.execute(
                nombre="Producto Inválido 1",
                categoria=self.categoria_bebidas,
                precio_compra=Decimal("-500.00"),
                precio_venta=Decimal("1000.00"),
            )

        with self.assertRaises(ValidationError):
            CrearProductoService.execute(
                nombre="Producto Inválido 2",
                categoria=self.categoria_bebidas,
                precio_compra=Decimal("500.00"),
                precio_venta=Decimal("1000.00"),
                stock_actual=-5,
            )

    def test_servicio_relacion_1_a_n_con_categoria(self):
        """
        Escenario: Relación 1:N entre Categoria y Producto (un producto pertenece a una categoría, una categoría tiene muchos productos)
        """
        from inventario.models import Producto
        from inventario.services import CrearProductoService

        p1 = CrearProductoService.execute(
            nombre="Coca Cola 1.5L",
            categoria=self.categoria_bebidas,
            precio_compra=Decimal("3500.00"),
            precio_venta=Decimal("4500.00"),
            stock_actual=10,
        )
        p2 = CrearProductoService.execute(
            nombre="Jugo de Naranja 1L",
            categoria=self.categoria_bebidas,
            precio_compra=Decimal("2800.00"),
            precio_venta=Decimal("3600.00"),
            stock_actual=15,
        )

        # Cada producto pertenece a la categoría asignada
        self.assertEqual(p1.categoria, self.categoria_bebidas)
        self.assertEqual(p2.categoria, self.categoria_bebidas)

        # La categoría contiene a ambos productos a través de su relación inversa (related_name='productos')
        productos_bebidas = self.categoria_bebidas.productos.all()
        self.assertEqual(productos_bebidas.count(), 2)
        self.assertIn(p1, productos_bebidas)
        self.assertIn(p2, productos_bebidas)

        # Conteo reflejado en la propiedad total_productos
        self.assertEqual(self.categoria_bebidas.total_productos, 2)

    def test_servicio_es_atomico_ante_fallos_de_persistencia(self):
        """
        Escenario NFR: Atomicidad garantizada con rollback completo ante excepción inesperada
        """
        from inventario.models import Producto
        from inventario.services import CrearProductoService

        initial_count = Producto.objects.count()

        with patch.object(Producto, 'save', side_effect=RuntimeError("Database failure")):
            with self.assertRaises(RuntimeError):
                CrearProductoService.execute(
                    nombre="Producto Atómico",
                    categoria=self.categoria_bebidas,
                    precio_compra=Decimal("1000.00"),
                    precio_venta=Decimal("1500.00"),
                )

        self.assertEqual(Producto.objects.count(), initial_count)
        self.assertFalse(Producto.objects.filter(nombre="Producto Atómico").exists())


class ProductRegistrationViewsAndRBACSecurityTests(TestCase):
    """
    Pruebas de integración para rutas HTTP, seguridad RBAC, validación de formularios y accesibilidad UI (HU-004)
    """

    def setUp(self):
        self.client = Client()

        # Categorías base
        self.cat_lacteos = Categoria.objects.create(nombre="Lácteos", activo=True)
        self.cat_abarrotes = Categoria.objects.create(nombre="Abarrotes", activo=True)
        self.cat_bebidas = Categoria.objects.create(nombre="Bebidas", activo=True)
        self.cat_carnes = Categoria.objects.create(nombre="Carnes", activo=True)

        # Permisos oficiales según specs/auth.md
        content_type, _ = ContentType.objects.get_or_create(app_label='inventario', model='producto')
        self.perm_add_producto, _ = Permission.objects.get_or_create(
            codename='add_producto',
            content_type=content_type,
            defaults={'name': 'Puede registrar productos'},
        )
        self.perm_view_producto, _ = Permission.objects.get_or_create(
            codename='view_producto',
            content_type=content_type,
            defaults={'name': 'Puede ver productos'},
        )

        # Roles / Grupos
        self.grupo_admin, _ = Group.objects.get_or_create(name='administrador')
        self.grupo_admin.permissions.add(self.perm_add_producto, self.perm_view_producto)

        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        self.grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')

        # Usuarios de prueba
        self.admin_user = User.objects.create_user(username='admin_user', password='password123', is_staff=True)
        self.admin_user.groups.add(self.grupo_admin)

        self.base_user = User.objects.create_user(username='base_user', password='password123')
        self.base_user.groups.add(self.grupo_usuario)

        self.vendedor_user = User.objects.create_user(username='vendedor_user', password='password123')
        self.vendedor_user.groups.add(self.grupo_vendedor)

        self.direct_perm_user = User.objects.create_user(username='direct_user', password='password123')
        self.direct_perm_user.user_permissions.add(self.perm_add_producto)

    def test_usuario_anonimo_redirigido_al_login(self):
        """
        Escenario RBAC NFR: Visitante anónimo es redirigido a login
        """
        url = reverse('inventario:crear_producto')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)
        self.assertIn('next=/inventario/productos/crear/', response.url)

    def test_usuario_rol_usuario_recibe_403_forbidden(self):
        """
        Escenario RBAC: Usuario con rol 'usuario' recibe 403 Forbidden al intentar acceder por GET o POST
        """
        self.client.force_login(self.base_user)
        url = reverse('inventario:crear_producto')

        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 403)

        post_response = self.client.post(url, {'nombre': 'Intento Ilegal'})
        self.assertEqual(post_response.status_code, 403)

    def test_usuario_rol_vendedor_sin_permiso_recibe_403_forbidden(self):
        """
        Escenario RBAC: Usuario vendedor (sin permiso inventario.add_producto) recibe 403 Forbidden
        """
        self.client.force_login(self.vendedor_user)
        url = reverse('inventario:crear_producto')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_usuario_con_permiso_directo_puede_acceder_al_formulario(self):
        """
        Escenario RBAC: Usuario no administrador con permiso directo puede acceder
        """
        self.client.force_login(self.direct_perm_user)
        url = reverse('inventario:crear_producto')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_formulario_muestra_categorias_ordenadas_alfabeticamente(self):
        """
        Escenario: El selector de categorías despliega las opciones ordenadas alfabéticamente
        """
        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_producto')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verificar que el formulario contenga el campo categoría con queryset ordenado
        form = response.context['form']
        cat_names = list(form.fields['categoria'].queryset.values_list('nombre', flat=True))
        self.assertEqual(cat_names, sorted(cat_names))
        self.assertEqual(cat_names, ["Abarrotes", "Bebidas", "Carnes", "Lácteos"])

    def test_creacion_exitosa_producto_por_administrador_con_mensaje_y_redireccion(self):
        """
        Escenario: Administrador completa formulario válidamente y el producto es creado con mensaje accesible
        """
        from inventario.models import Producto

        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_producto')

        payload = {
            'nombre': 'Galletas Festival Chocolate',
            'categoria': self.cat_abarrotes.pk,
            'precio_compra': '1200.00',
            'precio_venta': '1800.00',
            'stock_actual': '48',
            'stock_minimo': '12',
            'descripcion': 'Taco de galletas festival sabor chocolate',
            'activo': 'on',
        }

        response = self.client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verificar creación del producto
        self.assertTrue(Producto.objects.filter(nombre='Galletas Festival Chocolate').exists())
        producto = Producto.objects.get(nombre='Galletas Festival Chocolate')
        self.assertEqual(producto.categoria, self.cat_abarrotes)
        self.assertEqual(producto.slug, 'galletas-festival-chocolate')
        self.assertEqual(producto.stock_actual, 48)

        # Mensaje de confirmación flash accesible
        messages = list(response.context['messages'])
        self.assertTrue(len(messages) > 0)
        self.assertTrue(any('creado exitosamente' in m.message.lower() or 'Galletas Festival Chocolate' in m.message for m in messages))

    def test_formulario_rechaza_nombre_duplicado_con_atributos_accesibles(self):
        """
        Escenario: Rechazo de duplicidad con aria-invalid="true" y role="alert"
        """
        from inventario.models import Producto

        Producto.objects.create(
            nombre="Coca cola x 350",
            categoria=self.cat_bebidas,
            precio_compra=Decimal("2000.00"),
            precio_venta=Decimal("2500.00"),
        )

        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_producto')

        payload = {
            'nombre': 'coca cola x 350',
            'categoria': self.cat_bebidas.pk,
            'precio_compra': '2000.00',
            'precio_venta': '2500.00',
            'stock_actual': '10',
            'stock_minimo': '2',
            'activo': 'on',
        }

        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('El producto ya se encuentra registrado', html)
        self.assertIn('role="alert"', html)
        self.assertIn('aria-invalid="true"', html)

    def test_formulario_rechaza_campos_obligatorios_vacios(self):
        """
        Escenario: Rechazo de formulario cuando faltan campos obligatorios
        """
        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_producto')

        # Envío con nombre vacío
        payload = {
            'nombre': '',
            'categoria': self.cat_bebidas.pk,
            'precio_compra': '1000.00',
            'precio_venta': '1500.00',
        }

        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('nombre', form.errors)

    def test_formulario_accesibilidad_wcag_labels_y_clases_numericas(self):
        """
        Escenario NFR: Todos los inputs tienen asociado su <label for="..."> y clases font-mono tabular-nums
        """
        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_producto')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')

        # Verificar labels para campos esenciales
        expected_labels = [
            'for="id_nombre"',
            'for="id_categoria"',
            'for="id_precio_compra"',
            'for="id_precio_venta"',
            'for="id_stock_actual"',
            'for="id_stock_minimo"',
        ]
        for label in expected_labels:
            self.assertIn(label, html)

        # Tipografía numérica font-mono tabular-nums
        self.assertIn('tabular-nums', html)

    def test_formulario_acepta_precios_con_puntos_de_miles_sin_decimales(self):
        """
        Escenario: Envío de precios formateados con puntos de miles (ej. 3.500 y 4.500) sin decimales
        """
        from inventario.models import Producto

        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_producto')

        payload = {
            'nombre': 'Jugo Hit Mora 1L',
            'categoria': self.cat_bebidas.pk,
            'precio_compra': '3.500',
            'precio_venta': '4.500',
            'stock_actual': '20',
            'stock_minimo': '5',
            'activo': 'on',
        }

        response = self.client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

        producto = Producto.objects.get(nombre='Jugo Hit Mora 1L')
        self.assertEqual(producto.precio_compra, Decimal('3500'))
        self.assertEqual(producto.precio_venta, Decimal('4500'))

