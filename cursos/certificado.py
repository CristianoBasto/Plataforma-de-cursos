from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from django.http import HttpResponse
import datetime


def gerar_certificado(usuario, curso):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificado_{curso.slug}.pdf"'

    c = canvas.Canvas(response, pagesize=landscape(A4))
    largura, altura = landscape(A4)

    # Fundo
    c.setFillColor(colors.HexColor('#0d0d0d'))
    c.rect(0, 0, largura, altura, fill=1, stroke=0)

    # Borda decorativa
    c.setStrokeColor(colors.HexColor('#ff6b35'))
    c.setLineWidth(3)
    c.rect(20, 20, largura - 40, altura - 40, fill=0, stroke=1)
    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor('#ffaa00'))
    c.rect(28, 28, largura - 56, altura - 56, fill=0, stroke=1)

    # Logo / Nome da plataforma
    c.setFillColor(colors.HexColor('#ff6b35'))
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(largura / 2, altura - 90, 'EduPlay')

    # Título
    c.setFillColor(colors.HexColor('#f0f0f0'))
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(largura / 2, altura - 140, 'CERTIFICADO DE CONCLUSÃO')

    # Linha decorativa
    c.setStrokeColor(colors.HexColor('#ff6b35'))
    c.setLineWidth(2)
    c.line(largura / 2 - 150, altura - 155, largura / 2 + 150, altura - 155)

    # Texto principal
    c.setFillColor(colors.HexColor('#999999'))
    c.setFont('Helvetica', 14)
    c.drawCentredString(largura / 2, altura - 200, 'Certificamos que')

    # Nome do aluno
    nome = usuario.get_full_name() or usuario.username
    c.setFillColor(colors.HexColor('#f0f0f0'))
    c.setFont('Helvetica-Bold', 32)
    c.drawCentredString(largura / 2, altura - 250, nome)

    # Linha sob o nome
    c.setStrokeColor(colors.HexColor('#2a2a2a'))
    c.setLineWidth(1)
    c.line(largura / 2 - 200, altura - 260, largura / 2 + 200, altura - 260)

    # Texto do curso
    c.setFillColor(colors.HexColor('#999999'))
    c.setFont('Helvetica', 14)
    c.drawCentredString(largura / 2, altura - 295, 'concluiu com êxito o curso')

    # Nome do curso
    c.setFillColor(colors.HexColor('#ffaa00'))
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(largura / 2, altura - 335, curso.titulo)

    # Carga horária (estimada pelas aulas)
    total_aulas = curso.total_aulas()
    carga = total_aulas * 1  # estimativa de 1h por aula
    c.setFillColor(colors.HexColor('#999999'))
    c.setFont('Helvetica', 12)
    c.drawCentredString(largura / 2, altura - 370, f'com carga horária estimada de {carga} hora(s)')

    # Data
    hoje = datetime.date.today().strftime('%d de %B de %Y')
    c.setFont('Helvetica', 11)
    c.drawCentredString(largura / 2, altura - 410, f'Emitido em {hoje}')

    # Assinatura
    c.setStrokeColor(colors.HexColor('#2a2a2a'))
    c.line(largura / 2 - 100, altura - 460, largura / 2 + 100, altura - 460)
    c.setFillColor(colors.HexColor('#999999'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(largura / 2, altura - 475, 'EduPlay — Plataforma de Cursos Online')

    c.save()
    return response