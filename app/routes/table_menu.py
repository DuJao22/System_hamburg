from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from app.models import Table, Comanda, Product, Category, Extra, Order, OrderItem, OrderItemExtra
from flask_login import current_user, login_user
import io
import base64

table_menu_bp = Blueprint('table_menu', __name__)

@table_menu_bp.route('/mesa/<table_number>')
def table_access(table_number):
    table = Table.query.filter_by(table_number=table_number).first()
    if not table:
        flash('Mesa não encontrada.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('table_menu/table_access.html', table=table)

@table_menu_bp.route('/mesa/auth', methods=['POST'])
def table_auth():
    table_number = request.form.get('table_number')
    pin = request.form.get('pin')
    auth_method = request.form.get('auth_method')
    
    if auth_method == 'login':
        return redirect(url_for('auth.login', next=url_for('table_menu.table_access', table_number=table_number)))
    
    if not table_number or not pin:
        flash('Por favor, informe o número da mesa e o PIN.', 'danger')
        return redirect(url_for('table_menu.table_access', table_number=table_number))
    
    table = Table.query.filter_by(table_number=table_number).first()
    if not table:
        flash('Mesa não encontrada.', 'danger')
        return redirect(url_for('main.index'))
    
    comanda = Comanda.query.filter_by(table_id=table.id, status='open', access_pin=pin).first()
    
    if not comanda:
        flash('PIN inválido ou comanda não encontrada.', 'danger')
        return redirect(url_for('table_menu.table_access', table_number=table_number))
    
    session['table_session'] = {
        'table_id': table.id,
        'table_number': table.table_number,
        'comanda_id': comanda.id,
        'comanda_number': comanda.comanda_number
    }
    
    flash(f'Bem-vindo à mesa {table.table_number}!', 'success')
    return redirect(url_for('table_menu.table_catalog'))

@table_menu_bp.route('/mesa/catalogo')
def table_catalog():
    if 'table_session' not in session:
        flash('Por favor, faça login com o número da mesa e PIN.', 'warning')
        return redirect(url_for('main.index'))
    
    table_session = session['table_session']
    table = Table.query.get(table_session['table_id'])
    comanda = Comanda.query.get(table_session['comanda_id'])
    
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    
    query = Product.query.filter_by(active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Product.name.contains(search) | Product.description.contains(search))
    
    products = query.all()
    categories = Category.query.all()
    extras = Extra.query.filter_by(active=True).all()
    
    return render_template('table_menu/catalog.html', 
                         products=products, 
                         categories=categories,
                         extras=extras,
                         table=table,
                         comanda=comanda,
                         selected_category=category_id,
                         search_query=search)

@table_menu_bp.route('/mesa/adicionar-item', methods=['POST'])
def table_add_item():
    if 'table_session' not in session:
        return jsonify({'success': False, 'message': 'Sessão expirada'}), 401
    
    table_session = session['table_session']
    comanda = Comanda.query.get(table_session['comanda_id'])
    
    if not comanda or comanda.status != 'open':
        return jsonify({'success': False, 'message': 'Comanda não está aberta'}), 400
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    extras = data.get('extras', [])
    notes = data.get('notes', '')
    
    product = Product.query.get(product_id)
    if not product or not product.active:
        return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
    
    if product.stock < quantity:
        return jsonify({'success': False, 'message': 'Estoque insuficiente'}), 400
    
    from app.models import ComandaItem, ComandaItemExtra
    
    comanda_item = ComandaItem(
        comanda_id=comanda.id,
        product_id=product.id,
        quantity=quantity,
        price=product.price,
        notes=notes
    )
    db.session.add(comanda_item)
    db.session.flush()
    
    for extra_data in extras:
        extra_id = extra_data.get('id')
        extra_quantity = extra_data.get('quantity', 1)
        
        extra = Extra.query.get(extra_id)
        if extra and extra.active:
            comanda_item_extra = ComandaItemExtra(
                comanda_item_id=comanda_item.id,
                extra_id=extra.id,
                quantity=extra_quantity,
                price=extra.price
            )
            db.session.add(comanda_item_extra)
    
    comanda.total = comanda.calculate_total()
    db.session.commit()
    
    from app.routes.websocket import emit_kitchen_notification
    emit_kitchen_notification(comanda_item.id)
    
    return jsonify({
        'success': True, 
        'message': 'Item adicionado com sucesso!',
        'total': comanda.total
    })

@table_menu_bp.route('/mesa/meus-pedidos')
def table_orders():
    if 'table_session' not in session:
        flash('Por favor, faça login com o número da mesa e PIN.', 'warning')
        return redirect(url_for('main.index'))
    
    table_session = session['table_session']
    table = Table.query.get(table_session['table_id'])
    comanda = Comanda.query.get(table_session['comanda_id'])
    
    orders = Order.query.filter_by(table_id=table.id).order_by(Order.created_at.desc()).all()
    
    return render_template('table_menu/orders.html', 
                         table=table,
                         comanda=comanda,
                         orders=orders)

@table_menu_bp.route('/mesa/status/<int:order_id>')
def table_order_status(order_id):
    if 'table_session' not in session:
        return jsonify({'success': False, 'message': 'Sessão expirada'}), 401
    
    table_session = session['table_session']
    order = Order.query.filter_by(id=order_id, table_id=table_session['table_id']).first()
    
    if not order:
        return jsonify({'success': False, 'message': 'Pedido não encontrado'}), 404
    
    return jsonify({
        'success': True,
        'status': order.status,
        'payment_status': order.payment_status,
        'total': order.total,
        'items': [{
            'name': item.product.name,
            'quantity': item.quantity,
            'price': item.price
        } for item in order.items]
    })

@table_menu_bp.route('/mesa/sair')
def table_logout():
    session.pop('table_session', None)
    flash('Você saiu da sessão da mesa.', 'info')
    return redirect(url_for('main.index'))
