from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<slug:slug>/', views.checkout, name='checkout'),
    path('sucesso/', views.sucesso, name='pagamento_sucesso'),
    path('recusado/', views.recusado, name='pagamento_recusado'),
    path('webhook/', views.webhook, name='pagamento_webhook'),
]