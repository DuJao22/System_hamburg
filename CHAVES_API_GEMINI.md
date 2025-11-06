# 🔑 Como Adicionar Múltiplas Chaves API do Gemini

Este sistema suporta **rotação automática de até 5 chaves API** do Google Gemini!

## 📋 Como Funciona:

Quando uma chave atinge o limite de requisições, o sistema **automaticamente troca** para a próxima chave disponível.

## ✅ Como Configurar:

### 1. Gerar as Chaves API:
- Acesse: https://aistudio.google.com
- Crie 5 contas Google diferentes (ou use contas existentes)
- Em cada conta, gere uma chave API

### 2. Adicionar as Chaves no Replit:

No painel de **Secrets** do Replit, adicione as chaves com os seguintes nomes:

```
GEMINI_API_KEY_1 = sua_primeira_chave_aqui
GEMINI_API_KEY_2 = sua_segunda_chave_aqui
GEMINI_API_KEY_3 = sua_terceira_chave_aqui
GEMINI_API_KEY_4 = sua_quarta_chave_aqui
GEMINI_API_KEY_5 = sua_quinta_chave_aqui
```

**Importante:** A chave antiga `GEMINI_API_KEY` também funciona como fallback.

## 📊 Capacidade Total:

Com 5 chaves, você terá:
- **125 requisições por dia** (5 chaves × 25 requisições)
- **Rotação automática** quando uma chave atinge o limite

## 🔄 Como o Sistema Detecta Limites:

O sistema detecta automaticamente:
- ✅ Erros de quota excedida
- ✅ Rate limit (429)
- ✅ Resource exhausted
- ✅ Chaves inválidas

E **automaticamente tenta a próxima chave** disponível!

## 💡 Dicas:

1. Você pode adicionar de **1 até 5 chaves**
2. O sistema usa as chaves na ordem: KEY_1, KEY_2, KEY_3, KEY_4, KEY_5
3. Se todas as chaves atingirem o limite, o usuário recebe uma mensagem informando

## 🎯 Exemplo de Uso:

Não precisa fazer nada! O sistema é **totalmente automático**. Apenas adicione as chaves e pronto!
