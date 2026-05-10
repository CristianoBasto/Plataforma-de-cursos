from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.http import HttpResponse
import datetime
import qrcode
import io


def gerar_qrcode(url):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1a1a2e', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return ImageReader(buffer)


def gerar_certificado(usuario, curso, request=None):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificado_{curso.slug}.pdf"'

    c = canvas.Canvas(response, pagesize=landscape(A4))
    largura, altura = landscape(A4)

    # ─── FUNDO BRANCO ───
    c.setFillColor(colors.white)
    c.rect(0, 0, largura, altura, fill=1, stroke=0)

    # ─── FUNDO TOPO decorativo ───
    c.setFillColor(colors.HexColor('#1a1a2e'))
    c.rect(0, altura - 110, largura, 110, fill=1, stroke=0)

    # ─── FAIXA INFERIOR decorativa ───
    c.setFillColor(colors.HexColor('#1a1a2e'))
    c.rect(0, 0, largura, 55, fill=1, stroke=0)

    # ─── LINHA ACCENT topo ───
    c.setFillColor(colors.HexColor('#f4a261'))
    c.rect(0, altura - 115, largura, 5, fill=1, stroke=0)

    # ─── LINHA ACCENT inferior ───
    c.setFillColor(colors.HexColor('#f4a261'))
    c.rect(0, 55, largura, 5, fill=1, stroke=0)

    # ─── BORDAS LATERAIS ───
    c.setFillColor(colors.HexColor('#f4a261'))
    c.rect(0, 0, 8, altura, fill=1, stroke=0)
    c.rect(largura - 8, 0, 8, altura, fill=1, stroke=0)

    # ─── NOME DA PLATAFORMA ───
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 32)
    c.drawCentredString(largura / 2, altura - 70, 'SisPlay')

    c.setFillColor(colors.HexColor('#f4a261'))
    c.setFont('Helvetica', 13)
    c.drawCentredString(largura / 2, altura - 92, 'Plataforma de Cursos Online')

    # ─── TÍTULO CERTIFICADO ───
    c.setFillColor(colors.HexColor('#1a1a2e'))
    c.setFont('Helvetica-Bold', 26)
    c.drawCentredString(largura / 2, altura - 160, 'CERTIFICADO DE CONCLUSÃO')

    # ─── LINHA DECORATIVA ───
    c.setStrokeColor(colors.HexColor('#f4a261'))
    c.setLineWidth(2)
    c.line(largura / 2 - 180, altura - 172, largura / 2 + 180, altura - 172)

    # ─── TEXTO CERTIFICA ───
    c.setFillColor(colors.HexColor('#555555'))
    c.setFont('Helvetica', 14)
    c.drawCentredString(largura / 2, altura - 210, 'Certificamos que')

    # ─── NOME DO ALUNO ───
    nome = usuario.get_full_name() or usuario.username
    c.setFillColor(colors.HexColor('#1a1a2e'))
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(largura / 2, altura - 260, nome)

    # ─── LINHA SOB O NOME ───
    c.setStrokeColor(colors.HexColor('#dddddd'))
    c.setLineWidth(1)
    c.line(largura / 2 - 220, altura - 272, largura / 2 + 220, altura - 272)

    # ─── TEXTO CURSO ───
    c.setFillColor(colors.HexColor('#555555'))
    c.setFont('Helvetica', 14)
    c.drawCentredString(largura / 2, altura - 305, 'concluiu com êxito o curso')

    # ─── NOME DO CURSO ───
    c.setFillColor(colors.HexColor('#f4a261'))
    c.setFont('Helvetica-Bold', 24)
    c.drawCentredString(largura / 2, altura - 345, curso.titulo)

    # ─── INFORMAÇÕES ADICIONAIS ───
    total_segundos = sum(a.duracao for a in __import__('cursos.models', fromlist=['Aula']).Aula.objects.filter(modulo__curso=curso))
    total_horas = max(1, total_segundos // 3600)

    c.setFillColor(colors.HexColor('#777777'))
    c.setFont('Helvetica', 11)
    hoje = datetime.date.today()
    c.drawCentredString(largura / 2, altura - 378, f'Nível: {curso.get_nivel_display()}   ·   Carga horária: {total_horas}h   ·   Concluído em: {hoje.strftime("%d/%m/%Y")}')

    # ─── INSTRUTOR ───
    instrutor = curso.instrutor.get_full_name() or curso.instrutor.username
    c.setFillColor(colors.HexColor('#555555'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(largura / 2, altura - 400, f'Instrutor: {instrutor}')

    # ─── CÓDIGO DE VERIFICAÇÃO ───
    import hashlib
    codigo = hashlib.sha256(f'{usuario.id}{curso.id}{hoje}'.encode()).hexdigest()[:12].upper()

    # ─── ASSINATURA ESQUERDA ───
    c.setStrokeColor(colors.HexColor('#aaaaaa'))
    c.setLineWidth(1)
    c.line(100, 100, 280, 100)
    c.setFillColor(colors.HexColor('#1a1a2e'))
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(190, 85, 'SisPlay')
    c.setFillColor(colors.HexColor('#777777'))
    c.setFont('Helvetica', 10)
    c.drawCentredString(190, 72, 'Plataforma de Cursos Online')

    # ─── CÓDIGO CENTRAL ───
    c.setFillColor(colors.HexColor('#1a1a2e'))
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(largura / 2, 90, f'Código de verificação')
    c.setFillColor(colors.HexColor('#f4a261'))
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(largura / 2, 72, codigo)

    # ─── ASSINATURA DIREITA ───
    c.setStrokeColor(colors.HexColor('#aaaaaa'))
    c.line(largura - 280, 100, largura - 100, 100)
    c.setFillColor(colors.HexColor('#1a1a2e'))
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(largura - 190, 85, instrutor)
    c.setFillColor(colors.HexColor('#777777'))
    c.setFont('Helvetica', 10)
    c.drawCentredString(largura - 190, 72, 'Instrutor')

    # ─── QR CODE ───
    if request:
        url_verificacao = request.build_absolute_uri(f'/cursos/{curso.slug}/')
    else:
        url_verificacao = f'https://sisplay.com.br/cursos/{curso.slug}/'

    qr_img = gerar_qrcode(url_verificacao)
    c.drawImage(qr_img, largura - 115, 65, width=80, height=80)
    c.setFillColor(colors.HexColor('#777777'))
    c.setFont('Helvetica', 8)
    c.drawCentredString(largura - 75, 60, 'Verificar curso')

    # ─── MARCA D'ÁGUA ───
    c.saveState()
    c.setFillColor(colors.HexColor('#f4a261'))
    c.setFont('Helvetica-Bold', 60)
    c.translate(largura / 2, altura / 2)
    c.rotate(35)
    c.setFillAlpha(0.04)
    c.drawCentredString(0, 0, 'SisPlay')
    c.restoreState()

    c.save()
    return response