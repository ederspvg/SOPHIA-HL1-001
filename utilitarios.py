import PyPDF2
import csv

import io
import easyocr
import re
from transformers import pipeline
from PIL import Image
from PIL.ExifTags import TAGS

#--------------------------------------------------------
# Para função que gera hash de keys
#
import streamlit_authenticator as stauth

#--------------------------------------------------------
# Para função que gera a signature key
#
import secrets
import base64 # esta é usada para OUTRAS COISAS TAMBÉM, como converter arquivos armazenados em banco de dados como base64 para bytes

#--------------------------------------------------------
# Para função que imprime em pdf a partir de MarkDown
#
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate
from reportlab.lib.enums import TA_JUSTIFY

#---------------------------------------------------------
# Para função que imprime pdf a partir de HTML
# 
from xhtml2pdf import pisa

#---------------------------------------------------------
# Para converter texto em áudio
# 
from gtts import gTTS
import playsound

#---------------------------------------------------------
# Para testar as variáveis de ambiente
#
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path='ambiente.env')

#---------------------------------------------------------------------------------------------------------------
# Função que Converte MarkDown para PDF a partir de MarkDown
# 

def gerar_signature_key():
    chave_secreta_bytes = secrets.token_bytes(32) # gera 32 bytes de dados aleatórios
    signature_key = base64.urlsafe_b64encode(chave_secreta_bytes).decode('utf-8')
    return signature_key
    
#
# FIM: Função que Converte MarkDown para PDF
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
# Função que Converte MarkDown para PDF a partir de MarkDown
# 

def gerar_hash(_key):
    hash_gerado = stauth.Hasher.hash(_key)
    return hash_gerado

#
# FIM: Função que Converte MarkDown para PDF
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
# Função que Converte MarkDown para PDF a partir de MarkDown
# 
def pre_processar_texto_para_pdf(texto_markdown, limite_linha=100):
    """
    Pré-processa o texto markdown para inserir quebras de linha manuais em linhas longas.

    Args:
        texto_markdown (str): Texto markdown original.
        limite_linha (int): Número máximo de caracteres por linha antes de tentar quebrar.

    Returns:
        str: Texto markdown pré-processado com quebras de linha.
    """
    linhas_originais = texto_markdown.splitlines()
    linhas_pre_processadas = []

    for linha in linhas_originais:
        if len(linha) > limite_linha:
            linhas_quebradas = []
            linha_atual = ""
            palavras = linha.split() # Tenta quebrar por palavras primeiro
            for palavra in palavras:
                if len(linha_atual + palavra + " ") <= limite_linha:
                    linha_atual += palavra + " "
                else:
                    linhas_quebradas.append(linha_atual.strip())
                    linha_atual = palavra + " " # Começa nova linha com a palavra atual
            linhas_quebradas.append(linha_atual.strip()) # Adiciona a última linha
            linhas_pre_processadas.extend(linhas_quebradas) # Adiciona as linhas quebradas
        else:
            linhas_pre_processadas.append(linha) # Linhas curtas ficam como estão
    return "\n".join(linhas_pre_processadas) # Junta tudo de volta em um texto


def converter_markdown_para_pdf_2(texto_markdown, nome_arquivo_pdf="relatorio.pdf"):
    """Gera PDF, formatando listas corretamente com indentação e quebra de linha."""
    doc = SimpleDocTemplate(nome_arquivo_pdf, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Estilos de texto (leading, spaceAfter, justify)
    style_normal = styles['Normal']
    style_normal.leading = 16
    style_normal.spaceAfter = 12
    style_normal.alignment = TA_JUSTIFY

    style_heading2 = styles['Heading2']
    style_heading2.leading = 18
    style_heading2.spaceAfter = 18
    style_heading2.alignment = TA_JUSTIFY

    style_bold = styles['Normal']
    style_bold.fontName = 'Helvetica-Bold'
    style_bold.leading = 16
    style_bold.alignment = TA_JUSTIFY

    linhas_markdown = texto_markdown.splitlines()
    bloco_paragrafo = []

    for linha_markdown in linhas_markdown:
        linha = linha_markdown.strip()

        if not linha: # Linha vazia
            if bloco_paragrafo:
                texto_paragrafo = " ".join(bloco_paragrafo)
                p = Paragraph(texto_paragrafo, style_normal)
                story.append(p)
                story.append(Spacer(1, 0.2*inch))
                bloco_paragrafo = []

        elif linha.startswith("##"): # Títulos
            if bloco_paragrafo:
                texto_paragrafo = " ".join(bloco_paragrafo)
                p = Paragraph(texto_paragrafo, style_normal)
                story.append(p)
                story.append(Spacer(1, 0.2*inch))
                bloco_paragrafo = []

            titulo = linha[2:].strip()
            p_titulo = Paragraph(titulo, style_heading2)
            story.append(p_titulo)
            story.append(Spacer(1, 0.3*inch))

        elif linha.startswith("**"): # Negrito
            if bloco_paragrafo:
                texto_paragrafo = " ".join(bloco_paragrafo)
                p = Paragraph(texto_paragrafo, style_normal)
                story.append(p)
                story.append(Spacer(1, 0.2*inch))
                bloco_paragrafo = []

            partes = linha[2:].split(':', 1)
            if len(partes) == 2:
                label = partes[0].strip() + ":"
                valor = partes[1].strip()
                texto_formatado = f"<font name='Helvetica-Bold'>{label}</font> {valor}"
            else:
                texto_formatado = f"<font name='Helvetica-Bold'>{linha[2:].strip()}</font>"
            p_negrito = Paragraph(texto_formatado, style_normal)
            story.append(p_negrito)
            story.append(Spacer(1, 0.2*inch))

        elif linha.startswith("-") or linha.startswith("*"): # ***MODIFICAÇÃO IMPORTANTE: PROCESSAMENTO DE LISTAS COM INDENTAÇÃO***
            # Determinar o nível de indentação (contar espaços em branco no início da linha)
            indentation_level = 0
            original_linha = linha_markdown # Manter a linha original para contar a indentação
            linha = linha.lstrip() # Remover espaços em branco do início para processar o conteúdo
            indentation_level = len(original_linha) - len(linha) # Calcular nível de indentação

            item_lista = linha[1:].strip() # Remover o marcador de lista (- ou *) e espaços

            # Criar uma string de espaços para indentação (4 espaços por nível de indentação)
            indent_space = "    " * (indentation_level // 4) # Ajuste o número de espaços conforme necessário

            texto_formatado = f"{indent_space}- {item_lista}" # Adicionar indentação e marcador de lista

            p_lista = Paragraph(texto_formatado, style_normal)
            story.append(p_lista)
            story.append(Spacer(1, 0.1*inch)) # Espaço menor após itens de lista


        else: # Parágrafos normais
            bloco_paragrafo.append(linha)

    if bloco_paragrafo: # Processar o último bloco de parágrafo
        texto_paragrafo = " ".join(bloco_paragrafo)
        p = Paragraph(texto_paragrafo, style_normal)
        story.append(p)

    doc.build(story)
    return nome_arquivo_pdf

def converter_markdown_para_pdf(texto_markdown, nome_arquivo_pdf="relatorio.pdf"):
    """Gera PDF, formatando listas corretamente com indentação e quebra de linha."""
    doc = SimpleDocTemplate(nome_arquivo_pdf, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Estilos de texto (leading, spaceAfter, justify)
    style_normal = styles['Normal']
    style_normal.leading = 16
    style_normal.spaceAfter = 12
    style_normal.alignment = TA_JUSTIFY

    style_heading2 = styles['Heading2']
    style_heading2.leading = 18
    style_heading2.spaceAfter = 18
    style_heading2.alignment = TA_JUSTIFY

    style_bold = styles['Normal']
    style_bold.fontName = 'Helvetica-Bold'
    style_bold.leading = 16
    style_bold.alignment = TA_JUSTIFY

    linhas_markdown = texto_markdown.splitlines()
    bloco_paragrafo = []

    for linha_markdown in linhas_markdown:
        linha = linha_markdown.strip()

        if not linha: # Linha vazia
            if bloco_paragrafo:
                texto_paragrafo = " ".join(bloco_paragrafo)
                p = Paragraph(texto_paragrafo, style_normal)
                story.append(p)
                story.append(Spacer(1, 0.2*inch))
                bloco_paragrafo = []

        elif linha.startswith("##"): # Títulos
            if bloco_paragrafo:
                texto_paragrafo = " ".join(bloco_paragrafo)
                p = Paragraph(texto_paragrafo, style_normal)
                story.append(p)
                story.append(Spacer(1, 0.2*inch))
                bloco_paragrafo = []

            titulo = linha[2:].strip()
            p_titulo = Paragraph(titulo, style_heading2)
            story.append(p_titulo)
            story.append(Spacer(1, 0.3*inch))

        elif linha.startswith("**"): # Negrito
            if bloco_paragrafo:
                texto_paragrafo = " ".join(bloco_paragrafo)
                p = Paragraph(texto_paragrafo, style_normal)
                story.append(p)
                story.append(Spacer(1, 0.2*inch))
                bloco_paragrafo = []

            partes = linha[2:].split(':', 1)
            if len(partes) == 2:
                label = partes[0].strip() + ":"
                valor = partes[1].strip()
                texto_formatado = f"<font name='Helvetica-Bold'>{label}</font> {valor}"
            else:
                texto_formatado = f"<font name='Helvetica-Bold'>{linha[2:].strip()}</font>"
            p_negrito = Paragraph(texto_formatado, style_bold)
            story.append(p_negrito)
            story.append(Spacer(1, 0.2*inch))

        elif linha.startswith("-") or linha.startswith("*"): # ***MODIFICAÇÃO IMPORTANTE: PROCESSAMENTO DE LISTAS COM INDENTAÇÃO***
            # Determinar o nível de indentação (contar espaços em branco no início da linha)
            indentation_level = 0
            original_linha = linha_markdown # Manter a linha original para contar a indentação
            linha = linha.lstrip() # Remover espaços em branco do início para processar o conteúdo
            indentation_level = len(original_linha) - len(linha) # Calcular nível de indentação

            item_lista = linha[1:].strip() # Remover o marcador de lista (- ou *) e espaços

            # Criar uma string de espaços para indentação (4 espaços por nível de indentação)
            indent_space = "    " * (indentation_level // 4) # Ajuste o número de espaços conforme necessário

            texto_formatado = f"{indent_space}- {item_lista}" # Adicionar indentação e marcador de lista

            p_lista = Paragraph(texto_formatado, style_normal)
            story.append(p_lista)
            story.append(Spacer(1, 0.1*inch)) # Espaço menor após itens de lista


        else: # Parágrafos normais
            bloco_paragrafo.append(linha)

    if bloco_paragrafo: # Processar o último bloco de parágrafo
        texto_paragrafo = " ".join(bloco_paragrafo)
        p = Paragraph(texto_paragrafo, style_normal)
        story.append(p)

    doc.build(story)
    return nome_arquivo_pdf



#
# FIM: Função que Converte MarkDown para PDF
#---------------------------------------------------------------------------------------------------------------


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


#---------------------------------------------------------------------------------------------------------------
# Função que imprime PDF a partir de HTML
# 
def converter_html_em_pdf_xhtml2pdf(html_string, nome_arquivo_pdf="relatorio_html.pdf"):
    """Gera PDF a partir de HTML usando xhtml2pdf (pisa)."""
    with open(nome_arquivo_pdf, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(
            html_string,                # Conteúdo HTML
            dest=pdf_file)           # Arquivo para guardar o PDF

    # verificar o estado de erro
    if pisa_status.err:
        print(f"ERRO ao gerar PDF com xhtml2pdf: {pisa_status.err}")
        return None
    return nome_arquivo_pdf
#
# FIM
#---------------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------
# Função que converte TEXTO em FALA
# 
def texto_para_audio(texto, idioma='pt-br'): # Experimente mudar o idioma aqui
    tts = gTTS(texto, lang=idioma)
    arquivo_audio = "audio.mp3"
    tts.save(arquivo_audio)
    return arquivo_audio
    # playsound.playsound("audio.mp3")
    
def falar(arq_path):
    playsound.playsound(arq_path)
#
# FIM
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
# START: TESTES
# 

testar = False
if testar:
    
    credentials         = os.getenv('CREDENTIALS')
    print(" \n Credenciais \n ")
    print(os.getenv('CRED'))
    print(" \n FIM \n ")
    
    s_key = gerar_signature_key()
    print(" \n SK \n ")
    print(s_key)
    print(" \n FIM \n ")
    
    
    chave = input(" \n Informe a chave:   ") 
    chave = gerar_hash(chave)
    print(" \n HASH \n ")
    print(chave)
    print(" \n FIM \n ")
    
    texto = f"""
     ```markdowns
## Inteligência Artificial (IA): Uma Visão Geral

**Inteligência Artificial (IA)** refere-se à capacidade de sistemas de computador de executar tarefas que normalmente exigiriam inteligência humana.  Em termos mais técnicos, IA envolve o desenvolvimento de algoritmos e modelos computacionais que permitem que máquinas aprendam, raciocinem, resolvam problemas, compreendam linguagem natural e até mesmo percebam o ambiente ao seu redor.

O objetivo principal da IA é criar sistemas que possam simular aspectos da inteligência humana, não necessariamente replicando a inteligência humana em si, mas sim emulando suas capacidades para realizar tarefas específicas de forma eficaz.

### Tipos de Inteligência Artificial

A IA pode ser categorizada de diversas maneiras, sendo uma das mais comuns a divisão baseada em sua **capacidade**:    

*   **IA Fraca ou Estreita (Narrow AI ou Weak AI):** Este é o tipo de IA mais comum atualmente. Ela é projetada e treinada para realizar tarefas **específicas** e bem definidas.  Embora possa ser extremamente eficiente em sua área de atuação, ela não possui inteligência geral ou consciência.

    *   **Exemplos:**
        *   **Sistemas de recomendação:** Netflix, Amazon, Spotify usam IA para recomendar filmes, produtos e músicas. 
        *   **Assistentes virtuais:** Siri, Alexa, Google Assistant conseguem responder perguntas, definir alarmes, tocar música, etc.
        *   **Filtros de spam:** Sistemas que identificam e filtram e-mails indesejados.
        *   **Carros autônomos (níveis mais baixos de autonomia):**  Sistemas de assistência ao motorista, como piloto 
automático adaptativo e assistência de estacionamento.
        *   **Chatbots de atendimento ao cliente:**  Sistemas que respondem a perguntas frequentes em sites e aplicativos.

*   **IA Forte ou Geral (General AI ou Strong AI):** Este tipo de IA, ainda **teórico**, teria a capacidade de entender, aprender e aplicar conhecimento em **qualquer** tarefa intelectual que um ser humano possa realizar.  Ela possuiria inteligência geral e adaptabilidade semelhantes às humanas. Atualmente, **não existe IA Forte**.

    *   **Exemplo hipotético:** Uma IA capaz de aprender a dirigir um carro, depois aprender a cozinhar, depois aprender a programar computadores, tudo com a mesma facilidade e adaptabilidade que um ser humano.

*   **Superinteligência (Superintelligence):**  Também **teórica**, a superinteligência excederia a inteligência humana em **todos** os aspectos, incluindo criatividade, resolução de problemas e sabedoria geral. É um conceito muito debatido e frequentemente explorado na ficção científica.

Além da categorização por capacidade, a IA também pode ser dividida por **funcionalidade**:

*   **IA Reativa (Reactive Machines):**  São as formas mais básicas de IA.  Elas reagem a estímulos presentes e **não possuem memória** ou capacidade de aprender com experiências passadas.

    *   **Exemplo:** Deep Blue, o computador da IBM que venceu Garry Kasparov no xadrez. Ele selecionava os melhores movimentos com base na posição atual do tabuleiro, sem histórico de jogos anteriores.

*   **IA com Memória Limitada (Limited Memory):** Estas IAs conseguem **utilizar experiências passadas** para tomar decisões. A memória é temporária e usada para melhorar o desempenho em tarefas específicas.

    *   **Exemplo:** A maioria dos carros autônomos atuais. Eles memorizam dados recentes como a velocidade de outros carros, a distância de faixas, etc., para tomar decisões de direção, mas essa memória é de curto prazo.

*   **IA com Teoria da Mente (Theory of Mind AI):** Este tipo de IA, **ainda em desenvolvimento**,  seria capaz de **entender emoções, crenças e intenções** de outros agentes (humanos ou outras IAs).  É um passo crucial para criar interações mais naturais e complexas entre humanos e máquinas.

*   **IA Autoconsciente (Self-Aware AI):**  Este é o tipo de IA mais avançado e **também puramente teórico**.  Uma IA autoconsciente teria **consciência de si mesma**, de sua própria existência e de seu estado interno.  Ainda não há consenso sobre se ou como isso seria possível.

### Aplicações da Inteligência Artificial

A IA já está presente em inúmeras áreas e continua a expandir seu alcance:

*   **Saúde:**
    *   Diagnóstico médico:  IA auxilia na análise de imagens médicas (raio-X, ressonância magnética) para detectar doenças.
    *   Descoberta de medicamentos: IA acelera o processo de identificação e desenvolvimento de novos fármacos.        
    *   Medicina personalizada: IA analisa dados genéticos e históricos de pacientes para tratamentos individualizados.    *   Cirurgia robótica assistida por IA.

*   **Finanças:**
    *   Detecção de fraudes: IA identifica padrões suspeitos em transações financeiras.
    *   Análise de risco de crédito:  IA avalia o risco de empréstimos com base em diversos dados.
    *   Robo-advisors:  Plataformas automatizadas que oferecem aconselhamento financeiro e gestão de investimentos.    
    *   Trading algorítmico: IA realiza negociações na bolsa de valores de forma rápida e automatizada.

*   **Transporte:**
    *   Carros autônomos: Desenvolvimento de veículos que dirigem sem intervenção humana (em diferentes níveis de autonomia).
    *   Otimização de rotas e logística: IA melhora a eficiência de sistemas de transporte e entrega.
    *   Gestão de tráfego inteligente: IA analisa dados de tráfego para otimizar semáforos e reduzir congestionamentos.
*   **Manufatura:**
    *   Robótica industrial avançada: Robôs com IA realizam tarefas complexas em linhas de produção.
    *   Manutenção preditiva: IA analisa dados de sensores para prever falhas em equipamentos e programar manutenção preventiva.
    *   Controle de qualidade automatizado: IA inspeciona produtos para identificar defeitos.

*   **Varejo e Atendimento ao Cliente:**
    *   Chatbots e assistentes virtuais para suporte ao cliente.
    *   Recomendação de produtos personalizada.
    *   Otimização de estoque e previsão de demanda.
    *   Análise de sentimentos de clientes em redes sociais para melhorar o atendimento.

*   **Entretenimento:**
    *   Sistemas de recomendação de conteúdo (música, filmes, séries).
    *   Geração de conteúdo criativo (música, arte, texto).
    *   Personagens de jogos mais inteligentes e realistas.

*   **Agricultura:**
    *   Agricultura de precisão: IA analisa dados de sensores e drones para otimizar o uso de recursos (água, fertilizantes).
    *   Detecção de pragas e doenças em plantações.
    *   Colheita automatizada com robôs.

### Breve História e Evolução da Inteligência Artificial

A história da IA pode ser dividida em algumas fases principais:

*   **Anos 1950: Nascimento da IA:** O termo "Inteligência Artificial" foi cunhado em 1956 na Conferência de Dartmouth.  Os primeiros programas de IA focavam em resolução de problemas, jogos (como xadrez) e linguagem natural, usando abordagens baseadas em regras e lógica simbólica.

*   **Anos 1960 e 1970: O Primeiro "Inverno da IA":**  Embora houvesse entusiasmo inicial, as expectativas não se concretizaram rapidamente. As limitações das abordagens iniciais e a falta de poder computacional levaram a uma diminuição do financiamento e do interesse pela área.

*   **Anos 1980: Sistemas Especialistas e a Retomada:**  Os sistemas especialistas, que aplicavam conhecimento específico de um domínio para resolver problemas, trouxeram um novo fôlego à IA. Houve um aumento do financiamento e do interesse comercial.

*   **Final dos anos 1980 e início dos anos 1990: O Segundo "Inverno da IA":**  As limitações dos sistemas especialistas, os altos custos e as dificuldades de manutenção levaram a um novo declínio do interesse e do financiamento.

*   **Anos 2000 até o Presente: O Renascimento da IA:**  O ressurgimento da IA é impulsionado por diversos fatores:    
    *   **Aumento Exponencial do Poder Computacional:**  Leis como a Lei de Moore proporcionaram poder de processamento muito maior e mais barato.
    *   **Disponibilidade de Grandes Volumes de Dados (Big Data):** A era da internet e da digitalização gerou enormes 
conjuntos de dados, cruciais para treinar modelos de Machine Learning.
    *   **Avanços em Algoritmos de Machine Learning e Deep Learning:**  Novas técnicas e algoritmos, especialmente redes neurais profundas (Deep Learning), revolucionaram áreas como visão computacional, processamento de linguagem natural 
e reconhecimento de voz.
    *   **Investimento Maciço:** Empresas de tecnologia e governos investem bilhões em pesquisa e desenvolvimento de IA.

Hoje, a IA está em constante evolução, com avanços rápidos e contínuos.  Estamos vendo progressos em direção a IAs mais sofisticadas, embora ainda estejamos longe da IA Forte ou Superinteligência teóricas. O campo da IA é dinâmico e promissor, com potencial para transformar muitos aspectos da nossa sociedade.

Espero que esta explicação tenha sido útil e clara! Se tiver mais perguntas, é só perguntar.
```
"""
    texto = limpa_texto(texto, '*', '')
    texto = limpa_texto(texto, '#', '')
    texto = limpa_texto(texto, '```markdowns', '')
    texto = limpa_texto(texto, '**', '')
    texto = limpa_texto(texto, '```', '')
    texto = limpa_texto(texto, '##', '')
    texto_para_audio(texto, 'pt-br')
    print(" \n ")

    # texto = converter_texto_para_html(texto)
    # print(" \n ")
    # texto = limpa_texto(texto,'*','')
    # texto = limpa_texto(texto,'#','')
    # print(texto)
    # print(" \n ")
    # print(converter_html_em_pdf_xhtml2pdf(texto))
    
    # converter_markdown_para_pdf(texto)
    # converter_markdown_para_pdf_2(texto, "relatorio_2.pdf")
    print(" \n FIM DA CONVERSÃO \n ")