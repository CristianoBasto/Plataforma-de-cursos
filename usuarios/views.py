from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistroForm, PerfilForm
from functools import wraps


def instrutor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile') or not request.user.profile.is_instrutor():
            messages.error(request, 'Acesso restrito a instrutores.')
            return redirect('lista_cursos')
        return view_func(request, *args, **kwargs)
    return wrapper


def login_view(request):
    if request.user.is_authenticated:
        return redirect('lista_cursos')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'lista_cursos')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})


def registro_view(request):
    if request.user.is_authenticated:
        return redirect('lista_cursos')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            from core.emails import email_boas_vindas
            email_boas_vindas(user)


            messages.success(request, f'Bem-vindo(a), {user.first_name}!')
            if user.profile.is_instrutor():
                return redirect('instrutor_dashboard')
            return redirect('lista_cursos')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def perfil_view(request):
    from cursos.models import Matricula
    matriculas = Matricula.objects.filter(aluno=request.user).select_related('curso')
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado!')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    return render(request, 'usuarios/perfil.html', {
        'form': form,
        'matriculas': matriculas,
    })


# ---- PAINEL DO INSTRUTOR ----

@instrutor_required
def instrutor_dashboard(request):
    from cursos.models import Curso, Matricula
    from pagamentos.models import Pagamento
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    import json

    cursos = Curso.objects.filter(instrutor=request.user)
    total_alunos = Matricula.objects.filter(curso__instrutor=request.user).count()
    total_publicados = cursos.filter(publicado=True).count()

    # Receita total
    receita_total = Pagamento.objects.filter(
        curso__instrutor=request.user,
        status='aprovado'
    ).aggregate(total=Sum('valor'))['total'] or 0

    # Receita por mês (últimos 6 meses)
    from datetime import datetime, timedelta
    seis_meses_atras = datetime.now() - timedelta(days=180)

    receita_mensal = Pagamento.objects.filter(
        curso__instrutor=request.user,
        status='aprovado',
        criado_em__gte=seis_meses_atras
    ).annotate(
        mes=TruncMonth('criado_em')
    ).values('mes').annotate(
        total=Sum('valor')
    ).order_by('mes')

    labels_receita = []
    dados_receita = []
    meses_pt = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
        5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
        9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    for item in receita_mensal:
        labels_receita.append(f"{meses_pt[item['mes'].month]}/{item['mes'].year}")
        dados_receita.append(float(item['total']))

    # Alunos por mês (últimos 6 meses)
    alunos_mensal = Matricula.objects.filter(
        curso__instrutor=request.user,
        data_matricula__gte=seis_meses_atras
    ).annotate(
        mes=TruncMonth('data_matricula')
    ).values('mes').annotate(
        total=Count('id')
    ).order_by('mes')

    labels_alunos = []
    dados_alunos = []
    for item in alunos_mensal:
        labels_alunos.append(f"{meses_pt[item['mes'].month]}/{item['mes'].year}")
        dados_alunos.append(item['total'])

    # Cursos mais vendidos
    cursos_vendidos = cursos.annotate(
        total_matriculas=Count('matriculas'),
        receita=Sum('pagamentos__valor', filter=__import__('django.db.models', fromlist=['Q']).Q(pagamentos__status='aprovado'))
    ).order_by('-total_matriculas')[:5]

    labels_cursos = [c.titulo[:20] + '...' if len(c.titulo) > 20 else c.titulo for c in cursos_vendidos]
    dados_cursos = [c.total_matriculas for c in cursos_vendidos]

    return render(request, 'instrutor/dashboard.html', {
        'cursos': cursos,
        'total_alunos': total_alunos,
        'total_publicados': total_publicados,
        'receita_total': receita_total,
        'labels_receita': json.dumps(labels_receita),
        'dados_receita': json.dumps(dados_receita),
        'labels_alunos': json.dumps(labels_alunos),
        'dados_alunos': json.dumps(dados_alunos),
        'labels_cursos': json.dumps(labels_cursos),
        'dados_cursos': json.dumps(dados_cursos),
        'cursos_vendidos': cursos_vendidos,
    })

@instrutor_required
def instrutor_curso_criar(request):
    from cursos.models import Curso, Categoria
    categorias = Categoria.objects.all()
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        nivel = request.POST.get('nivel')
        preco = request.POST.get('preco') or 0
        gratuito = request.POST.get('gratuito') == 'on'
        publicado = request.POST.get('publicado') == 'on'
        categoria_id = request.POST.get('categoria')
        thumbnail = request.FILES.get('thumbnail')

        curso = Curso.objects.create(
            titulo=titulo,
            descricao=descricao,
            nivel=nivel,
            preco=preco,
            gratuito=gratuito,
            publicado=publicado,
            categoria_id=categoria_id if categoria_id else None,
            instrutor=request.user,
            thumbnail=thumbnail,
        )
        messages.success(request, f'Curso "{curso.titulo}" criado!')
        return redirect('instrutor_curso_editar', curso_id=curso.id)
    return render(request, 'instrutor/curso_form.html', {'categorias': categorias})


@instrutor_required
def instrutor_curso_editar(request, curso_id):
    from cursos.models import Curso, Categoria, Modulo, Aula
    from django.shortcuts import get_object_or_404
    curso = get_object_or_404(Curso, id=curso_id, instrutor=request.user)
    categorias = Categoria.objects.all()
    modulos = curso.modulos.prefetch_related('aulas').all()

    if request.method == 'POST':
        curso.titulo = request.POST.get('titulo')
        curso.descricao = request.POST.get('descricao')
        curso.nivel = request.POST.get('nivel')
        curso.preco = request.POST.get('preco') or 0
        curso.gratuito = request.POST.get('gratuito') == 'on'
        curso.publicado = request.POST.get('publicado') == 'on'
        categoria_id = request.POST.get('categoria')
        curso.categoria_id = categoria_id if categoria_id else None
        if request.FILES.get('thumbnail'):
            curso.thumbnail = request.FILES.get('thumbnail')
        curso.save()
        messages.success(request, 'Curso atualizado!')
        return redirect('instrutor_curso_editar', curso_id=curso.id)

    return render(request, 'instrutor/curso_form.html', {
        'curso': curso,
        'categorias': categorias,
        'modulos': modulos,
    })


@instrutor_required
def instrutor_modulo_criar(request, curso_id):
    from cursos.models import Curso, Modulo
    from django.shortcuts import get_object_or_404
    curso = get_object_or_404(Curso, id=curso_id, instrutor=request.user)
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao', '')
        ordem = request.POST.get('ordem', 0)
        Modulo.objects.create(curso=curso, titulo=titulo, descricao=descricao, ordem=ordem)
        messages.success(request, 'Módulo criado!')
    return redirect('instrutor_curso_editar', curso_id=curso.id)


@instrutor_required
def instrutor_aula_criar(request, modulo_id):
    from cursos.models import Modulo, Aula
    from django.shortcuts import get_object_or_404
    modulo = get_object_or_404(Modulo, id=modulo_id, curso__instrutor=request.user)
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao', '')
        video_url = request.POST.get('video_url', '')
        duracao = request.POST.get('duracao', 0)
        ordem = request.POST.get('ordem', 0)
        gratuita = request.POST.get('gratuita') == 'on'
        Aula.objects.create(
            modulo=modulo,
            titulo=titulo,
            descricao=descricao,
            video_url=video_url,
            duracao=duracao,
            ordem=ordem,
            gratuita=gratuita,
        )
        messages.success(request, 'Aula criada!')
    return redirect('instrutor_curso_editar', curso_id=modulo.curso.id)


@instrutor_required
def instrutor_aula_deletar(request, aula_id):
    from cursos.models import Aula
    from django.shortcuts import get_object_or_404
    aula = get_object_or_404(Aula, id=aula_id, modulo__curso__instrutor=request.user)
    curso_id = aula.modulo.curso.id
    aula.delete()
    messages.success(request, 'Aula removida!')
    return redirect('instrutor_curso_editar', curso_id=curso_id)


@instrutor_required
def instrutor_modulo_deletar(request, modulo_id):
    from cursos.models import Modulo
    from django.shortcuts import get_object_or_404
    modulo = get_object_or_404(Modulo, id=modulo_id, curso__instrutor=request.user)
    curso_id = modulo.curso.id
    modulo.delete()
    messages.success(request, 'Módulo removido!')
    return redirect('instrutor_curso_editar', curso_id=curso_id)