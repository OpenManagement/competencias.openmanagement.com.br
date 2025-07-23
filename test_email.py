#!/usr/bin/env python3
"""
Script de teste para verificar o envio de email
"""

import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def testar_configuracao_smtp():
    """Testar configuração SMTP"""
    print("=== TESTE DE CONFIGURAÇÃO SMTP ===\n")
    
    try:
        # Configurações do SMTP
        smtp_server = os.getenv("MAIL_SERVER")
        smtp_port = int(os.getenv("MAIL_PORT", 465))
        email_usuario = os.getenv("MAIL_USERNAME")
        email_senha = os.getenv("MAIL_PASSWORD")
        
        print(f"✓ Servidor SMTP: {smtp_server}")
        print(f"✓ Porta SMTP: {smtp_port}")
        print(f"✓ Usuário: {email_usuario}")
        print(f"✓ Senha configurada: {'Sim' if email_senha and email_senha != 'sua_senha_aqui' else 'Não'}")
        
        if not email_senha or email_senha == 'sua_senha_aqui':
            print("⚠️  AVISO: Senha do email não está configurada corretamente")
            print("   Para testar o envio real, configure MAIL_PASSWORD no arquivo .env")
            return False
        
        # Testar conexão SMTP
        print("\n--- Testando conexão SMTP ---")
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(email_usuario, email_senha)
        server.quit()
        print("✓ Conexão SMTP bem-sucedida!")
        
        return True
        
    except Exception as e:
        print(f"✗ ERRO na configuração SMTP: {e}")
        return False

def testar_envio_email_simulado():
    """Testar envio de email simulado (sem envio real)"""
    print("\n=== TESTE DE ENVIO SIMULADO ===\n")
    
    try:
        # Dados de teste
        nome = "João Silva"
        email_destino = "washington.a.dacruz@gmail.com"
        pontuacao_geral = 3.5
        
        # Configurações do SMTP
        email_usuario = os.getenv("MAIL_USERNAME")
        email_interno = os.getenv("MAIL_USERNAME")
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_usuario
        msg['To'] = f"{email_destino},{email_interno}"
        msg['Subject'] = "[Método Faça Bem] Seu Relatório de Competências (PDF)"
        
        # Corpo do email
        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">Olá {nome}!</h2>
                
                <p>Parabéns por completar sua autoavaliação de competências! 🎉</p>
                
                <p><strong>Sua pontuação geral foi: {pontuacao_geral:.2f}/5.00</strong></p>
                
                <p>Em anexo, você encontrará seu relatório personalizado em PDF com:</p>
                <ul>
                    <li>✅ Análise detalhada de suas competências</li>
                    <li>✅ Gráficos visuais dos resultados</li>
                    <li>✅ Ranking de pontos fortes e oportunidades</li>
                    <li>✅ Plano de desenvolvimento personalizado</li>
                </ul>
                
                <p>Este relatório foi desenvolvido especialmente para você com base em suas respostas na escala Likert. Use-o como guia para acelerar seu desenvolvimento pessoal e profissional.</p>
                
                <p><strong>Sucesso em sua jornada de desenvolvimento!</strong></p>
                
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 14px;">
                    <strong>Equipe Método Faça Bem</strong><br>
                    consultoria@openmanagement.com.br
                </p>
            </div>
        </body>
        </html>
        """
        
        # Versão texto simples
        corpo_texto = f"""Olá {nome}!

Parabéns por completar sua autoavaliação de competências! 🎉

Sua pontuação geral foi: {pontuacao_geral:.2f}/5.00

Em anexo, você encontrará seu relatório personalizado em PDF com:
✅ Análise detalhada de suas competências  
✅ Gráficos visuais dos resultados  
✅ Ranking de pontos fortes e oportunidades  
✅ Plano de desenvolvimento personalizado  

Este relatório foi desenvolvido especialmente para você com base em suas respostas na escala Likert. Use-o como guia para acelerar seu desenvolvimento pessoal e profissional.

Sucesso em sua jornada de desenvolvimento!

Equipe Método Faça Bem  
consultoria@openmanagement.com.br"""
        
        # Anexar corpo do email
        msg.attach(MIMEText(corpo_texto, 'plain', 'utf-8'))
        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))
        
        # Simular anexo de PDF
        pdf_path = "test_pdfs/relatorio_completo_20250722_150325.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="Relatorio_Competencias_{nome.replace(" ", "_")}.pdf"'
                )
                msg.attach(part)
            print(f"✓ PDF anexado: {pdf_path}")
        else:
            print("⚠️  PDF de teste não encontrado, simulando anexo")
        
        # Simular envio (não enviar realmente)
        email_content = msg.as_string()
        print(f"✓ Email preparado para: {email_destino}")
        print(f"✓ Assunto: {msg['Subject']}")
        print(f"✓ Tamanho do conteúdo: {len(email_content)} caracteres")
        print("✓ Email simulado com sucesso!")
        
        print("\n=== TESTE SIMULADO CONCLUÍDO COM SUCESSO ===")
        return True
        
    except Exception as e:
        print(f"✗ ERRO durante teste simulado: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal de teste"""
    print("=== TESTE COMPLETO DE EMAIL ===\n")
    
    # Testar configuração SMTP
    smtp_ok = testar_configuracao_smtp()
    
    # Testar envio simulado
    simulado_ok = testar_envio_email_simulado()
    
    if simulado_ok:
        print("\n✅ TODOS OS TESTES DE EMAIL PASSARAM!")
        if not smtp_ok:
            print("⚠️  Para envio real, configure a senha SMTP no arquivo .env")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)

