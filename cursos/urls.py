from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_cursos, name='lista_cursos'),
    path('meus-cursos/', views.meus_cursos, name='meus_cursos'),
    path('aula/<int:aula_id>/concluir/', views.marcar_concluida, name='marcar_concluida'),
    path('aula/<int:aula_id>/comentar/', views.comentar_aula, name='comentar_aula'),
    path('comentario/<int:comentario_id>/deletar/', views.deletar_comentario, name='deletar_comentario'),
    path('<slug:slug>/', views.detalhe_curso, name='detalhe_curso'),
    path('<slug:slug>/matricular/', views.matricular, name='matricular'),
    path('<slug:slug>/assistir/', views.assistir_aula, name='assistir_aula'),
    path('<slug:slug>/assistir/<int:aula_id>/', views.assistir_aula, name='assistir_aula_id'),
    path('<slug:slug>/avaliar/', views.avaliar_curso, name='avaliar_curso'),
    path('<slug:slug>/certificado/', views.emitir_certificado, name='certificado'),
]