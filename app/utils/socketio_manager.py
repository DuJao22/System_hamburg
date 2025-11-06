"""
Gerenciador de Socket.IO para notificações em tempo real
Namespace: /orders
Rooms: table_{id}, kitchen_all, waiter_{user_id}
"""
from flask_socketio import emit, join_room, leave_room
from flask import request
from app import socketio
from functools import wraps

ORDERS_NAMESPACE = '/orders'

def emit_order_notification(event_type, data, rooms=None):
    """
    Emite notificação de pedido para rooms específicas
    
    Args:
        event_type: Tipo de evento ('order:new', 'order:update', 'order:itemUpdate', 'notification')
        data: Dados do evento
        rooms: Lista de rooms para emitir (table_{id}, kitchen_all, waiter_{id})
    """
    if rooms is None:
        rooms = []
    
    for room in rooms:
        socketio.emit(event_type, data, room=room, namespace=ORDERS_NAMESPACE)

def emit_new_order(order_data, table_id=None, waiter_id=None):
    """
    Emite evento de novo pedido para cozinha, garçom e cliente
    """
    rooms = ['kitchen_all']
    
    if table_id:
        rooms.append(f'table_{table_id}')
    
    if waiter_id:
        rooms.append(f'waiter_{waiter_id}')
    
    emit_order_notification('order:new', order_data, rooms)

def emit_order_status_update(order_data, table_id=None, waiter_id=None):
    """
    Emite evento de atualização de status do pedido
    """
    rooms = ['kitchen_all']
    
    if table_id:
        rooms.append(f'table_{table_id}')
    
    if waiter_id:
        rooms.append(f'waiter_{waiter_id}')
    
    emit_order_notification('order:update', order_data, rooms)

def emit_order_item_update(item_data, table_id=None, waiter_id=None):
    """
    Emite evento de atualização de item do pedido
    """
    rooms = []
    
    if table_id:
        rooms.append(f'table_{table_id}')
    
    if waiter_id:
        rooms.append(f'waiter_{waiter_id}')
    
    rooms.append('kitchen_all')
    
    emit_order_notification('order:itemUpdate', item_data, rooms)

def emit_notification(notification_data, recipient_type, recipient_id=None):
    """
    Emite notificação genérica
    
    Args:
        notification_data: Dados da notificação
        recipient_type: 'kitchen', 'waiter', 'table'
        recipient_id: ID do destinatário (table_id, user_id)
    """
    if recipient_type == 'kitchen':
        room = 'kitchen_all'
    elif recipient_type == 'waiter' and recipient_id:
        room = f'waiter_{recipient_id}'
    elif recipient_type == 'table' and recipient_id:
        room = f'table_{recipient_id}'
    else:
        return
    
    emit_order_notification('notification', notification_data, [room])

@socketio.on('connect', namespace=ORDERS_NAMESPACE)
def handle_connect():
    """Cliente conectado ao namespace de pedidos"""
    print(f'Cliente conectado ao namespace {ORDERS_NAMESPACE}')

@socketio.on('disconnect', namespace=ORDERS_NAMESPACE)
def handle_disconnect():
    """Cliente desconectado do namespace de pedidos"""
    print(f'Cliente desconectado do namespace {ORDERS_NAMESPACE}')

@socketio.on('join', namespace=ORDERS_NAMESPACE)
def handle_join(data):
    """
    Cliente entra em uma room
    data: {'room': 'table_1' | 'kitchen_all' | 'waiter_5'}
    """
    room = data.get('room')
    if room:
        join_room(room)
        print(f'Cliente entrou na room: {room}')
        emit('joined', {'room': room})

@socketio.on('leave', namespace=ORDERS_NAMESPACE)
def handle_leave(data):
    """
    Cliente sai de uma room
    data: {'room': 'table_1' | 'kitchen_all' | 'waiter_5'}
    """
    room = data.get('room')
    if room:
        leave_room(room)
        print(f'Cliente saiu da room: {room}')
        emit('left', {'room': room})

def socket_emit_after_commit(f):
    """
    Decorator para garantir que eventos Socket.IO só sejam emitidos após commit no BD
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result, emit_func = f(*args, **kwargs)
        if emit_func:
            emit_func()
        return result
    return decorated_function
