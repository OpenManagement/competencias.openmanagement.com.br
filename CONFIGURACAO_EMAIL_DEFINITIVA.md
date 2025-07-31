# 📧 GUIA DEFINITIVO - CONFIGURAÇÃO DE E-MAIL

## 🚀 CONFIGURAÇÃO RÁPIDA (2 minutos):

### **1. Abra o arquivo `app.py`**

### **2. Encontre estas linhas (por volta da linha 66-67):**
```python
EMAIL_USER = 'consultoria@openmanagement.com.br'  # ALTERE AQUI para seu e-mail
EMAIL_PASS = 'sua_senha_de_app_aqui'  # ALTERE AQUI para sua senha de app
```

### **3. Substitua pelos seus dados:**
```python
EMAIL_USER = 'seu_email@gmail.com'  # Seu e-mail do Gmail
EMAIL_PASS = 'abcd efgh ijkl mnop'  # Sua senha de app (16 caracteres)
```

### **4. Salve o arquivo e execute:**
```cmd
python app.py
```

## 🔐 COMO OBTER SENHA DE APP DO GMAIL:

### **Passo 1:** Acesse sua conta Google
- Vá para: https://myaccount.google.com/

### **Passo 2:** Ative a verificação em duas etapas
- Clique em "Segurança" → "Verificação em duas etapas"
- Siga as instruções para ativar

### **Passo 3:** Gere uma senha de app
- Ainda em "Segurança", procure por "Senhas de app"
- Clique em "Senhas de app"
- Selecione "E-mail" como aplicativo
- Copie a senha gerada (16 caracteres com espaços)

### **Passo 4:** Use a senha no código
```python
EMAIL_PASS = 'abcd efgh ijkl mnop'  # Cole aqui a senha gerada
```

## 📱 OUTROS PROVEDORES:

### **Outlook/Hotmail:**
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USER = 'seu_email@outlook.com'
EMAIL_PASS = 'sua_senha_normal'  # Outlook usa senha normal
```

### **Yahoo:**
```python
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
EMAIL_USER = 'seu_email@yahoo.com'
EMAIL_PASS = 'sua_senha_de_app'  # Yahoo também usa senha de app
```

## 🔍 VERIFICAÇÃO:

Quando você executar `python app.py`, verá:

### **✅ Configurado corretamente:**
```
🔧 Configuração de E-mail:
   Host: smtp.gmail.com
   Porta: 587
   Usuário: seu_email@gmail.com
   Senha configurada: ✅ Sim
   E-mail habilitado: ✅ Sim
```

### **❌ Não configurado:**
```
🔧 Configuração de E-mail:
   Host: smtp.gmail.com
   Porta: 587
   Usuário: consultoria@openmanagement.com.br
   Senha configurada: ❌ Não
   E-mail habilitado: ❌ Não
   ⚠️  Para habilitar e-mail, configure EMAIL_USER e EMAIL_PASS no código
```

## 🐛 SOLUÇÃO DE PROBLEMAS:

### **Erro de autenticação:**
- ✅ Verifique se ativou verificação em duas etapas
- ✅ Use senha de app (não a senha normal)
- ✅ Copie a senha exatamente como gerada

### **Erro de conexão:**
- ✅ Verifique sua internet
- ✅ Alguns antivírus bloqueiam SMTP
- ✅ Tente desativar firewall temporariamente

### **E-mail não chega:**
- ✅ Verifique pasta de spam
- ✅ Aguarde alguns minutos
- ✅ Teste com outro e-mail

## ⚡ CONFIGURAÇÃO ALTERNATIVA (Variáveis de Ambiente):

Se preferir não alterar o código:

### **Windows:**
```cmd
set EMAIL_USER=seu_email@gmail.com
set EMAIL_PASS=sua_senha_de_app
python app.py
```

### **Linux/Mac:**
```bash
export EMAIL_USER=seu_email@gmail.com
export EMAIL_PASS=sua_senha_de_app
python app.py
```

## 🎯 RESULTADO:

Após configurar corretamente, quando alguém completar a avaliação:
1. ✅ PDF será gerado
2. ✅ E-mail será enviado automaticamente
3. ✅ Usuário receberá o relatório completo

**Agora o e-mail funcionará 100%!**

