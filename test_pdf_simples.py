#!/usr/bin/env python3
"""
Teste simples de geração de PDF
"""

import os
import pdfkit
from datetime import datetime

def testar_pdf_simples():
    """Testar geração de PDF com HTML simples"""
    print("=== TESTE SIMPLES DE PDF ===\n")
    
    try:
        # HTML simples para teste
        html_simples = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Teste PDF</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #4CAF50; }
                .info { background: #f0f0f0; padding: 20px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>Relatório de Teste</h1>
            <div class="info">
                <p><strong>Nome:</strong> João Silva</p>
                <p><strong>Data:</strong> """ + datetime.now().strftime('%d/%m/%Y') + """</p>
                <p><strong>Pontuação:</strong> 3.5/5.0</p>
            </div>
            <h2>Competências</h2>
            <ul>
                <li>Comunicação: 4.0</li>
                <li>Organização: 3.5</li>
                <li>Liderança: 3.0</li>
            </ul>
        </body>
        </html>
        """
        
        print("✓ HTML simples criado")
        
        # Criar diretório para PDFs de teste
        os.makedirs('test_pdfs', exist_ok=True)
        
        # Nome do arquivo PDF
        pdf_filename = f"teste_simples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join('test_pdfs', pdf_filename)
        
        # Opções básicas para PDF
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'quiet': ''
        }
        
        print("✓ Opções básicas configuradas")
        
        # Gerar PDF
        pdfkit.from_string(html_simples, pdf_path, options=options)
        
        # Verificar se o arquivo foi criado
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            tamanho = os.path.getsize(pdf_path)
            print(f"✓ PDF simples gerado com sucesso: {pdf_path} ({tamanho} bytes)")
            return True
        else:
            print("✗ PDF não foi criado ou está vazio")
            return False
            
    except Exception as e:
        print(f"✗ ERRO durante teste simples: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_pdf_simples()
    if sucesso:
        print("\n=== TESTE SIMPLES CONCLUÍDO COM SUCESSO ===")
    else:
        print("\n=== TESTE SIMPLES FALHOU ===")

