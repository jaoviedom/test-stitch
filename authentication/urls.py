from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/', views.user_list_view, name='user_list'),
    path('usuarios/<int:user_id>/accesos/', views.user_manage_access_view, name='user_manage_access'),
    path('perfil/', views.profile_view, name='profile'),
    path('profile/', views.profile_view, name='profile_alias'),
]

