from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import (
    UserRegistrationForm,
    UpdateUserAccessForm,
    LoginForm,
    UserProfileForm,
    UserPasswordChangeForm,
)
from .services import (
    RegisterUserService,
    UpdateUserAccessService,
    AuthenticateUserService,
    UpdateUserProfileService,
    UpdateUserPasswordService,
)



def login_view(request):
    """
    Controlador de inicio de sesión seguro (HU-003).
    Soporta autenticación por username o email, redirección con 'next' segura y persistencia de sesión.
    """
    if request.user.is_authenticated:
        return redirect('inventario:dashboard')

    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            user = AuthenticateUserService.execute(
                identifier=identifier,
                password=password,
                request=request,
            )

            if user is not None:
                login(request, user)

                if remember_me:
                    request.session.set_expiry(2592000)  # 30 días
                else:
                    request.session.set_expiry(0)  # Expira al cerrar el navegador

                messages.success(request, f"¡Bienvenido de nuevo, {user.first_name or user.username}!")

                if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('inventario:dashboard')
            else:
                form.add_error(None, "Nombre de usuario, correo o contraseña incorrectos.")
    else:
        form = LoginForm()

    context = {
        'form': form,
        'next': next_url,
    }
    return render(request, 'authentication/login.html', context, status=200)


def register_view(request):
    """
    Controlador de registro de nuevos usuarios con rol base por defecto (HU-001)
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']

            user = RegisterUserService.execute(
                first_name=first_name,
                username=username,
                email=email,
                password=password,
            )

            login(request, user)
            messages.success(request, f"¡Bienvenido a TeckStore, {user.first_name}! Tu cuenta ha sido activada.")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'authentication/register.html', {'form': form})


def _check_manage_access(user: User) -> None:
    """Verifica si el usuario posee autorización para gestionar roles"""
    if not (user.is_superuser or user.has_perm('authentication.manage_access') or user.has_perm('auth.manage_access')):
        raise PermissionDenied("No posee autorización para gestionar roles y permisos.")


@login_required
def user_list_view(request):
    """
    Lista de usuarios para el administrador con sus roles asignados (HU-002)
    """
    _check_manage_access(request.user)
    users = User.objects.all().prefetch_related('groups', 'user_permissions').order_by('-date_joined')
    context = {
        'users': users,
        'active_nav': 'usuarios',
    }
    return render(request, 'authentication/user_list.html', context)


@login_required
def user_manage_access_view(request, user_id: int):
    """
    Formulario para asignar o revocar roles y permisos a un usuario específico (HU-002)
    """
    _check_manage_access(request.user)
    target_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UpdateUserAccessForm(request.POST)
        if form.is_valid():
            role_names = [g.name for g in form.cleaned_data['roles']]
            permission_codenames = [p.codename for p in form.cleaned_data['permissions']]

            UpdateUserAccessService.execute(
                target_user=target_user,
                role_names=role_names,
                permission_codenames=permission_codenames,
                requested_by=request.user,
            )

            messages.success(request, f"Accesos de '{target_user.username}' actualizados exitosamente.")
            return redirect('authentication:user_list')
    else:
        form = UpdateUserAccessForm(initial={
            'roles': target_user.groups.all(),
            'permissions': target_user.user_permissions.all(),
        })

    context = {
        'target_user': target_user,
        'form': form,
        'active_nav': 'usuarios',
    }
    return render(request, 'authentication/user_manage_access.html', context)


def logout_view(request):
    """
    Cierra la sesión del usuario actual y redirige a la pantalla de login
    """
    logout(request)
    messages.info(request, "Has cerrado tu sesión en TeckStore.")
    return redirect('authentication:login')


@login_required
def profile_view(request):
    """
    Vista de consulta y actualización de perfil de usuario (HU-004).
    Permite consultar roles y permisos en modo solo lectura, actualizar información personal
    y cambiar la contraseña con validación segura y preservación de sesión.
    """
    user = request.user
    profile_form = UserProfileForm(user=user, initial={'first_name': user.first_name, 'email': user.email})
    password_form = UserPasswordChangeForm(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            profile_form = UserProfileForm(request.POST, user=user)
            if profile_form.is_valid():
                first_name = profile_form.cleaned_data['first_name']
                email = profile_form.cleaned_data['email']

                UpdateUserProfileService.execute(
                    user=user,
                    first_name=first_name,
                    email=email,
                )
                messages.success(request, "Tu información de perfil ha sido actualizada con éxito.")
                return redirect('authentication:profile')

        elif action == 'change_password':
            password_form = UserPasswordChangeForm(request.POST, user=user)
            if password_form.is_valid():
                current_password = password_form.cleaned_data['current_password']
                new_password = password_form.cleaned_data['new_password1']

                UpdateUserPasswordService.execute(
                    user=user,
                    current_password=current_password,
                    new_password=new_password,
                )
                update_session_auth_hash(request, user)
                messages.success(request, "Tu contraseña ha sido actualizada con éxito.")
                return redirect('authentication:profile')

    context = {
        'profile_user': user,
        'profile_form': profile_form,
        'password_form': password_form,
        'active_nav': 'perfil',
    }
    return render(request, 'authentication/profile.html', context)



