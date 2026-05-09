from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    TIPO_CHOICES = [
        ('aluno', 'Aluno'),
        ('instrutor', 'Instrutor'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='aluno')
    bio = models.TextField(blank=True)
    foto = models.ImageField(upload_to='perfis/', blank=True, null=True)

    def __str__(self):
        return f'{self.usuario.username} - {self.tipo}'

    def is_instrutor(self):
        return self.tipo == 'instrutor'

    def is_aluno(self):
        return self.tipo == 'aluno'


@receiver(post_save, sender=User)
def criar_ou_salvar_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(usuario=instance)