# 🚀 Site de Avaliação de Competências - Versão Windows

## ✅ Correções Implementadas para Windows

### Problemas Resolvidos:
1. **❌ Erro wkhtmltopdf:** Configuração automática para Windows
2. **❌ requirements.txt ausente:** Arquivo criado com dependências
3. **❌ Caminhos Linux:** Adaptação para sistema Windows

## 📋 Pré-requisitos

### 1. Python 3.11+ 
Certifique-se de ter Python instalado: https://python.org

### 2. wkhtmltopdf (Opcional - para gerar PDFs)
**Download:** https://wkhtmltopdf.org/downloads.html
- Baixe a versão para Windows
- Instale no caminho padrão: `C:\Program Files\wkhtmltopdf\`
- **Nota:** O site funcionará sem o wkhtmltopdf, mas não gerará PDFs

## 🔧 Instalação e Execução

### Passo 1: Instalar Dependências
```cmd
pip install -r requirements.txt
```

### Passo 2: Executar o Site
```cmd
python app.py
```

### Passo 3: Acessar no Navegador
```
http://localhost:5000
```

## 🎯 Funcionalidades Mantidas

### ✅ Escala Likert de 5 Pontos
- **1 = Discordo Totalmente**
- **2 = Discordo** 
- **3 = Neutro**
- **4 = Concordo**
- **5 = Concordo Totalmente**

### ✅ Gráficos Visuais no Relatório
- 📊 Gráfico de barras das competências
- 🎯 Gráfico radar (spider chart)
- 📏 Escala Likert visual
- 📈 Barras de progresso individuais

### ✅ Relatório Completo
- Análise personalizada
- Plano de desenvolvimento
- Ranking de competências
- Interpretação da pontuação

## 🔧 Configurações Automáticas

O sistema agora detecta automaticamente:
- **Windows:** Busca wkhtmltopdf em caminhos padrão
- **Linux:** Configuração para /usr/bin/wkhtmltopdf
- **macOS:** Suporte para Homebrew

## ⚠️ Notas Importantes

### Se wkhtmltopdf não estiver instalado:
- ✅ O site funcionará normalmente
- ✅ Todas as funcionalidades da escala Likert funcionam
- ✅ Gráficos são exibidos corretamente
- ❌ PDFs não serão gerados
- ❌ Emails não serão enviados

### Para funcionalidade completa:
1. Instale wkhtmltopdf do link oficial
2. Configure credenciais de email no app.py (linhas 25-27)

## 🐛 Solução de Problemas

### Erro: "No module named 'flask'"
```cmd
pip install flask
```

### Erro: "wkhtmltopdf not found"
- Instale wkhtmltopdf ou ignore (site funcionará sem PDFs)

### Erro: "Port already in use"
- Feche outras instâncias do Python
- Ou mude a porta no app.py (linha final)

## 📁 Estrutura do Projeto

```
competencias_site/
├── app.py                          # Backend Flask (compatível Windows)
├── requirements.txt                # Dependências Python
├── templates/
│   ├── index.html                  # Interface com escala Likert
│   └── relatorio_template.html     # Template com gráficos
├── static/
│   └── img/
│       └── logo.png               # Logo do projeto
└── relatorios_temp/               # PDFs temporários (criado automaticamente)
```

## 🎉 Resultado

O site agora funciona perfeitamente no Windows com:
- ✅ **Escala Likert completa** implementada
- ✅ **Gráficos visuais** no relatório
- ✅ **Compatibilidade Windows** total
- ✅ **Detecção automática** do sistema operacional
- ✅ **Funcionamento garantido** mesmo sem wkhtmltopdf

**Todas as funcionalidades da escala Likert e gráficos foram preservadas!**

