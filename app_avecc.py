import streamlit as st
import pandas as pd
import markdownify
import banco as Consulta_Banco
import send_email as Correio

#------------------------------------------------------------------------------------------------------------------
# Funções
#
# Funções de exemplo (substitua pelas suas funções reais)

def obter_chamados_nao_categorizados():
    # Aqui você deve buscar os chamados não categorizados
    # Exemplo:
    
    # dados = {'ID': [1, 2, 3],
    #          'Título': ['Erro no sistema', 'Dúvida no módulo', 'Solicitação de acesso'],
    #          'Descrição': ['...', '...', '...']}
    dados = Consulta_Banco.listar_chamados_nao_categorizados('Open', '0000', '9999')    
    
    retorno = [pd.DataFrame(dados[1]), dados[0]]
    return retorno # pd.DataFrame(dados[1])

def gerar_relatorio_categorizacao(chamados):
    # Aqui você deve gerar o relatório de categorização
    # Exemplo:
    relatorio = ""
    for index, row in chamados.iterrows():
        relatorio += f"## Chamado {row['ID']}\n"
        relatorio += f"**Título:** {row['Título']}\n"
        relatorio += f"**Descrição:** {row['Descrição']}\n\n"
    return relatorio

def analisar_ticket(ticket_id):
    # Aqui você deve realizar a análise aprofundada do ticket
    # Exemplo:
    return f"Análise aprofundada do ticket {ticket_id}: ... (detalhes da análise)"

def enviar_email(email, conteudo):
    # Aqui você deve enviar o email com o conteúdo
    # Exemplo:
    print(f"Enviando email para: {email}\nConteúdo: {conteudo}")
#
# FIM
#-------------------------------------------------------------------------------------------------------------------

chamados_nao_categorizados  = pd.DataFrame()
analise_aprofundada         = ''

# Título da aplicação
st.title("Assistente Virtual Experimental Categorizador de Chamados")

# Botão Categorizar
if st.button("Listar Tickets Não Categorizados"):
    # Chama a função que lista os chamados não categorizados
    # Substitua por sua função real
    chamados_nao_categorizados = obter_chamados_nao_categorizados()

    # Exibe os chamados em uma tabela
    st.dataframe(chamados_nao_categorizados[0])
    
    # Relatório Análise Geral
    st.subheader("Relatório de Análise Geral")
    # st.write_stream()
    # markd_ = markdownify.markdownify(chamados_nao_categorizados[1])
    # st.write(chamados_nao_categorizados[1], unsafe_allow_html=True)
    st.markdown(chamados_nao_categorizados[1])
    # st.write(markd_)

# Grid Chamados (exibe a tabela retornada pelo botão Categorizar)
# O grid é atualizado automaticamente quando o botão é clicado

# # Botão Análise Geral
# if st.button("Análise Geral"):
#     # Chama a função que analisa a tabela e retorna o relatório
#     # Substitua por sua função real
#     relatorio_categorizacao = gerar_relatorio_categorizacao(chamados_nao_categorizados)
#     # Exibe o relatório
#     st.write(relatorio_categorizacao)

# Quadro Relatório (exibe o texto retornado pelo botão Categorização)
# O quadro é atualizado automaticamente quando o botão é clicado

# Caixa Ticket Alvo
ticket_alvo = st.text_input("Ticket Alvo")

# Botão Análise Aprofundada
if st.button("Análise Aprofundada"):
    # Chama a função que analisa o ticket e retorna o resultado
    # Substitua por sua função real
    # analise_aprofundada = analisar_ticket(ticket_alvo)
    analise_aprofundada = Consulta_Banco.analise_profunda_ticket_nao_categorizados('Open', ticket_alvo, ticket_alvo)

    # Exibe a análise aprofundada
    # st.write(analise_aprofundada)
    st.markdown(analise_aprofundada)

# Quadro Análise Aprofundada (exibe o texto retornado pelo botão Análise Aprofundada)
# O quadro é atualizado automaticamente quando o botão é clicado

# Caixa Email
email = st.text_input("Email")

# # Botão Enviar por Email
# if st.button("Enviar por Email"):
#     # Chama a função que envia a análise por email
#     # Substitua por sua função real
#     enviar_email(email, analise_aprofundada)

#     # Exibe mensagem de confirmação
#     st.write("Email enviado com sucesso!")

arquivos = ["arquivo_temporario.pdf", "lista_de_tickets_nao_categorizados.csv"]  # Lista de arquivos anexos
# Ou, para enviar apenas um arquivo:
# arquivos = ["/caminho/para/arquivo1.pdf"]

if st.button("Enviar por Email"):
    # Chama a função que envia a análise por email, com anexos
    if Correio.enviar_email(email, "Análise Aprofundada do Ticket", analise_aprofundada, arquivos):
        st.write("Email enviado com sucesso!")
    else:
        st.write("Falha ao enviar email. Verifique o console para mais detalhes.")