from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class UserLoginUnitAndServiceTests(TestCase):
    """
    Pruebas unitarias para la capa de servicio de autenticación dual (HU-003)
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='carlosr',
            email='carlos@tienda.co',
            password='Password123!',
            first_name='Carlos',
        )

    def test_authenticate_service_success_with_exact_username(self):
        """
        Escenario: Autenticación exitosa por nombre de usuario exacto
        """
        from authentication.services import AuthenticateUserService

        user = AuthenticateUserService.execute(
            identifier='carlosr',
            password='Password123!',
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(user.username, 'carlosr')

    def test_authenticate_service_success_with_case_insensitive_username(self):
        """
        Escenario: Autenticación insensible a mayúsculas/minúsculas en username
        """
        from authentication.services import AuthenticateUserService

        user = AuthenticateUserService.execute(
            identifier='CaRlOsR',
            password='Password123!',
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.user.pk)

    def test_authenticate_service_success_with_exact_email(self):
        """
        Escenario: Autenticación exitosa utilizando correo electrónico
        """
        from authentication.services import AuthenticateUserService

        user = AuthenticateUserService.execute(
            identifier='carlos@tienda.co',
            password='Password123!',
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(user.email, 'carlos@tienda.co')

    def test_authenticate_service_success_with_case_insensitive_email(self):
        """
        Escenario: Autenticación insensible a mayúsculas/minúsculas en email
        """
        from authentication.services import AuthenticateUserService

        user = AuthenticateUserService.execute(
            identifier='CARLOS@TIENDA.CO',
            password='Password123!',
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.user.pk)

    def test_authenticate_service_fails_with_wrong_password(self):
        """
        Escenario: Falla de autenticación por contraseña incorrecta
        """
        from authentication.services import AuthenticateUserService

        user = AuthenticateUserService.execute(
            identifier='carlosr',
            password='ContrasenaEquivocada123',
        )
        self.assertIsNone(user)

    def test_authenticate_service_fails_with_nonexistent_user(self):
        """
        Escenario: Falla de autenticación con usuario o correo inexistente
        """
        from authentication.services import AuthenticateUserService

        user = AuthenticateUserService.execute(
            identifier='usuario_fantasma',
            password='Password123!',
        )
        self.assertIsNone(user)


class UserLoginIntegrationAndViewsTests(TestCase):
    """
    Pruebas de integración HTTP y vistas para login, redirecciones y seguridad NFR (HU-003)
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='carlosr',
            email='carlos@tienda.co',
            password='Password123!',
            first_name='Carlos',
        )

    def test_login_page_renders_with_form_and_csrf_token(self):
        """
        Escenario: La página de login renderiza correctamente (HTTP 200) con formulario accesible
        """
        response = self.client.get(reverse('authentication:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar Sesión')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'name="remember_me"')

    def test_login_success_with_username_creates_session_and_redirects(self):
        """
        Escenario: Login exitoso por nombre de usuario crea sesión y redirige a /inventario/
        """
        response = self.client.post(
            reverse('authentication:login'),
            data={
                'username': 'carlosr',
                'password': 'Password123!',
                'remember_me': 'on',
            },
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('inventario:dashboard'))

        # Validar sesión activa en el cliente
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_success_with_email_creates_session_and_redirects(self):
        """
        Escenario: Login exitoso por email crea sesión activa y redirige a /inventario/
        """
        response = self.client.post(
            reverse('authentication:login'),
            data={
                'username': 'carlos@tienda.co',
                'password': 'Password123!',
            },
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('inventario:dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_redirects_to_next_url_when_internal_and_safe(self):
        """
        Escenario: Redirección contextual respetando el parámetro 'next' seguro
        """
        target_next = '/inventario/categorias/'
        response = self.client.post(
            f"{reverse('authentication:login')}?next={target_next}",
            data={
                'username': 'carlosr',
                'password': 'Password123!',
                'next': target_next,
            },
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, target_next)

    def test_login_open_redirect_protection_sanitizes_malicious_next(self):
        """
        Escenario NFR: Protección contra Open Redirect hacia sitios externos maliciosos
        """
        malicious_next = 'https://sitio-malicioso.com/phishing'
        response = self.client.post(
            f"{reverse('authentication:login')}?next={malicious_next}",
            data={
                'username': 'carlosr',
                'password': 'Password123!',
                'next': malicious_next,
            },
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        # Debe redirigir de forma segura al dashboard interno y nunca al dominio malicioso
        self.assertEqual(response.url, reverse('inventario:dashboard'))
        self.assertNotIn('sitio-malicioso.com', response.url)

    def test_login_fails_with_invalid_credentials_shows_generic_accessible_alert(self):
        """
        Escenario: Rechazo de credenciales con HTTP 200, role='alert' y prevención de enumeración
        """
        response = self.client.post(
            reverse('authentication:login'),
            data={
                'username': 'carlosr',
                'password': 'PasswordEquivocada!',
            },
            follow=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

        # NFR Accesibilidad: role="alert"
        self.assertContains(response, 'role="alert"')

        # NFR Seguridad: Mensaje genérico que no revela si existe el usuario o falló la clave
        self.assertContains(response, 'Nombre de usuario, correo o contraseña incorrectos')

    def test_authenticated_user_redirected_away_from_login_page(self):
        """
        Escenario: Usuario ya autenticado es redirigido inmediatamente a /inventario/
        """
        self.client.force_login(self.user)

        response_get = self.client.get(reverse('authentication:login'))
        self.assertEqual(response_get.status_code, 302)
        self.assertEqual(response_get.url, reverse('inventario:dashboard'))

        response_post = self.client.post(reverse('authentication:login'), data={})
        self.assertEqual(response_post.status_code, 302)
        self.assertEqual(response_post.url, reverse('inventario:dashboard'))

    def test_login_remember_me_controls_session_expiry(self):
        """
        Escenario: Casilla 'remember_me' configura la expiración de la sesión en el navegador
        """
        # 1. Sin marcar remember_me: debe expirar al cerrar el navegador
        self.client.post(
            reverse('authentication:login'),
            data={
                'username': 'carlosr',
                'password': 'Password123!',
            },
        )
        self.assertTrue(self.client.session.get_expire_at_browser_close())

        self.client.logout()

        # 2. Marcando remember_me: la sesión persiste tras cerrar el navegador
        self.client.post(
            reverse('authentication:login'),
            data={
                'username': 'carlosr',
                'password': 'Password123!',
                'remember_me': 'on',
            },
        )
        self.assertFalse(self.client.session.get_expire_at_browser_close())
