import PyPDF2
import csv
import base64
import io
import easyocr
import re
from transformers import pipeline
from PIL import Image
from PIL.ExifTags import TAGS

#---------------------------------------------------------------------------------------------------------------
# Função que Converte MarkDown para HTML
#

def converter_texto_para_html(texto_markdown):
    """Converte texto no formato 'markdown' para HTML, suportando títulos, negrito inline e parágrafos."""
    linhas = texto_markdown.splitlines()
    html_output = "<html><body>\n"

    for linha in linhas:
        linha = linha.strip()

        if linha.startswith("##"):
            titulo = linha[2:].strip()
            # Formatar títulos (h2)
            html_output += f"<h2>{titulo}</h2>\n"
        elif linha: # Linha não vazia (pode conter texto normal ou negrito inline)
            # Processar negrito inline **texto** usando regex antes de envolver em <p>
            linha_com_negrito_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', linha)
            # Envolver o resto da linha (já com negrito formatado) em parágrafo (p)
            html_output += f"<p>{linha_com_negrito_html}</p>\n"

    html_output += "</body></html>"
    return html_output

#
# FIM Converte MarkDown para HTML
#---------------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------
# Função para extrair texto de uma imagem usando EasyOCR
#
def extrair_texto_de_imagem_sem_ia_EasyOCR(imagem_bytes):
    """
    Converte uma imagem em formato de bytes para texto sem usar IA,
    extraindo metadados, informações básicas e utilizando OCR com EasyOCR.

    Args:
        imagem_bytes: Os bytes da imagem.

    Returns:
        Um dicionário contendo informações sobre a imagem, como metadados,
        tamanho, formato e texto extraído (se houver).
    """

    try:
        imagem = Image.open(io.BytesIO(imagem_bytes))
    except Exception as e:
        return f"Erro ao abrir a imagem: {e}"

    informacoes_da_imagem = {}

    # Metadados EXIF
    metadados_exif = {}
    if hasattr(imagem, "_getexif"):
        exif = imagem._getexif()
        if exif is not None:
            for tag, valor in exif.items():
                nome_da_tag = TAGS.get(tag, tag)
                metadados_exif[nome_da_tag] = valor
    informacoes_da_imagem["metadados_exif"] = metadados_exif

    # Informações básicas
    informacoes_da_imagem["formato"] = imagem.format
    informacoes_da_imagem["tamanho"] = imagem.size
    informacoes_da_imagem["modo_de_cor"] = imagem.mode

    # Texto na imagem (OCR com EasyOCR)
    texto_extraido = ""
    try:
        leitor = easyocr.Reader(['pt', 'en'])  # 'pt' para português, 'en' para inglês
        resultado = leitor.readtext(imagem)
        # texto_extraido = ""
        for (caixa_delimitadora, texto, confianca) in resultado:
            texto_extraido += texto + " "
        informacoes_da_imagem["texto_extraido"] = texto_extraido
    except Exception as e:
        informacoes_da_imagem["texto_extraido"] = f"Erro no OCR com EasyOCR: {e}"

    return texto_extraido
#
# FIM
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
# Função para extrair texto de uma imagem usanco OCR Pysseract
#
def extrair_texto_de_imagem_sem_ia(imagem_bytes):
    """
    Converte uma imagem em formato de bytes para texto sem usar IA,
    extraindo metadados, informações básicas e utilizando OCR para texto na imagem.

    Args:
        imagem_bytes: Os bytes da imagem.

    Returns:
        Um dicionário contendo informações sobre a imagem, como metadados,
        tamanho, formato e texto extraído (se houver).
    """

    try:
        imagem = Image.open(io.BytesIO(imagem_bytes))
    except Exception as e:
        return f"Erro ao abrir a imagem: {e}"

    informacoes_da_imagem = {}

    # Metadados EXIF
    metadados_exif = {}
    if hasattr(imagem, "_getexif"):
        exif = imagem._getexif()
        if exif is not None:
            for tag, valor in exif.items():
                nome_da_tag = TAGS.get(tag, tag)
                metadados_exif[nome_da_tag] = valor
    informacoes_da_imagem["metadados_exif"] = metadados_exif

    # Informações básicas
    informacoes_da_imagem["formato"] = imagem.format
    informacoes_da_imagem["tamanho"] = imagem.size
    informacoes_da_imagem["modo_de_cor"] = imagem.mode

    # Texto na imagem (OCR)
    try:
        import pytesseract  # Certifique-se de ter o pytesseract instalado
        texto_extraido = pytesseract.image_to_string(imagem)
        informacoes_da_imagem["texto_extraido"] = texto_extraido
    except ImportError:
        informacoes_da_imagem["texto_extraido"] = "Pytesseract não instalado."
    except Exception as e:
        informacoes_da_imagem["texto_extraido"] = f"Erro no OCR: {e}"

    return informacoes_da_imagem
#
# FIM
#---------------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------
# Função para extrair texto de um PDF
#
def extrair_texto_de_imagem(imagem_base64):
    """
    Converte uma imagem em formato base64 para texto usando o modelo BLIP.

    Args:
        imagem_base64: Uma string contendo a imagem em formato base64.

    Returns:
        Uma string contendo a descrição textual da imagem.
    """

    # Decodifica a imagem base64 para dados binários
    imagem_binaria = base64.b64decode(imagem_base64)
    
    # Converte os dados binários para um objeto PIL
    imagem_pil = Image.open(io.BytesIO(imagem_binaria))

    # Cria um pipeline de image-to-text com o modelo BLIP
    gerador_de_legenda = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

    # Gera a legenda da imagem
    descricao = gerador_de_legenda(imagem_pil)[0]["generated_text"]

    return descricao
#
# FIM
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
# Função para extrair texto de um PDF
#
def extrair_texto_de_pdf(pdf_path):
    if pdf_path == '':
        return ''
    else:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
#
# FIM
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
# Função que armaezena em uma tabela a categorização dos chamados "NÃO CATEGORIZADOS" e "NÃO ATENDIDOS"
#
# Exemplo de uso converter_para_csv(nome_tabela, nome_arquivo, campos = ["Id_Ticket", "Resumo", "Dificuldade", "SLA"])
def converter_para_csv(tabela, nome_arquivo, fieldnames):
    """Converte a tabela para um arquivo CSV, sobrescrevendo o arquivo existente ou criando um novo."""
    with open(nome_arquivo, 'w', newline='') as arquivo_csv:  # Abre o arquivo em modo de escrita ('w')
        # Cria o cabeçalho do CSV
        #fieldnames = ["Id_Ticket", "Resumo", "Dificuldade", "SLA"]
        writer = csv.DictWriter(arquivo_csv, fieldnames=fieldnames, delimiter=';')

        writer.writeheader()

        # Escreve os dados na tabela
        for linha in tabela:
            writer.writerow(linha)
    pass

def converter_para_csv_v2(tabela, nome_arquivo, fieldnames):
    """Converte a tabela para um arquivo CSV, sobrescrevendo o arquivo existente ou criando um novo."""
    try:
        with open(nome_arquivo, 'w', encoding='utf-8', newline='') as arquivo_csv:
            writer = csv.DictWriter(arquivo_csv, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for linha in tabela:
                # Limpeza de caracteres problemáticos
                linha_limpa = {}
                for chave, valor in linha.items():
                    if isinstance(valor, str):
                        linha_limpa[chave] = valor.replace('\u200b', '')  # Remove espaços de largura zero
                    else:
                        linha_limpa[chave] = valor
                writer.writerow(linha_limpa)
    except Exception as e:
        print(f"Erro ao converter para CSV: {e}")
#
# FIM
#---------------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------
# Função que remove símbolos do texto. No momento, apenas '*' e '#'
#
def limpa_texto(_texto, _alvo, _transformacao):
    sujeira = True
    contador = 0
    while sujeira:
        if _alvo in _texto:
            _texto = _texto.replace(_alvo, _transformacao)
        else:
            sujeira = False
            contador += 1
    return _texto
#
# FIM
#---------------------------------------------------------------------------------------------------------------