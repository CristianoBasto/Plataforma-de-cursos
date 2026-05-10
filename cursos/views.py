from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Curso, Modulo, Aula, Matricula, Progresso, Categoria, Avaliacao


def home(request):
    cursos_destaque = Curso.objects.filter(publicado=True).order_by('-criado_em')[:6]
    categorias = Categoria.objects.all()
    return render(request, 'base/home.html', {
        'cursos_destaque': cursos_destaque,
        'categorias': categorias,
    })


def lista_cursos(request):
    # Redireciona instrutor para o painel
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.is_instrutor():
        return redirect('instrutor_dashboard')
    
    # ... resto do código
    cursos = Curso.objects.filter(publicado=True)
    categoria_slug = request.GET.get('categoria')
    nivel = request.GET.get('nivel')
    busca = request.GET.get('busca')

    if categoria_slug:
        cursos = cursos.filter(categoria__slug=categoria_slug)
    if nivel:
        cursos = cursos.filter(nivel=nivel)
    if busca:
        cursos = cursos.filter(titulo__icontains=busca)

    categorias = Categoria.objects.all()
    return render(request, 'cursos/lista.html', {
        'cursos': cursos,
        'categorias': categorias,
        'nivel_atual': nivel,
        'categoria_atual': categoria_slug,
        'busca': busca,
    })


def detalhe_curso(request, slug):
    curso = get_object_or_404(Curso, slug=slug, publicado=True)
    modulos = curso.modulos.prefetch_related('aulas').all()
    matriculado = False
    progresso = 0

    if request.user.is_authenticated:
        matricula = Matricula.objects.filter(aluno=request.user, curso=curso).first()
        if matricula:
            matriculado = True
            progresso = matricula.progresso()

    avaliacoes = curso.avaliacoes.select_related('aluno').order_by('-criada_em')[:5]

    return render(request, 'cursos/detalhe.html', {
        'curso': curso,
        'modulos': modulos,
        'matriculado': matriculado,
        'progresso': progresso,
        'avaliacoes': avaliacoes,
    })


@login_required
def matricular(request, slug):
    curso = get_object_or_404(Curso, slug=slug, publicado=True)
    matricula, criada = Matricula.objects.get_or_create(aluno=request.user, curso=curso)
    if criada:
        from core.emails import email_matricula_confirmada
        email_matricula_confirmada(request.user, curso)
        messages.success(request, f'Matrícula no curso "{curso.titulo}" realizada com sucesso!')
    else:
        messages.info(request, 'Você já está matriculado neste curso.')
    return redirect('assistir_aula', slug=slug)


@login_required
def assistir_aula(request, slug, aula_id=None):
    curso = get_object_or_404(Curso, slug=slug, publicado=True)
    matricula = get_object_or_404(Matricula, aluno=request.user, curso=curso, ativa=True)
    modulos = curso.modulos.prefetch_related('aulas').all()

    # Pegar primeira aula se não especificado
    if not aula_id:
        primeira_aula = Aula.objects.filter(modulo__curso=curso).order_by('modulo__ordem', 'ordem').first()
        if primeira_aula:
            return redirect('assistir_aula_id', slug=slug, aula_id=primeira_aula.id)

    aula = get_object_or_404(Aula, id=aula_id, modulo__curso=curso)
    progresso_obj, _ = Progresso.objects.get_or_create(aluno=request.user, aula=aula)

    # Aulas anterior e próxima
    todas_aulas = list(Aula.objects.filter(modulo__curso=curso).order_by('modulo__ordem', 'ordem'))
    idx = next((i for i, a in enumerate(todas_aulas) if a.id == aula.id), None)
    aula_anterior = todas_aulas[idx - 1] if idx and idx > 0 else None
    proxima_aula = todas_aulas[idx + 1] if idx is not None and idx < len(todas_aulas) - 1 else None

    aulas_concluidas = set(
        Progresso.objects.filter(
            aluno=request.user,
            aula__modulo__curso=curso,
            concluida=True
        ).values_list('aula_id', flat=True)
    )
    
    from .models import Comentario
    comentarios = aula.comentarios.filter(parent=None).prefetch_related('respostas__aluno')
    return render(request, 'cursos/assistir.html', {
        'curso': curso,
        'modulos': modulos,
        'aula': aula,
        'progresso_obj': progresso_obj,
        'aula_anterior': aula_anterior,
        'proxima_aula': proxima_aula,
        'aulas_concluidas': aulas_concluidas,
        'progresso_total': matricula.progresso(),
        'comentarios': comentarios,
    })


@login_required
def marcar_concluida(request, aula_id):
    if request.method == 'POST':
        aula = get_object_or_404(Aula, id=aula_id)
        matricula = get_object_or_404(Matricula, aluno=request.user, curso=aula.modulo.curso, ativa=True)
        progresso, criado = Progresso.objects.get_or_create(aluno=request.user, aula=aula)
        progresso.concluida = not progresso.concluida
        if progresso.concluida:
            progresso.data_conclusao = timezone.now()
        else:
            progresso.data_conclusao = None
        progresso.save()
        matricula = Matricula.objects.filter(aluno=request.user, curso=aula.modulo.curso).first()
        if matricula and matricula.progresso() == 100:
            from core.emails import email_certificado_disponivel
            email_certificado_disponivel(request.user, aula.modulo.curso)
            return redirect('assistir_aula_id', slug=aula.modulo.curso.slug, aula_id=aula_id)


@login_required
def meus_cursos(request):
     # Redireciona instrutor para o painel
    if hasattr(request.user, 'profile') and request.user.profile.is_instrutor():
        return redirect('instrutor_dashboard')
    matriculas = Matricula.objects.filter(aluno=request.user, ativa=True).select_related('curso')
    return render(request, 'cursos/meus_cursos.html', {'matriculas': matriculas})


@login_required
def avaliar_curso(request, slug):
    curso = get_object_or_404(Curso, slug=slug)
    if request.method == 'POST':
        nota = request.POST.get('nota')
        comentario = request.POST.get('comentario', '')
        Avaliacao.objects.update_or_create(
            aluno=request.user,
            curso=curso,
            defaults={'nota': nota, 'comentario': comentario}
        )
        messages.success(request, 'Avaliação enviada!')
    return redirect('detalhe_curso', slug=slug)


@login_required
def comentar_aula(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)
    if request.method == 'POST':
        texto = request.POST.get('texto', '').strip()
        parent_id = request.POST.get('parent_id')
        if texto:
            from .models import Comentario
            Comentario.objects.create(
                aluno=request.user,
                aula=aula,
                texto=texto,
                parent_id=parent_id if parent_id else None
            )
        if parent_id:
            from cursos.models import Comentario
            parent = Comentario.objects.filter(id=parent_id).first()
            if parent and parent.aluno != request.user:
                from core.emails import email_comentario_respondido
                email_comentario_respondido(
                    usuario=parent.aluno,
                    aula=aula,
                    resposta=texto,
                    instrutor=request.user
                )
            messages.success(request, 'Comentário enviado!')
    return redirect('assistir_aula_id', slug=aula.modulo.curso.slug, aula_id=aula.id)


@login_required
def deletar_comentario(request, comentario_id):
    from .models import Comentario
    comentario = get_object_or_404(Comentario, id=comentario_id, aluno=request.user)
    aula = comentario.aula
    comentario.delete()
    return redirect('assistir_aula_id', slug=aula.modulo.curso.slug, aula_id=aula.id)


@login_required
def emitir_certificado(request, slug):
    curso = get_object_or_404(Curso, slug=slug, publicado=True)
    matricula = get_object_or_404(Matricula, aluno=request.user, curso=curso, ativa=True)

    if matricula.progresso() < 100:
        messages.error(request, 'Você precisa concluir todas as aulas para emitir o certificado.')
        return redirect('assistir_aula', slug=slug)

    from .certificado import gerar_certificado
    return gerar_certificado(request.user, curso, request)