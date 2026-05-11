from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = 'Categorias'


class Curso(models.Model):
    NIVEL_CHOICES = [
        ('iniciante', 'Iniciante'),
        ('intermediario', 'Intermediário'),
        ('avancado', 'Avançado'),
    ]

    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descricao = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    gratuito = models.BooleanField(default=False)
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='iniciante')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    instrutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cursos_criados')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    publicado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def total_aulas(self):
        return Aula.objects.filter(modulo__curso=self).count()

    def total_alunos(self):
        return Matricula.objects.filter(curso=self).count()

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name_plural = 'Cursos'


class Modulo(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='modulos')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.curso.titulo} - {self.titulo}'

    class Meta:
        ordering = ['ordem']
        verbose_name_plural = 'Módulos'


class Aula(models.Model):
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='aulas')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    video_url = models.URLField(blank=True, help_text='URL externa (YouTube, Vimeo, Google Drive)')
    video_file = models.FileField(upload_to='aulas/videos/', blank=True, null=True, help_text='Upload de vídeo direto')
    duracao = models.PositiveIntegerField(default=0, help_text='Duração em segundos')
    ordem = models.PositiveIntegerField(default=0)
    gratuita = models.BooleanField(default=False, help_text='Aula de preview gratuita')
    criada_em = models.DateTimeField(auto_now_add=True)
    apostila = models.FileField(upload_to='aulas/apostilas/', blank=True, null=True, help_text='Material de apoio em PDF')

    def duracao_formatada(self):
        minutos = self.duracao // 60
        segundos = self.duracao % 60
        return f'{minutos:02d}:{segundos:02d}'

    def get_video(self):
        if self.video_file:
            return ('file', self.video_file.url)
        elif self.video_url:
            return ('url', self.video_url)
        return (None, None)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ['ordem']
        verbose_name_plural = 'Aulas'


class Matricula(models.Model):
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matriculas')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='matriculas')
    data_matricula = models.DateTimeField(auto_now_add=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        unique_together = ('aluno', 'curso')
        verbose_name_plural = 'Matrículas'

    def __str__(self):
        return f'{self.aluno.username} - {self.curso.titulo}'

    def progresso(self):
        from django.db.models import Count
        total = Aula.objects.filter(modulo__curso=self.curso).count()
        if total == 0:
            return 0
        concluidas = Progresso.objects.filter(
            aluno=self.aluno,
            aula__modulo__curso=self.curso,
            concluida=True
        ).count()
        return int((concluidas / total) * 100)


class Progresso(models.Model):
    aluno = models.ForeignKey(User, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    concluida = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('aluno', 'aula')
        verbose_name_plural = 'Progressos'

    def __str__(self):
        return f'{self.aluno.username} - {self.aula.titulo}'


class Avaliacao(models.Model):
    aluno = models.ForeignKey(User, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='avaliacoes')
    nota = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comentario = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('aluno', 'curso')
        verbose_name_plural = 'Avaliações'


class Comentario(models.Model):
    aluno = models.ForeignKey(User, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='comentarios')
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='respostas')

    def __str__(self):
        return f'{self.aluno.username} - {self.aula.titulo}'

    class Meta:
        ordering = ['criado_em']
        verbose_name_plural = 'Comentários'