from django.db import models
from django.contrib.auth.models import User
from cursos.models import Curso


class Pagamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
        ('cancelado', 'Cancelado'),
    ]

    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagamentos')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='pagamentos')
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    preference_id = models.CharField(max_length=200, blank=True)
    payment_id = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.aluno.username} - {self.curso.titulo} - {self.status}'

    class Meta:
        verbose_name_plural = 'Pagamentos'