from flask import Blueprint, request, jsonify, session
from app import db
from app.models import ChatConversation, ChatMessage, Product, Category, Order, User, StoreSettings
from google import genai
from google.genai import types
import os
import uuid
import json
from datetime import datetime

chatbot_bp = Blueprint('chatbot', __name__)

# the newest Gemini model is "gemini-2.5-flash" which was released in 2025.
# do not change this unless explicitly requested by the user
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
    
    categories = Category.query.all()
    products = Product.query.filter_by(active=True).all()
    
    products_info = []
    for product in products[:20]:  # Limitar a 20 produtos para não ultrapassar contexto
        products_info.append({
            'nome': product.name,
            'preço': f'R$ {product.price:.2f}',
            'descrição': product.description or '',
            'categoria': product.category.name if product.category else ''
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

PRODUTOS DISPONÍVEIS:
{json.dumps(products_info, ensure_ascii=False, indent=2)}
{order_context}

SUAS CAPACIDADES:
1. Ajudar clientes a fazer pedidos (colete: nome, telefone, endereço e itens desejados)
2. Responder perguntas sobre produtos e cardápio
3. Consultar status de pedidos (por código do pedido ou telefone)
4. Fornecer informações sobre a loja
5. Ser educado, prestativo e profissional

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

INSTRUÇÕES IMPORTANTES:
- Seja amigável e use emojis ocasionalmente 🍔
- Sugira produtos baseado no que o cliente pede
- Confirme sempre os detalhes antes de finalizar pedido
- Para novos pedidos, oriente o cliente a usar o site para finalizar
- Se não souber algo, seja honesto
- Mantenha respostas concisas e objetivas
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
        
        # Salvar mensagem do usuário
        save_message(conversation.id, 'user', user_message)
        
        # Obter histórico
        history = get_conversation_history(conversation)
        
        # Preparar contexto (passa a mensagem do usuário para detectar consultas de pedido)
        store_context = get_store_context(user_message)
        
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
        
        # Gerar resposta do Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=messages,
            config=types.GenerateContentConfig(
                temperature=0.9,
                max_output_tokens=1024,
            )
        )
        
        ai_response = response.text if response.text else 'Desculpe, não consegui processar sua mensagem.'
        
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
