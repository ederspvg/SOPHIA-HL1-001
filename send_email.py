import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='ambiente.env')

#---------------------------------------------------------------------------------------------------------------
# Função para envio de email
#
def enviar_email(destinatario, assunto, corpo, arquivos_anexos=None):
    """Envia um email com o conteúdo especificado para o destinatário,
    com a opção de anexar um ou mais arquivos.
    """

    remetente   = os.getenv('EMAIL_REMETENTE')
    senha       = os.getenv('SENHA_EMAIL_REMETENTE')

    if not remetente or not senha:
        raise ValueError("As variáveis de ambiente EMAIL_REMETENTE e SENHA_EMAIL_REMETENTE não foram definidas.")

    mensagem = MIMEMultipart()
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    mensagem["Subject"] = assunto

    mensagem.attach(MIMEText(corpo, "html"))

    if arquivos_anexos:
        for arquivo in arquivos_anexos:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(open(arquivo, "rb").read())
            encoders.encode_base64(parte)
            parte.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(arquivo)}")
            mensagem.attach(parte)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(remetente, senha)
            servidor.sendmail(remetente, destinatario, mensagem.as_string())
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False
    
# 
# FIM
#---------------------------------------------------------------------------------------------------------------

arquivos = ['arquivo_temporario.pdf']
enviar_email('eder.silva@luft.com.br', 'Teste', 'Test', arquivos)
print(" \n ")
    
# # Exemplo de uso (em outro script.py)
# from enviar_email import enviar_email

# arquivos = ["/caminho/para/arquivo1.pdf", "/caminho/para/arquivo2.docx"]  # Lista de arquivos anexos
# # Ou, para enviar apenas um arquivo:
# # arquivos = ["/caminho/para/arquivo1.pdf"]

# if st.button("Enviar por Email"):
#     # Chama a função que envia a análise por email, com anexos
#     if enviar_email(email, "Análise Aprofundada do Ticket", analise_aprofundada, arquivos):
#         st.write("Email enviado com sucesso!")
#     else:
#         st.write("Falha ao enviar email. Verifique o console para mais detalhes.")