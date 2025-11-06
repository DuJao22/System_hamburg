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
