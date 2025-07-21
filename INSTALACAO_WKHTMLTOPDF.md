# 🔧 Guia de Instalação do wkhtmltopdf no Windows

## 📥 Download e Instalação

### Passo 1: Download
1. Acesse: https://wkhtmltopdf.org/downloads.html
2. Clique em **"Windows"**
3. Baixe a versão **64-bit** (recomendado) ou **32-bit**

### Passo 2: Instalação
1. Execute o arquivo baixado (.exe)
2. Siga o assistente de instalação
3. **Importante:** Instale no caminho padrão: `C:\Program Files\wkhtmltopdf\`

### Passo 3: Verificação
Abra o Prompt de Comando e teste:
```cmd
"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe" --version
```

## 🎯 Caminhos Suportados pelo Sistema

O sistema busca automaticamente o wkhtmltopdf nos seguintes locais:
1. `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`
2. `C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe`
3. `wkhtmltopdf.exe` (se estiver no PATH do sistema)

## ⚠️ Problemas Comuns

### "Arquivo não encontrado"
- Certifique-se de instalar no caminho padrão
- Verifique se o arquivo existe em: `C:\Program Files\wkhtmltopdf\bin\`

### "Acesso negado"
- Execute o Prompt de Comando como Administrador
- Ou instale em uma pasta com permissões de usuário

### "Versão incompatível"
- Baixe a versão mais recente do site oficial
- Certifique-se de baixar a versão correta (32-bit ou 64-bit)

## 🔄 Alternativa: Adicionar ao PATH

Se preferir, pode adicionar ao PATH do Windows:
1. Copie o caminho: `C:\Program Files\wkhtmltopdf\bin`
2. Vá em **Configurações > Sistema > Sobre > Configurações avançadas do sistema**
3. Clique em **Variáveis de Ambiente**
4. Edite a variável **PATH**
5. Adicione o caminho copiado

## ✅ Teste Final

Após a instalação, execute o site:
```cmd
python app.py
```

Se aparecer a mensagem:
```
✅ wkhtmltopdf configurado com sucesso!
```

Significa que está funcionando corretamente!

## 🚫 Funcionamento Sem wkhtmltopdf

**O site funciona normalmente sem o wkhtmltopdf!**
- ✅ Todas as funcionalidades da escala Likert
- ✅ Gráficos visuais no navegador
- ✅ Cálculos e análises
- ❌ Apenas não gera PDFs para download

Se aparecer:
```
⚠️ AVISO: wkhtmltopdf não encontrado!
📄 O site funcionará, mas PDFs não serão gerados.
```

Isso é normal e o site funcionará perfeitamente!

