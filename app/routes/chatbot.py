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

def get_store_context():
    """Obter contexto da loja e produtos"""
    store_name = StoreSettings.get_setting('store_name', 'Nossa Hamburgueria')
    store_phone = StoreSettings.get_setting('store_phone', '')
    
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
    
    context = f"""
Você é o assistente virtual da {store_name}, uma hamburgueria.

PRODUTOS DISPONÍVEIS:
{json.dumps(products_info, ensure_ascii=False, indent=2)}

SUAS CAPACIDADES:
1. Ajudar clientes a fazer pedidos
2. Responder perguntas sobre produtos e cardápio
3. Consultar status de pedidos
4. Fornecer informações sobre a loja
5. Ser educado, prestativo e profissional

INSTRUÇÕES IMPORTANTES:
- Seja amigável e use emojis ocasionalmente 🍔
- Sugira produtos baseado no que o cliente pede
- Se o cliente quiser fazer pedido, colete: nome, telefone, endereço e itens
- Confirme sempre os detalhes antes de finalizar
- Se não souber algo, seja honesto
- Mantenha respostas concisas e objetivas

Telefone da loja: {store_phone}
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
        
        # Preparar contexto
        store_context = get_store_context()
        
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
