from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import datetime


def enviar_email(destinatario, assunto, template, contexto):
    try:
        html = render_to_string(template, contexto)
        send_mail(
            subject=assunto,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            html_message=html,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Erro ao enviar email: {e}')
        return False


def email_boas_vindas(usuario):
    return enviar_email(
        destinatario=usuario.email,
        assunto='Bem-vindo(a) à SisPlay! 🎉',
        template='emails/boas_vindas.html',
        contexto={
            'nome': usuario.first_name or usuario.username,
            'url_cursos': f'{settings.SITE_URL}/cursos/',
        }
    )


def email_matricula_confirmada(usuario, curso):
    return enviar_email(
        destinatario=usuario.email,
        assunto=f'Matrícula confirmada — {curso.titulo}',
        template='emails/matricula_confirmada.html',
        contexto={
            'nome': usuario.first_name or usuario.username,
            'curso_titulo': curso.titulo,
            'curso_nivel': curso.get_nivel_display(),
            'total_aulas': curso.total_aulas(),
            'instrutor': curso.instrutor.get_full_name() or curso.instrutor.username,
            'data': datetime.date.today().strftime('%d/%m/%Y'),
            'url_curso': f'{settings.SITE_URL}/cursos/{curso.slug}/assistir/',
        }
    )


def email_pagamento_aprovado(usuario, curso, valor):
    return enviar_email(
        destinatario=usuario.email,
        assunto=f'Pagamento aprovado — {curso.titulo}',
        template='emails/pagamento_aprovado.html',
        contexto={
            'nome': usuario.first_name or usuario.username,
            'curso_titulo': curso.titulo,
            'valor': f'{valor:.2f}',
            'instrutor': curso.instrutor.get_full_name() or curso.instrutor.username,
            'data': datetime.date.today().strftime('%d/%m/%Y'),
            'url_curso': f'{settings.SITE_URL}/cursos/{curso.slug}/assistir/',
        }
    )


def email_comentario_respondido(usuario, aula, resposta, instrutor):
    return enviar_email(
        destinatario=usuario.email,
        assunto=f'Nova resposta na aula — {aula.titulo}',
        template='emails/comentario_respondido.html',
        contexto={
            'nome': usuario.first_name or usuario.username,
            'aula_titulo': aula.titulo,
            'resposta': resposta,
            'instrutor': instrutor.get_full_name() or instrutor.username,
            'url_aula': f'{settings.SITE_URL}/cursos/{aula.modulo.curso.slug}/assistir/{aula.id}/',
        }
    )


def email_certificado_disponivel(usuario, curso):
    return enviar_email(
        destinatario=usuario.email,
        assunto=f'Certificado disponível — {curso.titulo} 🎓',
        template='emails/certificado_disponivel.html',
        contexto={
            'nome': usuario.first_name or usuario.username,
            'curso_titulo': curso.titulo,
            'data': datetime.date.today().strftime('%d/%m/%Y'),
            'url_certificado': f'{settings.SITE_URL}/cursos/{curso.slug}/certificado/',
        }
    )