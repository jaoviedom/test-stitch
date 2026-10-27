from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError


class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'full-name',
            'placeholder': 'Ej. Sara Jensen',
            'autocomplete': 'name',
            'class': 'w-full h-10 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-10 pr-3 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'username',
            'placeholder': 'sara.jensen',
            'autocomplete': 'username',
            'class': 'w-full h-10 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-10 pr-3 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'id': 'email',
            'placeholder': 'usuario@teckstore.io',
            'autocomplete': 'email',
            'class': 'w-full h-10 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-10 pr-3 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    password1 = forms.CharField(
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'id': 'password',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
            'class': 'w-full h-10 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-10 pr-10 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    password2 = forms.CharField(
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'id': 'confirm-password',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
            'class': 'w-full h-10 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-10 pr-10 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'id': 'terms',
            'class': 'peer sr-only',
        })
    )

    def clean_username(self) -> str:
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Ya existe un usuario registrado con este nombre de usuario.")
        return username

    def clean_email(self) -> str:
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta registrada con este correo electrónico.")
        return email

    def clean(self) -> dict:
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')

        if p1 and p2 and p1 != p2:
            self.add_error('password2', ValidationError("Las contraseñas no coinciden."))

        return cleaned_data


class UpdateUserAccessForm(forms.Form):
    """
    Formulario para gestionar los múltiples roles y permisos directos de un usuario (HU-002).
    """
    roles = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['roles'].queryset = Group.objects.all()
        self.fields['permissions'].queryset = Permission.objects.filter(
            codename__in=[
                'view_categoria', 'add_categoria', 'change_categoria',
                'view_producto', 'add_producto', 'change_producto',
                'access_pos', 'manage_access'
            ]
        )


class LoginForm(forms.Form):
    """
    Formulario de autenticación para TeckStore (HU-003).
    Soporta identificación por username o correo electrónico y persistencia de sesión.
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Usuario o Correo",
        widget=forms.TextInput(attrs={
            'id': 'id_username',
            'placeholder': 'usuario o correo@example.com',
            'autocomplete': 'username',
            'class': 'w-full h-11 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-11 pr-4 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    password = forms.CharField(
        required=True,
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'id': 'id_password',
            'placeholder': '••••••••••••',
            'autocomplete': 'current-password',
            'class': 'w-full h-11 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-11 pr-11 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    remember_me = forms.BooleanField(
        required=False,
        label="Recordar este dispositivo por 30 días",
        widget=forms.CheckboxInput(attrs={
            'id': 'id_remember_me',
            'class': 'w-4 h-4 rounded border-outline-variant/40 text-primary focus:ring-primary/20 accent-primary cursor-pointer',
        })
    )


class UserProfileForm(forms.Form):
    """
    Formulario para actualización de datos personales del perfil (HU-004).
    Valida campos obligatorios y unicidad de correo electrónico excluyendo la cuenta actual.
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nombre Completo",
        widget=forms.TextInput(attrs={
            'id': 'id_first_name',
            'placeholder': 'Ej. Jose Alonso Oviedo',
            'autocomplete': 'name',
            'class': 'w-full h-11 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-11 pr-4 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    email = forms.EmailField(
        required=True,
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={
            'id': 'id_email',
            'placeholder': 'usuario@teckstore.io',
            'autocomplete': 'email',
            'class': 'w-full h-11 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-11 pr-4 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    def __init__(self, *args, user: User = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_first_name(self) -> str:
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise ValidationError("El nombre completo es requerido.")
        return first_name

    def clean_email(self) -> str:
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise ValidationError("El correo electrónico es requerido.")

        query = User.objects.filter(email__iexact=email)
        if self.user and self.user.pk:
            query = query.exclude(pk=self.user.pk)

        if query.exists():
            raise ValidationError("Este correo electrónico ya está registrado por otra cuenta de usuario.")

        return email


class UserPasswordChangeForm(forms.Form):
    """
    Formulario para cambio seguro de contraseña en el perfil (HU-004).
    Valida la contraseña actual del usuario y asegura que las nuevas contraseñas coincidan y cumplan las reglas.
    """
    current_password = forms.CharField(
        required=True,
        label="Contraseña Actual",
        widget=forms.PasswordInput(attrs={
            'id': 'id_current_password',
            'placeholder': '••••••••••••',
            'autocomplete': 'current-password',
            'class': 'w-full h-11 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-11 pr-4 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    new_password1 = forms.CharField(
        min_length=8,
        required=True,
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={
            'id': 'id_new_password1',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
            'class': 'w-full h-11 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-11 pr-4 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    new_password2 = forms.CharField(
        min_length=8,
        required=True,
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={
            'id': 'id_new_password2',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
            'class': 'w-full h-11 bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-11 pr-4 rounded-xl border border-outline-variant/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all',
        })
    )

    def __init__(self, *args, user: User = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self) -> str:
        current_password = self.cleaned_data.get('current_password', '')
        if self.user and not self.user.check_password(current_password):
            raise ValidationError("La contraseña actual ingresada es incorrecta.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                self.add_error('new_password2', "Las contraseñas nuevas no coinciden.")
            elif self.user:
                from django.contrib.auth.password_validation import validate_password
                try:
                    validate_password(new_password1, user=self.user)
                except ValidationError as error:
                    self.add_error('new_password1', error)

        return cleaned_data


