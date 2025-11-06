from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from flask import session
from app import socketio, db
from app.models import Order, User
from datetime import datetime

@socketio.on('connect')
def handle_connect():
    try:
        user_id = session.get('_user_id')
        if user_id:
            user = User.query.get(int(user_id))
            if user:
                if user.is_admin:
                    join_room('admin_orders')
                    emit('connected', {'message': 'Conectado ao sistema de pedidos'})
                    
                    pending_count = Order.query.filter_by(status='Pendente').count()
                    emit('order_stats', {'pending_count': pending_count})
                else:
                    join_room(f'user_{user.id}')
                    emit('connected', {'message': 'Conectado ao sistema de atualizações'})
                return
        
        emit('error', {'message': 'Não autorizado'})
    except Exception as e:
        print(f"Erro na conexão Socket.IO: {e}")
        emit('error', {'message': 'Erro de autenticação'})

@socketio.on('disconnect')
def handle_disconnect():
    try:
        user_id = session.get('_user_id')
        if user_id:
            user = User.query.get(int(user_id))
            if user:
                if user.is_admin:
                    leave_room('admin_orders')
                else:
                    leave_room(f'user_{user.id}')
    except Exception as e:
        print(f"Erro ao desconectar: {e}")

@socketio.on('join_user_room')
def handle_join_user_room(data):
    try:
        user_id = session.get('_user_id')
        if user_id and int(user_id) == data.get('user_id'):
            join_room(f'user_{user_id}')
            print(f"Usuário {user_id} entrou na sala de notificações")
    except Exception as e:
        print(f"Erro ao entrar na sala: {e}")

@socketio.on('join_comanda_room')
def handle_join_comanda_room(data):
    try:
        comanda_id = data.get('comanda_id')
        customer_comanda_id = session.get('customer_comanda_id')
        
        if customer_comanda_id and int(customer_comanda_id) == int(comanda_id):
            join_room(f'comanda_{comanda_id}')
            emit('connected', {'message': f'Conectado à comanda {comanda_id}'})
            print(f"Cliente entrou na sala da comanda {comanda_id}")
    except Exception as e:
        print(f"Erro ao entrar na sala da comanda: {e}")
        emit('error', {'message': 'Erro ao conectar à comanda'})

@socketio.on('leave_comanda_room')
def handle_leave_comanda_room(data):
    try:
        comanda_id = data.get('comanda_id')
        leave_room(f'comanda_{comanda_id}')
        print(f"Cliente saiu da sala da comanda {comanda_id}")
    except Exception as e:
        print(f"Erro ao sair da sala da comanda: {e}")

@socketio.on('request_order_update')
def handle_order_update_request():
    if current_user.is_authenticated and current_user.is_admin:
        orders = Order.query.order_by(Order.created_at.desc()).limit(50).all()
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'customer_name': order.user.username,
                'total': float(order.total),
                'status': order.status,
                'payment_status': order.payment_status,
                'created_at': order.created_at.strftime('%d/%m/%Y %H:%M'),
                'delivery_type': order.delivery_type,
                'estimated_prep_time': order.estimated_prep_time,
                'items_count': len(order.items)
            })
        
        emit('orders_update', {'orders': orders_data})

def notify_new_order(order):
    from app import socketio
    order_data = {
        'id': order.id,
        'customer_name': order.user.username,
        'customer_phone': order.customer_phone or order.user.phone,
        'total': float(order.total),
        'status': order.status,
        'payment_status': order.payment_status,
        'created_at': order.created_at.strftime('%d/%m/%Y %H:%M'),
        'delivery_type': order.delivery_type,
        'delivery_address': order.delivery_address,
        'items': [{'name': item.product.name, 'quantity': item.quantity, 'price': float(item.price)} for item in order.items],
        'items_count': len(order.items)
    }
    socketio.emit('new_order', order_data, room='admin_orders', namespace='/')

def notify_order_update(order):
    from app import socketio
    order_data = {
        'id': order.id,
        'status': order.status,
        'payment_status': order.payment_status,
        'estimated_prep_time': order.estimated_prep_time,
        'estimated_delivery_time': order.estimated_delivery_time
    }
    socketio.emit('order_updated', order_data, room='admin_orders', namespace='/')
    
    user_notification = {
        'order_id': order.id,
        'new_status': order.status,
        'payment_status': order.payment_status
    }
    socketio.emit('order_status_changed', user_notification, room=f'user_{order.user_id}', namespace='/')

def notify_comanda_item_update(comanda_item):
    from app import socketio
    item_data = {
        'item_id': comanda_item.id,
        'comanda_id': comanda_item.comanda_id,
        'product_name': comanda_item.product.name,
        'status': comanda_item.status,
        'sent_to_kitchen': comanda_item.sent_to_kitchen
    }
    socketio.emit('comanda_item_updated', item_data, room=f'comanda_{comanda_item.comanda_id}', namespace='/')
    print(f"Notificação enviada para comanda_{comanda_item.comanda_id}: item {comanda_item.id} status {comanda_item.status}")

def notify_new_comanda_item(comanda_item):
    from app import socketio
    item_data = {
        'item_id': comanda_item.id,
        'comanda_id': comanda_item.comanda_id,
        'product_name': comanda_item.product.name,
        'quantity': comanda_item.quantity,
        'status': comanda_item.status
    }
    socketio.emit('new_item_added', item_data, room=f'comanda_{comanda_item.comanda_id}', namespace='/')
    print(f"Novo item adicionado à comanda_{comanda_item.comanda_id}")
