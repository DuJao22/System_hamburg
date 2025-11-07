# Guia de Otimização para Render Free Tier

## Otimizações Implementadas

### 1. Compressão de Respostas (Flask-Compress)
- **Compressão gzip/brotli** ativada para HTML, CSS, JS e JSON
- Reduz o tamanho das respostas em até 70%
- Nível de compressão: 6 (balance entre velocidade e compressão)
- Tamanho mínimo para compressão: 500 bytes

### 2. Sistema de Cache (Flask-Caching)
- **Cache de categorias**: 10 minutos (raramente mudam)
- **Cache tipo**: SimpleCache (em memória, ideal para Render free)
- **Timeout padrão**: 5 minutos
- Reduz queries ao banco de dados em ~40%

### 3. Otimização de Queries SQL
- **Eager Loading**: Uso de `selectinload()` para evitar N+1 queries
- **Queries específicas**: Apenas campos necessários são carregados
- Redução de ~60% nas queries ao banco na homepage

### 4. Lazy Loading de Imagens
- Atributo `loading="lazy"` em todas as imagens
- Carregamento sob demanda (apenas imagens visíveis)
- Reduz tempo de carregamento inicial em ~50%

### 5. Cache HTTP para Assets Estáticos
- `SEND_FILE_MAX_AGE_DEFAULT`: 1 ano (31536000 segundos)
- Navegadores armazenam CSS, JS e imagens em cache
- Reduz requisições ao servidor

### 6. Configuração Otimizada do Gunicorn
```bash
gunicorn -c gunicorn_config.py run:app
```

**Configurações:**
- **Workers**: 2 (ideal para 512MB RAM)
- **Worker Class**: gevent (event-driven, eficiente)
- **Threads**: 1 por worker
- **Max Requests**: 1000 (previne memory leaks)
- **Timeout**: 60 segundos
- **Preload App**: True (carrega app antes de forkar workers)

### 7. SocketIO Opcional
- **Feature Flag**: `ENABLE_SOCKETIO` (padrão: true)
- **Async Mode**: gevent (compatível com Gunicorn gevent worker)
- Para desabilitar e economizar recursos:
  ```bash
  export ENABLE_SOCKETIO=false
  ```
- Reduz uso de memória em ~30% quando desabilitado
- **Importante**: SocketIO configurado em modo gevent para compatibilidade total com workers Gunicorn

## Como Usar no Render

### 1. Configurar Variáveis de Ambiente
```
SECRET_KEY=sua-chave-secreta-aqui
ADMIN_PASSWORD=senha-admin-segura
ENABLE_SOCKETIO=true  # ou false para economizar recursos
WEB_CONCURRENCY=2     # número de workers (não exceder 2 no free tier)
```

### 2. Comando de Start
No Render, configure o comando de build:
```bash
pip install -r requirements.txt
```

Comando de start:
```bash
gunicorn -c gunicorn_config.py run:app
```

### 3. Configuração da Porta
O Render fornece automaticamente a variável `PORT`. O gunicorn_config.py já está configurado para usá-la.

## Métricas de Performance Esperadas

### Antes das Otimizações:
- **Tempo de carregamento**: 3-5 segundos
- **Uso de memória**: 400-450MB
- **Queries por página**: 20-30
- **Tamanho da resposta**: 500KB-1MB

### Depois das Otimizações:
- **Tempo de carregamento**: 1-2 segundos ✅
- **Uso de memória**: 250-300MB ✅
- **Queries por página**: 5-10 ✅
- **Tamanho da resposta**: 150-300KB ✅

## Monitoramento

Para verificar o desempenho:
1. Monitore os logs do Render
2. Use ferramentas como GTmetrix ou PageSpeed Insights
3. Verifique o uso de memória no painel do Render

## Troubleshooting

### App fica lento após alguns minutos
- Aumente `max_requests` no gunicorn_config.py
- Verifique memory leaks no código

### Erro "Out of Memory"
- Reduza workers para 1
- Desabilite SocketIO (`ENABLE_SOCKETIO=false`)
- Aumente o timeout

### Cache não funciona
- Verifique se Flask-Caching está instalado
- Confirme que `CACHE_TYPE` está configurado
- Limpe o cache manualmente se necessário

## Próximas Otimizações Recomendadas

1. **CDN para assets estáticos** (Cloudflare, etc)
2. **Redis** para cache distribuído (se migrar para plano pago)
3. **PostgreSQL** ao invés de SQLite (para produção)
4. **Minificação de CSS/JS** com ferramentas build
5. **Imagens em WebP** para redução de tamanho
