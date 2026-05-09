from django.contrib import admin
from .models import Curso, Modulo, Aula, Matricula, Progresso, Categoria, Avaliacao

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('titulo',)}
    list_display = ('titulo', 'instrutor', 'nivel', 'publicado', 'criado_em')
    list_filter = ('publicado', 'nivel', 'categoria')
    search_fields = ('titulo',)

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'ordem')

@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'modulo', 'ordem', 'gratuita')

admin.site.register(Matricula)
admin.site.register(Progresso)
admin.site.register(Avaliacao)



from .models import Comentario

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'aula', 'criado_em')
    search_fields = ('aluno__username', 'texto')