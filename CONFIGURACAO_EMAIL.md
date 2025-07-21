# 📧 Configuração de E-mail para o Site de Competências

## 🔧 Como Configurar o Envio de E-mail:

### **Opção 1: Variáveis de Ambiente (Recomendado)**

Crie um arquivo `.env` na pasta do projeto:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASS=sua_senha_de_app
```

### **Opção 2: Configuração Direta no Windows**

Execute antes de iniciar o servidor:
```cmd
set EMAIL_HOST=smtp.gmail.com
set EMAIL_PORT=587
set EMAIL_USER=seu_email@gmail.com
set EMAIL_PASS=sua_senha_de_app
python app.py
```

### **Opção 3: Configuração Direta no Linux/Mac**

```bash
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USER=seu_email@gmail.com
export EMAIL_PASS=sua_senha_de_app
python app.py
```

## 🔐 Como Obter Senha de App do Gmail:

1. Acesse sua conta Google
2. Vá em "Gerenciar sua Conta Google"
3. Clique em "Segurança"
4. Ative "Verificação em duas etapas"
5. Procure por "Senhas de app"
6. Gere uma senha para "E-mail"
7. Use essa senha no EMAIL_PASS

## ⚙️ Outros Provedores de E-mail:

### **Outlook/Hotmail:**
```
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
```

### **Yahoo:**
```
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
```

## 🚀 Funcionamento:

- **COM configuração:** Envia PDF por e-mail
- **SEM configuração:** Mostra relatório na tela
- **Erro de envio:** Gera PDF mas informa erro

## ✅ Teste de Configuração:

O sistema detecta automaticamente se o e-mail está configurado e informa o status no resultado da avaliação.

