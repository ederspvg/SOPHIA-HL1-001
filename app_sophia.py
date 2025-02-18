import parametros_globais as OneRing

import time
import streamlit as st
import pandas as pd
import re
import markdownify
import banco as Consulta_Banco
import send_email as Correio
import utilitarios as Canivete
import os

# --- Inicialização do st.session_state ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False # Inicializa como não autenticado

if 'analise_aprofundada' not in st.session_state:
    st.session_state['analise_aprofundada'] = ''

if 'chamados_nao_categorizados' not in st.session_state:
    st.session_state['chamados_nao_categorizados'] = [pd.DataFrame(), '']

if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = ''

#--------------------------------------------------------------------------------------
# FUNÇÃO PARA OBTER CHAMADOS NÃO CATEGORIZADOS
#
def obter_chamados_nao_categorizados():
    dados = Consulta_Banco.listar_chamados_nao_categorizados('Open', '0000', '9999')
    retorno = [pd.DataFrame(dados[1]), dados[0]]
    return retorno

#----------------------------------------------------------------------
# CONFIGURAÇÃO DE LOGIN E SENHA A PARTIR DAS VARIÁVEIS DE AMBIENTE ---
# Versão simples. Futuramente melhorar para uma versão melhor
#
if OneRing.TESTE_LOCAL_:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='ambiente.env')
    LOGIN_CORRETO = os.getenv('LOGIN_DE_ACESSO') 
    SENHA_CORRETA = os.getenv('SENHA_DE_ACESSO') 
else:
    import streamlit as st
    LOGIN_CORRETO = st.secrets["LOGIN_DE_ACESSO"]
    SENHA_CORRETA = st.secrets["SENHA_DE_ACESSO"]

#----------------------------------------------------------------------------------------------------
# --- FORMULÁRIO DE LOGIN ---
#
if not st.session_state['autenticado']: # SE NÃO ESTÁ AUTENTICADO, MOSTRA O FORMULÁRIO DE LOGIN
    with st.form("login_form"):
        st.subheader("Login de Acesso")
        login_usuario = st.text_input("Login")
        senha_usuario = st.text_input("Senha", type="password")
        botao_login = st.form_submit_button("Entrar")

        if botao_login:
            if login_usuario == LOGIN_CORRETO and senha_usuario == SENHA_CORRETA: # VERIFICA AS CREDENCIAIS
                st.session_state['autenticado'] = True # Define como autenticado em caso de sucesso
                st.success("Login bem-sucedido!")
                time.sleep(1) # Pequeno delay para mostrar a mensagem de sucesso
                st.rerun() # Recarrega a aplicação para exibir o conteúdo autenticado
            else:
                st.error("Credenciais incorretas. Tente novamente.") # Mensagem de erro se as credenciais falharem
else: # SE JÁ ESTÁ AUTENTICADO, EXIBE O CONTEÚDO DA APLICAÇÃO
    # --- BOTÃO DE LOGOUT ---
    if st.sidebar.button("Logout"):
        st.session_state['autenticado'] = False # Define como não autenticado ao clicar em logout
        st.rerun() # Recarrega a aplicação para exibir o formulário de login novamente

    # --- Título da aplicação 
    st.title("Suporte Orientado Por Heurística Inteligente Artificial - Helpdesk Nível 1 - versão 001")
    st.subheader("Assistente Virtual Experimental Categorizador de Chamados")

    # --- ABAS DA APLICAÇÃO
    aba1, aba2 = st.tabs(["Listar Tickets Não Categorizados", "Análise Aprofundada de Ticket"])

    # --- Aba 1: Listar Tickets Não Categorizados
    with aba1:
        st.header("Listar Tickets Não Categorizados")
        st.markdown("Clique no botão abaixo para listar os tickets que ainda não foram categorizados.")

        if st.button("Listar Tickets Não Categorizados", key="botao_listar_nao_categorizados"):
            with st.spinner('Aguarde... Buscando chamados não categorizados...'):
                st.session_state['chamados_nao_categorizados'] = obter_chamados_nao_categorizados()

            st.dataframe(st.session_state['chamados_nao_categorizados'][0])

            st.subheader("Relatório de Análise Geral")
            st.session_state['analise_aprofundada'] =  Canivete.limpa_texto(st.session_state['chamados_nao_categorizados'][1], '```markdown', '')
            st.session_state['analise_aprofundada'] =  Canivete.limpa_texto(st.session_state['chamados_nao_categorizados'][1], '```', '')
            Canivete.converter_markdown_para_pdf(st.session_state['chamados_nao_categorizados'][1])
            st.markdown(f'<div style="word-wrap: break-word;">{st.session_state['chamados_nao_categorizados'][1]}</div>')

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

    # --- Aba 2: Análise Aprofundada de Ticket
    with aba2:
        st.header("Análise Aprofundada de Ticket")
        st.markdown("Insira o ID do ticket desejado para uma análise mais detalhada e envie os resultados por email.")

        ticket_alvo = st.text_input("Ticket Alvo", key="ticket_alvo_input")

        if st.button("Análise Aprofundada", key="botao_analise_aprofundada"):
            ticket_alvo_val = st.session_state['ticket_alvo_input']
            with st.spinner(f'Aguarde... Analisando ticket {ticket_alvo_val}...'):
                st.session_state['analise_aprofundada'] = Consulta_Banco.analise_profunda_ticket_nao_categorizados('Open', ticket_alvo_val, ticket_alvo_val)

            st.session_state['analise_aprofundada'] =  Canivete.limpa_texto(st.session_state['analise_aprofundada'], '```markdown', '')
            st.session_state['analise_aprofundada'] =  Canivete.limpa_texto(st.session_state['analise_aprofundada'], '```', '')
            Canivete.converter_markdown_para_pdf(st.session_state['analise_aprofundada'])
            st.markdown(f'<div style="word-wrap: break-word;">{st.session_state["analise_aprofundada"]}</div>')

        email = st.text_input("Email", key="email_input")

        if st.button("Enviar por Email", key="botao_enviar_email"):
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

            corpo_mail = Canivete.converter_texto_para_html(corpo_mail)
            arquivos = [Canivete.converter_html_em_pdf_xhtml2pdf(corpo_mail), st.session_state['audio_path'], "lista_de_tickets_nao_categorizados.csv"]
            if Correio.enviar_email_gmail_smtp(email, "Categorização de Chamados com IA", corpo_mail, arquivos):
                st.write("Email enviado com sucesso!")
                if st.button("Reproduzir Áudio", key="botao_reproduzir_audio"):
                    if st.session_state['audio_path']:
                        Canivete.falar(st.session_state['audio_path'])
                    else:
                        st.warning("Áudio ainda não foi gerado. Envie o email primeiro para gerar o áudio.")
            else:
                st.write("Falha ao enviar email. Verifique o console para mais detalhes.")