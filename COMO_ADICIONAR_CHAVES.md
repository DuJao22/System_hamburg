# 📝 Como Adicionar Suas 5 Chaves API do Gemini

## ✅ Arquivo Criado: `gemini_keys.py`

Este arquivo já está criado e configurado! Agora é só você adicionar suas chaves.

---

## 🔧 PASSO A PASSO:

### 1️⃣ Abra o arquivo `gemini_keys.py`

### 2️⃣ Você verá esta estrutura:

```python
GEMINI_API_KEYS = [
    "AIzaSyDmUgmObZ_HsSe9BHdJaUbqgdSud4Qrl6Y",  # Chave 1 (já configurada)
    "",  # Cole a Chave 2 aqui
    "",  # Cole a Chave 3 aqui
    "",  # Cole a Chave 4 aqui
    ""   # Cole a Chave 5 aqui
]
```

### 3️⃣ Substitua as aspas vazias pelas suas chaves API:

**Exemplo:**
```python
GEMINI_API_KEYS = [
    "AIzaSyDmUgmObZ_HsSe9BHdJaUbqgdSud4Qrl6Y",
    "AIzaSyBXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "AIzaSyCYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",
    "AIzaSyDZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
    "AIzaSyEWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"
]
```

### 4️⃣ Salve o arquivo

### 5️⃣ Pronto! O sistema automaticamente vai usar as chaves 🎉

---

## 📊 Como Funciona:

✅ O sistema **tenta usar a primeira chave** da lista  
⚠️ Se ela atingir o limite, **automaticamente usa a segunda**  
⚠️ Se a segunda atingir o limite, **usa a terceira**  
⚠️ E assim por diante até a quinta chave!

---

## 🎯 Capacidade Total:

| Chaves | Mensagens/Dia |
|--------|---------------|
| 1 chave | 25 mensagens |
| 2 chaves | 50 mensagens |
| 3 chaves | 75 mensagens |
| 4 chaves | 100 mensagens |
| 5 chaves | **125 mensagens** |

---

## 💡 Dicas Importantes:

1. **Não remova as aspas** - sempre mantenha as chaves entre aspas duplas `""`
2. **Mantenha as vírgulas** entre as chaves
3. **Não precisa reiniciar** - o sistema já está configurado
4. Você pode adicionar **1 até 5 chaves**, não precisa ser exatamente 5

---

## ⚙️ Verificando se está funcionando:

Depois de adicionar as chaves, teste o chatbot. No console você verá:

```
📋 Carregadas 5 chaves do arquivo gemini_keys.py
```

Se aparecer isso, está tudo certo! ✅

---

**Dúvidas?** É só perguntar! 😊
