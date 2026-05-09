from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('instrutor/', views.instrutor_dashboard, name='instrutor_dashboard'),
    path('instrutor/curso/novo/', views.instrutor_curso_criar, name='instrutor_curso_criar'),
    path('instrutor/curso/<int:curso_id>/', views.instrutor_curso_editar, name='instrutor_curso_editar'),
    path('instrutor/curso/<int:curso_id>/modulo/', views.instrutor_modulo_criar, name='instrutor_modulo_criar'),
    path('instrutor/modulo/<int:modulo_id>/aula/', views.instrutor_aula_criar, name='instrutor_aula_criar'),
    path('instrutor/aula/<int:aula_id>/deletar/', views.instrutor_aula_deletar, name='instrutor_aula_deletar'),
    path('instrutor/modulo/<int:modulo_id>/deletar/', views.instrutor_modulo_deletar, name='instrutor_modulo_deletar'),
]