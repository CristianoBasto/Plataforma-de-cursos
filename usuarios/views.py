from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistroForm, PerfilForm


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
            messages.success(request, f'Bem-vindo(a), {user.first_name}!')
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
        form = PerfilForm(request.POST, instance=request.user)
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
