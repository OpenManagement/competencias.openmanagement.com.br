# 🔧 GUIA COMPLETO - CONFIGURAÇÃO ZOHO MAIL

## ❌ **PROBLEMA ATUAL:**
```
❌ Erro de autenticação SMTP: (535, b'Authentication Failed')
```

## ✅ **SOLUÇÃO PASSO A PASSO:**

### **1. Configurar Senha de App no Zoho**

#### **Passo 1: Acessar Configurações de Segurança**
- Acesse: https://accounts.zoho.com/home#security/app-passwords
- Faça login com sua conta Zoho

#### **Passo 2: Ativar Autenticação de 2 Fatores (se não estiver ativo)**
- Vá em "Two-Factor Authentication"
- Ative usando SMS ou app autenticador
- **OBRIGATÓRIO:** Zoho exige 2FA para senhas de app

#### **Passo 3: Gerar Senha de App**
- Clique em "Generate App Password"
- Nome da aplicação: "Site Competências" ou similar
- Selecione: "Mail"
- Clique em "Generate"
- **COPIE A SENHA GERADA** (aparece apenas uma vez)

### **2. Configurar no Código**

#### **Abra o arquivo `app.py` e altere as linhas 66-67:**

```python
# ANTES (não funciona):
EMAIL_USER = 'consultoria@openmanagement.com.br'
EMAIL_PASS = 'sua_senha_de_app_aqui'

# DEPOIS (funcionará):
EMAIL_USER = 'consultoria@openmanagement.com.br'
EMAIL_PASS = 'COLE_AQUI_A_SENHA_DE_APP_GERADA'
```

### **3. Configurações Zoho Corretas**

```python
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 587
EMAIL_USER = 'consultoria@openmanagement.com.br'
EMAIL_PASS = 'sua_senha_de_app_do_zoho'  # ← SENHA DE APP, NÃO A SENHA NORMAL
```

### **4. Testar**

```cmd
python app.py
# Deve aparecer: "E-mail habilitado: ✅ Sim"
# Teste enviando uma avaliação
```

## 🔍 **DIAGNÓSTICO DE PROBLEMAS:**

### **Se ainda der erro 535:**
- ✅ Verificar se 2FA está ativo
- ✅ Gerar nova senha de app
- ✅ Copiar senha exatamente (sem espaços)
- ✅ Verificar se o e-mail está correto

### **Se der erro de conexão:**
- ✅ Verificar internet
- ✅ Verificar firewall/antivírus
- ✅ Tentar porta 465 com SSL

## 🎯 **CONFIGURAÇÃO ALTERNATIVA (Porta 465):**

Se a porta 587 não funcionar, tente:

```python
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 465
# E modificar a função para usar SSL em vez de TLS
```

## 📞 **SUPORTE:**

Se continuar com problemas:
1. Verificar status do Zoho Mail
2. Contatar suporte Zoho
3. Considerar usar Gmail como alternativa

**Após configurar corretamente, o e-mail funcionará 100%!**

