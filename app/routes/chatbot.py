from flask import Blueprint, request, jsonify, session
from app import db
from app.models import ChatConversation, ChatMessage, Product, Category, Order, User, StoreSettings
from google import genai
from google.genai import types
import os
import uuid
import json
import re
from datetime import datetime

chatbot_bp = Blueprint('chatbot', __name__)

def get_available_api_keys():
    """Retorna lista de chaves API disponíveis"""
    api_keys = []
    
    try:
        from gemini_keys import GEMINI_API_KEYS
        api_keys = [key for key in GEMINI_API_KEYS if key and key.strip()]
        print(f"📋 Carregadas {len(api_keys)} chaves do arquivo gemini_keys.py")
    except ImportError:
        print("⚠️ Arquivo gemini_keys.py não encontrado, usando variáveis de ambiente...")
        for i in range(1, 6):
            key = os.environ.get(f"GEMINI_API_KEY_{i}")
            if key:
                api_keys.append(key)
        
        fallback_key = os.environ.get("GEMINI_API_KEY")
        if fallback_key and fallback_key not in api_keys:
            api_keys.append(fallback_key)
    
    return api_keys

def create_gemini_client_with_rotation(api_keys):
    """Tenta criar cliente com rotação de chaves"""
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            return client, key
        except Exception as e:
            print(f"Falha ao inicializar com chave: {str(e)[:20]}...")
            continue
    
    return None, None

api_keys = get_available_api_keys()
client, current_key = create_gemini_client_with_rotation(api_keys)

if not client:
    print("⚠️ AVISO: Nenhuma chave API válida encontrada!")
    client = None

def get_order_info(order_code=None, phone=None):
    """Buscar informações de pedidos"""
    orders = []
    
    if order_code:
        order_code = order_code.strip().upper()
        
        # 1. Tentar buscar por order_code customizado (alfanumérico)
        order = Order.query.filter_by(order_code=order_code).first()
        if order:
            orders.append(order)
        else:
            # 2. Tentar extrair ID do formato PED000123
            import re
            match = re.search(r'PED0*(\d+)', order_code)
            if match:
                order_id = int(match.group(1))
                order = Order.query.get(order_id)
                if order:
                    orders.append(order)
            else:
                # 3. Tentar buscar diretamente por ID se for só número
                try:
                    order_id = int(order_code)
                    order = Order.query.get(order_id)
                    if order:
                        orders.append(order)
                except ValueError:
                    pass
    elif phone:
        # Normalizar telefone (remover TODOS os caracteres não numéricos)
        import re
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Buscar pedidos recentes pelo telefone (últimos 5)
        # Tentar diferentes formatos de telefone no banco
        user = User.query.filter_by(phone=clean_phone).first()
        if not user:
            user = User.query.filter_by(phone=f'+55{clean_phone}').first()
        if not user:
            # Tentar com DDD separado
            user = User.query.filter_by(phone=f'({clean_phone[:2]}) {clean_phone[2:7]}-{clean_phone[7:]}').first()
        
        if user:
            orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).limit(5).all()
    
    orders_info = []
    for order in orders:
        # Obter detalhes completos dos itens do pedido
        items_details = []
        for item in order.items:
            items_details.append({
                'produto': item.product.name if item.product else 'Produto não disponível',
                'quantidade': item.quantity,
                'preço_unitário': f'R$ {item.price:.2f}',
                'subtotal': f'R$ {(item.price * item.quantity):.2f}'
            })
        
        orders_info.append({
            'código': order.order_number,
            'status': order.status,
            'valor_total': f'R$ {order.total:.2f}',
            'data': order.created_at.strftime('%d/%m/%Y %H:%M'),
            'endereço_entrega': order.delivery_address or 'Retirada no local',
            'forma_pagamento': order.payment_method or 'Não especificado',
            'itens': items_details
        })
    
    return orders_info

def get_store_context(user_message=''):
    """Obter contexto da loja, produtos e pedidos"""
    store_name = StoreSettings.get_setting('store_name', 'Nossa Hamburgueria')
    store_phone = StoreSettings.get_setting('store_phone', '')
    store_address = StoreSettings.get_setting('store_address', '')
    
    # Obter domínio do site (para construir URLs completas)
    site_domain = os.environ.get('REPL_SLUG', '')
    if site_domain:
        site_url = f"https://{site_domain}.repl.co"
    else:
        site_url = request.host_url.rstrip('/')
    
    categories = Category.query.all()
    products = Product.query.filter_by(active=True).all()
    
    # Organizar produtos por categoria para melhor apresentação
    categories_info = []
    for category in categories:
        cat_products = [p for p in products if p.category_id == category.id][:5]
        if cat_products:
            categories_info.append({
                'nome': category.name,
                'link': f'{site_url}/categoria/{category.id}',
                'produtos': len([p for p in products if p.category_id == category.id])
            })
    
    products_info = []
    for product in products[:20]:  # Limitar a 20 produtos para não ultrapassar contexto
        products_info.append({
            'id': product.id,
            'nome': product.name,
            'preço': f'R$ {product.price:.2f}',
            'descrição': product.description or '',
            'categoria': product.category.name if product.category else '',
            'link': f'{site_url}/produto/{product.id}',
            'em_estoque': product.stock > 0 if product.stock is not None else True
        })
    
    # Detectar se o usuário está perguntando sobre pedido
    order_context = ""
    if any(word in user_message.lower() for word in ['pedido', 'status', 'código', 'rastrear', 'acompanhar']):
        # Extrair possível código de pedido ou telefone
        import re
        
        # Normalizar mensagem para extrair telefone (remove tudo que não é número)
        normalized_message = re.sub(r'[^\d]', '', user_message)
        phone_match = re.search(r'\d{10,11}', normalized_message)
        
        # Buscar código de pedido com priorização inteligente
        # 1º: Códigos alfanuméricos (ABC123, XYZ456)
        # 2º: Códigos PED (PED000001)
        # 3º: Números isolados (1, 2, 3)
        all_matches = re.findall(r'\b([A-Z]{3}[0-9]{3,6}|PED\d+|\d{1,10})\b', user_message.upper())
        
        code_match = None
        if all_matches:
            # Priorizar por tipo de código
            for match in all_matches:
                if re.match(r'[A-Z]{3}[0-9]{3,6}', match):  # Alfanumérico
                    code_match = match
                    break
            if not code_match:
                for match in all_matches:
                    if match.startswith('PED'):  # Código PED
                        code_match = match
                        break
            if not code_match:
                # Usar número apenas se houver palavra-chave específica
                if any(word in user_message.upper() for word in ['PED', 'CÓDIGO', 'CODIGO', 'NUMERO', 'NÚMERO', 'PEDIDO']):
                    code_match = all_matches[0]
        
        orders_info = []
        if code_match:
            orders_info = get_order_info(order_code=code_match)
        elif phone_match:
            # Usar telefone apenas se não encontrou código
            orders_info = get_order_info(phone=phone_match.group())
        
        if orders_info:
            order_context = f"\n\nPEDIDOS ENCONTRADOS:\n{json.dumps(orders_info, ensure_ascii=False, indent=2)}\n"
    
    context = f"""
Você é o assistente virtual da {store_name}, uma hamburgueria especializada em hambúrgueres artesanais.

INFORMAÇÕES DA LOJA:
- Nome: {store_name}
- Telefone: {store_phone}
- Endereço: {store_address}
- Site: {site_url}
- Página de Compras: {site_url}/

CATEGORIAS DISPONÍVEIS:
{json.dumps(categories_info, ensure_ascii=False, indent=2)}

PRODUTOS DISPONÍVEIS:
{json.dumps(products_info, ensure_ascii=False, indent=2)}
{order_context}

PROTOCOLO DE ATENDIMENTO (SIGA RIGOROSAMENTE):
1. PRIMEIRA INTERAÇÃO: Pergunte o NOME do cliente de forma amigável
2. SEGUNDA INTERAÇÃO: Pergunte o TELEFONE (com DDD) do cliente
3. APÓS COLETAR DADOS: Confirme os dados (Nome + Telefone) com o cliente
4. SOMENTE DEPOIS: Envie o link da página de compras e ajude com produtos
5. Durante todo processo, seja amigável e use emojis 😊

SUAS CAPACIDADES:
1. Coletar nome e telefone do cliente ANTES de qualquer outra coisa
2. Ajudar clientes a escolher produtos
3. Responder perguntas sobre produtos e cardápio
4. Consultar status de pedidos (por código do pedido ou telefone)
5. Fornecer informações sobre a loja
6. Ser educado, prestativo e profissional

CONSULTA DE PEDIDOS:
- Se o cliente quiser consultar um pedido, peça o código do pedido OU telefone cadastrado
- Códigos de pedido podem ser:
  * Alfanuméricos customizados (ex: ABC12345, XYZ789)
  * Formato padrão (PED000001, PED000002)
  * Apenas o número do ID (1, 2, 3)
- Com telefone, você pode consultar os últimos 5 pedidos do cliente
- Aceite telefones em qualquer formato: (31) 98765-4321, 31987654321, +55 31 98765-4321

STATUS DE PEDIDOS:
- pending: Pedido recebido, aguardando confirmação
- confirmed: Pedido confirmado, em preparação
- preparing: Pedido sendo preparado
- ready: Pedido pronto para retirada/entrega
- in_delivery: Pedido saiu para entrega
- delivered: Pedido entregue
- cancelled: Pedido cancelado

INSTRUÇÕES IMPORTANTES SOBRE COLETA DE DADOS:
- NUNCA envie o link de vendas ANTES de coletar Nome e Telefone
- Seja persistente mas educado ao pedir os dados
- Se o cliente tentar desviar, lembre gentilmente que precisa dos dados para continuar
- Após coletar, confirme: "Perfeito! Nome: [nome], Telefone: [telefone]. Está correto?"
- Somente após confirmação, envie o link de vendas

FORMATO DE COLETA DE DADOS:
1ª mensagem do cliente → Pergunte: "Olá! 👋 Qual é o seu nome?"
2ª mensagem (nome fornecido) → Pergunte: "Prazer, [Nome]! 😊 Qual é o seu telefone (com DDD)?"
3ª mensagem (telefone fornecido) → Confirme: "Perfeito! Nome: [nome], Telefone: [telefone]. Está correto?"
4ª mensagem (confirmação) → Envie link e ajude: "Ótimo! Agora você pode fazer seu pedido aqui: {site_url}"

INSTRUÇÕES SOBRE LINKS (APÓS COLETA DE DADOS):
- Após coletar e confirmar dados, SEMPRE inclua: "🛒 Faça seu pedido aqui: {site_url}"
- Quando mencionar produtos, inclua os links diretos
- Quando listar produtos, mostre o link de cada um
- Facilite o acesso à página de compras

INSTRUÇÕES GERAIS:
- Seja amigável e use emojis 🍔
- NÃO pule a etapa de coleta de dados
- PRIMEIRO coleta dados, DEPOIS envia links
- Sugira produtos COM LINKS clicáveis (após coletar dados)
- Facilite ao máximo o acesso à página de compras
"""
    return context

def get_or_create_conversation(session_id):
    """Obter ou criar conversa"""
    conversation = ChatConversation.query.filter_by(session_id=session_id).first()
    
    if not conversation:
        conversation = ChatConversation(session_id=session_id)
        db.session.add(conversation)
        db.session.commit()
    
    return conversation

def extract_phone_from_text(text):
    """Extrair telefone da mensagem"""
    phone_normalized = re.sub(r'[^\d]', '', text)
    phone_match = re.search(r'\d{10,11}', phone_normalized)
    if phone_match:
        return phone_match.group()
    return None

def register_user_from_chat(name, phone):
    """Registrar usuário automaticamente via chatbot"""
    try:
        phone_normalized = ''.join(filter(str.isdigit, phone))
        
        if len(phone_normalized) < 10:
            return None, "Telefone inválido. Digite um número com DDD (ex: 31987654321)"
        
        existing_user = User.query.filter_by(phone=phone_normalized).first()
        if existing_user:
            return existing_user, None
        
        new_user = User(username=name, phone=phone_normalized, role='customer')
        db.session.add(new_user)
        db.session.commit()
        
        return new_user, None
    except Exception as e:
        return None, f"Erro ao criar conta: {str(e)}"

def get_conversation_history(conversation, limit=10):
    """Obter histórico de mensagens"""
    messages = conversation.messages[-limit:] if len(conversation.messages) > limit else conversation.messages
    
    history = []
    for msg in messages:
        history.append({
            'role': msg.role,
            'content': msg.content
        })
    
    return history

def save_message(conversation_id, role, content, extra_data=None):
    """Salvar mensagem no banco"""
    message = ChatMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        extra_data=json.dumps(extra_data) if extra_data else None
    )
    db.session.add(message)
    db.session.commit()
    return message

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal do chatbot"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        # Criar ou obter session_id
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Obter ou criar conversa
        conversation = get_or_create_conversation(session_id)
        
        # Detectar e salvar nome/telefone
        phone_detected = extract_phone_from_text(user_message)
        
        # Se ainda não tem nome e parece ser um nome (não tem números), salvar
        if not conversation.user_name and not any(char.isdigit() for char in user_message) and len(user_message.split()) <= 3:
            conversation.user_name = user_message.strip()
            db.session.commit()
            print(f"📝 Nome salvo: {conversation.user_name}")
        
        # Se já tem nome mas não tem telefone, e detectou telefone na mensagem
        if conversation.user_name and not conversation.user_phone and phone_detected:
            conversation.user_phone = phone_detected
            db.session.commit()
            print(f"📞 Telefone salvo: {conversation.user_phone}")
            
            # Tentar criar usuário automaticamente
            user, error = register_user_from_chat(conversation.user_name, conversation.user_phone)
            if user:
                conversation.user_id = user.id
                db.session.commit()
                print(f"✅ Usuário criado/encontrado: {user.username} ({user.phone})")
        
        # Salvar mensagem do usuário
        save_message(conversation.id, 'user', user_message)
        
        # Obter histórico
        history = get_conversation_history(conversation)
        
        # Obter domínio do site
        site_domain = os.environ.get('REPL_SLUG', '')
        if site_domain:
            site_url = f"https://{site_domain}.repl.co"
        else:
            site_url = request.host_url.rstrip('/')
        
        # Adicionar informação sobre status da coleta de dados ao contexto
        data_collection_status = ""
        if not conversation.user_name:
            data_collection_status = "\n\n⚠️ ATENÇÃO: Cliente ainda NÃO forneceu o NOME. PERGUNTE O NOME AGORA e NÃO envie links."
        elif not conversation.user_phone:
            data_collection_status = f"\n\n⚠️ ATENÇÃO: Cliente {conversation.user_name} ainda NÃO forneceu o TELEFONE. PERGUNTE O TELEFONE AGORA e NÃO envie links."
        elif not conversation.user_id:
            data_collection_status = f"\n\n✅ Dados coletados: {conversation.user_name} - {conversation.user_phone}. CONFIRME com o cliente se os dados estão corretos. Se sim, envie o link: {site_url}"
        else:
            data_collection_status = f"\n\n✅ Cliente cadastrado: {conversation.user_name} - {conversation.user_phone}. PODE enviar links e ajudar com produtos."
        
        # Preparar contexto (passa a mensagem do usuário para detectar consultas de pedido)
        store_context = get_store_context(user_message) + data_collection_status
        
        # Preparar mensagens para o Gemini
        messages = [
            types.Content(
                role='user',
                parts=[types.Part(text=store_context)]
            )
        ]
        
        # Adicionar histórico
        for msg in history:
            role = 'user' if msg['role'] == 'user' else 'model'
            messages.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg['content'])]
                )
            )
        
        # Gerar resposta do Gemini com rotação automática de chaves
        ai_response = None
        last_error = None
        
        available_keys = get_available_api_keys()
        
        for api_key in available_keys:
            try:
                temp_client = genai.Client(api_key=api_key)
                
                response = temp_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=messages,
                    config=types.GenerateContentConfig(
                        temperature=0.9,
                        max_output_tokens=1024,
                    )
                )
                
                ai_response = response.text if response.text else 'Desculpe, não consegui processar sua mensagem.'
                print(f"✅ Resposta gerada com sucesso usando chave: ...{api_key[-10:]}")
                break
                
            except Exception as e:
                error_str = str(e).lower()
                last_error = str(e)
                
                if 'quota' in error_str or 'limit' in error_str or '429' in error_str or 'resource_exhausted' in error_str:
                    print(f"⚠️ Limite atingido na chave ...{api_key[-10:]}, tentando próxima...")
                    continue
                elif 'invalid' in error_str or 'api_key' in error_str:
                    print(f"❌ Chave inválida ...{api_key[-10:]}, tentando próxima...")
                    continue
                else:
                    print(f"❌ Erro desconhecido com chave ...{api_key[-10:]}: {str(e)[:50]}")
                    continue
        
        if not ai_response:
            ai_response = f'Desculpe, todas as chaves API atingiram o limite. Tente novamente mais tarde. Erro: {last_error[:100] if last_error else "Desconhecido"}'
        
        # Salvar resposta do assistente
        save_message(conversation.id, 'assistant', ai_response)
        
        # Atualizar timestamp da conversa
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Erro no chatbot: {str(e)}")
        return jsonify({
            'error': 'Ocorreu um erro ao processar sua mensagem',
            'details': str(e)
        }), 500

@chatbot_bp.route('/api/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Obter histórico de conversa"""
    try:
        conversation = ChatConversation.query.filter_by(session_id=session_id).first()
        
        if not conversation:
            return jsonify({'messages': []})
        
        messages = []
        for msg in conversation.messages:
            messages.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat()
            })
        
        return jsonify({
            'messages': messages,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/api/chat/clear/<session_id>', methods=['DELETE'])
def clear_chat(session_id):
    """Limpar conversa"""
    try:
        conversation = ChatConversation.query.filter_by(session_id=session_id).first()
        
        if conversation:
            db.session.delete(conversation)
            db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
