from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db, socketio
from app.models import Order, OrderItem, ComandaItem
from flask_socketio import emit

kitchen_bp = Blueprint('kitchen', __name__, url_prefix='/cozinha')

def admin_or_kitchen_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Acesso restrito. Faça login.', 'danger')
            return redirect(url_for('auth.login'))
        if not (current_user.is_admin or current_user.role in ['kitchen', 'manager']):
            flash('Acesso restrito à cozinha e administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@kitchen_bp.route('/')
@login_required
@admin_or_kitchen_required
def kds():
    pending_orders = Order.query.filter(
        Order.status.in_(['Pendente', 'Confirmado', 'Em Preparo'])
    ).order_by(Order.created_at).all()
    
    pending_comanda_items = ComandaItem.query.filter_by(status='pending').order_by(ComandaItem.created_at).all()
    
    return render_template('kitchen/kds.html', 
                         pending_orders=pending_orders,
                         pending_comanda_items=pending_comanda_items)

@kitchen_bp.route('/pedido/<int:order_id>/status', methods=['POST'])
@login_required
@admin_or_kitchen_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    valid_statuses = ['Confirmado', 'Em Preparo', 'Pronto', 'Entregue']
    if new_status not in valid_statuses:
        flash('Status inválido', 'danger')
        return redirect(url_for('kitchen.kds'))
    
    old_status = order.status
    order.status = new_status
    db.session.commit()
    
    socketio.emit('order_status_changed', {
        'order_id': order.id,
        'new_status': new_status
    }, room=f'user_{order.user_id}')
    
    socketio.emit('kitchen_update', {
        'order_id': order.id,
        'status': new_status
    }, room='admin_orders')
    
    flash(f'✅ Pedido #{order.id} atualizado de "{old_status}" para "{new_status}"', 'success')
    return redirect(url_for('kitchen.kds'))

@kitchen_bp.route('/comanda-item/<int:item_id>/status', methods=['POST'])
@login_required
@admin_or_kitchen_required
def update_comanda_item_status(item_id):
    from app.routes.websocket import notify_comanda_item_update
    
    item = ComandaItem.query.get_or_404(item_id)
    new_status = request.form.get('status')
    
    valid_statuses = ['pending', 'preparing', 'ready', 'delivered']
    if new_status not in valid_statuses:
        flash('Status inválido', 'danger')
        return redirect(url_for('kitchen.kds'))
    
    item.status = new_status
    db.session.commit()
    
    notify_comanda_item_update(item)
    
    socketio.emit('comanda_item_updated', {
        'item_id': item.id,
        'status': new_status
    }, room='admin_orders')
    
    status_display = {
        'pending': 'Pendente',
        'preparing': 'Em Preparo',
        'ready': 'Pronto',
        'delivered': 'Entregue'
    }
    
    flash(f'✅ Item da comanda #{item.comanda.comanda_number} atualizado para "{status_display.get(new_status, new_status)}"', 'success')
    return redirect(url_for('kitchen.kds'))

@kitchen_bp.route('/api/pendentes')
@login_required
@admin_or_kitchen_required
def api_pending_orders():
    pending_orders = Order.query.filter(
        Order.status.in_(['Pendente', 'Confirmado', 'Em Preparo'])
    ).order_by(Order.created_at).all()
    
    orders_data = []
    for order in pending_orders:
        orders_data.append({
            'id': order.id,
            'status': order.status,
            'created_at': order.created_at.strftime('%H:%M'),
            'items': [{'name': item.product.name, 'quantity': item.quantity} for item in order.items],
            'delivery_type': order.delivery_type,
            'table_number': order.table.table_number if order.table_id else None
        })
    
    return jsonify(orders_data)
