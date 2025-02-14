import time
import streamlit as st
import pandas as pd
import re
import markdownify
import banco as Consulta_Banco
import send_email as Correio
import utilitarios as Canivete

# Inicializar analise_aprofundada no st.session_state se não existir
if 'analise_aprofundada' not in st.session_state:
    st.session_state['analise_aprofundada'] = ''

# Inicializar chamados_nao_categorizados no st.session_state se não existir
if 'chamados_nao_categorizados' not in st.session_state:
    st.session_state['chamados_nao_categorizados'] = [pd.DataFrame(), '']
    
# Inicializar audio_path no st.session_state se não existir
if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = ''

#------------------------------------------------------------------------------------------------------------------
# Funções de suporte - acho que vou precisar de apenas uma
#
def obter_chamados_nao_categorizados():
    dados = Consulta_Banco.listar_chamados_nao_categorizados('Open', '0000', '9999')
    retorno = [pd.DataFrame(dados[1]), dados[0]]
    return retorno
#
# FIM
#-------------------------------------------------------------------------------------------------------------------

chamados_nao_categorizados = pd.DataFrame()

# Título da aplicação
st.title("Assistente Virtual Experimental Categorizador de Chamados")

# Criando as abas que vou usar
aba1, aba2 = st.tabs(["Listar Tickets Não Categorizados", "Análise Aprofundada de Ticket"])

# Aba 1: Listar Tickets Não Categorizados
with aba1:
    st.header("Listar Tickets Não Categorizados")
    st.markdown("Clique no botão abaixo para listar os tickets que ainda não foram categorizados.")

    # Botão Categorizar (dentro da aba 1)
    if st.button("Listar Tickets Não Categorizados", key="botao_listar_nao_categorizados"): 
        # Chama a função que lista os chamados não categorizados
        #
        with st.spinner('Aguarde... Buscando chamados não categorizados...'): 
            st.session_state['chamados_nao_categorizados'] = obter_chamados_nao_categorizados()

        # Exibe os chamados em uma tabela
        st.dataframe(st.session_state['chamados_nao_categorizados'][0])

        # Relatório Análise Geral
        st.subheader("Relatório de Análise Geral")
        st.session_state['analise_aprofundada'] =  Canivete.limpa_texto(st.session_state['chamados_nao_categorizados'][1], '```markdown', '')
        st.session_state['analise_aprofundada'] =  Canivete.limpa_texto(st.session_state['chamados_nao_categorizados'][1], '```', '')
        Canivete.converter_markdown_para_pdf(st.session_state['chamados_nao_categorizados'][1])
        st.markdown(f'<div style="word-wrap: break-word;">{st.session_state['chamados_nao_categorizados'][1]}</div>')

    # Caixa Email (dentro da aba 1)
    email_1 = st.text_input("Email", key="email_input_aba_1") 

    if st.button("Enviar Categorização por Email", key="botao_enviar_email_aba_1"):
        corpo_mail_1 = st.session_state['chamados_nao_categorizados'][1]
        corpo_mail_1 = Canivete.limpa_texto(corpo_mail_1, '```markdown', '')
        corpo_mail_1 = Canivete.limpa_texto(corpo_mail_1, '```', '')
        corpo_mail_1 = Canivete.converter_texto_para_html(corpo_mail_1)
        arquivos = [Canivete.converter_html_em_pdf_xhtml2pdf(corpo_mail_1), "lista_de_tickets_nao_categorizados.csv"] 
        if Correio.enviar_email_gmail_smtp(email_1, "Categorização de Chamados com IA - Ordem de Priorização", corpo_mail_1, arquivos): 
            st.write("Email enviado com sucesso!")
        else:
            st.write("Falha ao enviar email. Verifique o console para mais detalhes.")


# Aba 2: Análise Aprofundada de Ticket
with aba2:
    st.header("Análise Aprofundada de Ticket")
    st.markdown("Insira o ID do ticket desejado para uma análise mais detalhada e envie os resultados por email.")

    # Caixa Ticket Alvo (dentro da aba 2)
    ticket_alvo = st.text_input("Ticket Alvo", key="ticket_alvo_input") 

    # Botão Análise Aprofundada (dentro da aba 2)
    if st.button("Análise Aprofundada", key="botao_analise_aprofundada"): 
        # Chama a função que analisa o ticket e retorna o resultado
        ticket_alvo_val = st.session_state['ticket_alvo_input'] 
        with st.spinner(f'Aguarde... Analisando ticket {ticket_alvo_val}...'): 
            st.session_state['analise_aprofundada'] = Consulta_Banco.analise_profunda_ticket_nao_categorizados('Open', ticket_alvo_val, ticket_alvo_val) # SALVA NO st.session_state

        st.session_state['analise_aprofundada'] =  Canivete.limpa_texto(st.session_state['analise_aprofundada'], '```markdown', '')
        st.session_state['analise_aprofundada'] =  Canivete.limpa_texto(st.session_state['analise_aprofundada'], '```', '')
        Canivete.converter_markdown_para_pdf(st.session_state['analise_aprofundada'])
        # Exibe a análise aprofundada
        st.markdown(f'<div style="word-wrap: break-word;">{st.session_state["analise_aprofundada"]}</div>')
        
        # # Botão Reproduzir Áudio
        # if st.button("Reproduzir Áudio", key="botao_reproduzir_audio"):
        #     if st.session_state['audio_path']: # Verificando se o audio_path foi gerado
        #         Canivete.falar(st.session_state['audio_path'])
        #     else:
        #         st.warning("Áudio ainda não foi gerado. Envie o email primeiro para gerar o áudio.")

    # Caixa Email (dentro da aba 2)
    email = st.text_input("Email", key="email_input")

    if st.button("Enviar por Email", key="botao_enviar_email"): 
        # Chama a função que envia a análise por email, com anexos
        corpo_mail = st.session_state['analise_aprofundada']
        corpo_mail = Canivete.limpa_texto(corpo_mail, '```markdown', '')
        corpo_mail = Canivete.limpa_texto(corpo_mail, '```', '')
        texto_audio = corpo_mail
        texto_audio = Canivete.limpa_texto(texto_audio, '*', '')
        texto_audio = Canivete.limpa_texto(texto_audio, '**', '')
        texto_audio = Canivete.limpa_texto(texto_audio, '#', '')
        texto_audio = Canivete.limpa_texto(texto_audio, '##', '')
        
        with st.spinner('Aguarde... Gerando arquivo de áudio...'):
            st.session_state['audio_path'] = Canivete.texto_para_audio(texto_audio)

        # audio_path = Canivete.texto_para_audio(texto_audio)
        # Canivete.falar(audio_path)
        
        corpo_mail = Canivete.converter_texto_para_html(corpo_mail)
        arquivos = [Canivete.converter_html_em_pdf_xhtml2pdf(corpo_mail), st.session_state['audio_path'], "lista_de_tickets_nao_categorizados.csv"]
        if Correio.enviar_email_gmail_smtp(email, "Categorização de Chamados com IA", corpo_mail, arquivos): 
            st.write("Email enviado com sucesso!")
            # Botão Reproduzir Áudio
            if st.button("Reproduzir Áudio", key="botao_reproduzir_audio"):
                if st.session_state['audio_path']: # Verificando se o audio_path foi gerado
                    Canivete.falar(st.session_state['audio_path'])
                else:
                    st.warning("Áudio ainda não foi gerado. Envie o email primeiro para gerar o áudio.")
        else:
            st.write("Falha ao enviar email. Verifique o console para mais detalhes.")