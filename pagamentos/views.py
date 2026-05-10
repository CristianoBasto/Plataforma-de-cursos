from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
import mercadopago
import json

from cursos.models import Curso, Matricula
from .models import Pagamento


@login_required
def checkout(request, slug):

    curso = get_object_or_404(Curso, slug=slug, publicado=True)

    if Matricula.objects.filter(aluno=request.user, curso=curso).exists():
        messages.info(request, 'Você já está matriculado neste curso.')
        return redirect('assistir_aula', slug=slug)

    if curso.gratuito:
        Matricula.objects.get_or_create(aluno=request.user, curso=curso)
        return redirect('assistir_aula', slug=slug)

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    # base_url = request.build_absolute_uri('/').rstrip('/')
    base_url = request.build_absolute_uri('/').rstrip('/')
    
    # Forçar HTTPS apenas se não for localhost
    if not any(host in base_url for host in ['127.0.0.1', 'localhost']) and base_url.startswith('http://'):
        base_url = base_url.replace('http://', 'https://', 1)
    
    print('BASE URL:', base_url)
    
# Forçar HTTPS para o Mercado Pago
    if base_url.startswith('http://'):
        base_url = base_url.replace('http://', 'https://', 1)
    print('BASE URL:', base_url)

    # preference_data = {
    #     "items": [
    #         {
    #             "title": curso.titulo,
    #             "quantity": 1,
    #             "currency_id": "BRL",
    #             "unit_price": float(curso.preco),
    #         }
    #     ],
    #     "payer": {
    #         "email": request.user.email,
    #     },
    #     "back_urls": {
    #         "success": f"{base_url}/pagamentos/sucesso/",
    #         "failure": f"{base_url}/pagamentos/recusado/",
    #         "pending": f"{base_url}/pagamentos/sucesso/",
    #     },
    #     "auto_return": "approved",
    #     "external_reference": f"{request.user.id}_{curso.id}",
    # }
    
    preference_data = {
        "items": [
            {
                "title": curso.titulo,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(curso.preco),
            }
        ],
        "payer": {
            "email": request.user.email,
        },
        "payment_methods": {
            "installments": 12,
            "default_installments": 1,
        },
        "back_urls": {
            "success": f"{base_url}/pagamentos/sucesso/",
            "failure": f"{base_url}/pagamentos/recusado/",
            "pending": f"{base_url}/pagamentos/sucesso/",
        },
        "auto_return": "all",
        "external_reference": f"{request.user.id}_{curso.id}",
    }

    preference_response = sdk.preference().create(preference_data)
    
    # DEBUG - mostra resposta completa
    # print('=' * 50)
    # print('STATUS:', preference_response.get('status'))
    # print('RESPONSE:', preference_response.get('response'))
    # print('=' * 50)

    if preference_response.get('status') != 201:
        messages.error(request, f'Erro ao criar preferência: {preference_response.get("response")}')
        return redirect('detalhe_curso', slug=slug)

    preference = preference_response["response"]

    pagamento, _ = Pagamento.objects.get_or_create(
        aluno=request.user,
        curso=curso,
        defaults={
            'valor': curso.preco,
            'status': 'pendente',
            'preference_id': preference.get('id', ''),
        }
    )
    pagamento.preference_id = preference.get('id', '')
    pagamento.save()

    return render(request, 'pagamentos/checkout.html', {
        'curso': curso,
        'preference_id': preference.get('id'),
        'public_key': settings.MERCADOPAGO_PUBLIC_KEY,
    })

@login_required
def sucesso(request):
    print('PARAMS RECEBIDOS:', dict(request.GET))

    payment_id = request.GET.get('payment_id')
    external_reference = request.GET.get('external_reference', '')
    status = request.GET.get('status') or request.GET.get('collection_status')
    preference_id = request.GET.get('preference_id')

    # Tentar buscar pelo preference_id se não tiver external_reference
    if not external_reference and preference_id:
        pagamento = Pagamento.objects.filter(preference_id=preference_id).first()
        if pagamento:
            external_reference = f'{pagamento.aluno.id}_{pagamento.curso.id}'
            status = 'approved'

    if external_reference and status == 'approved':
        try:
            user_id, curso_id = external_reference.split('_')
            curso = Curso.objects.get(id=curso_id)

            pagamento = Pagamento.objects.filter(
                aluno=request.user,
                curso=curso
            ).first()
            if pagamento:
                pagamento.status = 'aprovado'
                pagamento.payment_id = payment_id or ''
                pagamento.save()

            Matricula.objects.get_or_create(aluno=request.user, curso=curso)

            from core.emails import email_pagamento_aprovado
            resultado = email_pagamento_aprovado(
                request.user,
                curso,
                pagamento.valor if pagamento else curso.preco
            )
            print('EMAIL ENVIADO:', resultado)

            messages.success(request, f'Pagamento aprovado! Bem-vindo ao curso "{curso.titulo}"!')
            return render(request, 'pagamentos/sucesso.html', {'curso': curso})
        except Exception as e:
            print('ERRO:', e)
            import traceback
            traceback.print_exc()

    return render(request, 'pagamentos/sucesso.html', {'curso': None})


@login_required
def recusado(request):
    messages.error(request, 'Pagamento recusado. Tente novamente.')
    return redirect('lista_cursos')


@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if data.get('type') == 'payment':
                payment_id = data['data']['id']
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                payment_info = sdk.payment().get(payment_id)
                payment = payment_info['response']

                external_reference = payment.get('external_reference', '')
                status = payment.get('status')

                if external_reference:
                    user_id, curso_id = external_reference.split('_')
                    pagamento = Pagamento.objects.filter(
                        aluno_id=user_id,
                        curso_id=curso_id
                    ).first()
                    if pagamento:
                        if status == 'approved':
                            pagamento.status = 'aprovado'
                            Matricula.objects.get_or_create(
                                aluno_id=user_id,
                                curso_id=curso_id
                            )
                        elif status in ['rejected', 'cancelled']:
                            pagamento.status = 'recusado'
                        pagamento.payment_id = str(payment_id)
                        pagamento.save()
        except Exception:
            pass
    return HttpResponse(status=200)

