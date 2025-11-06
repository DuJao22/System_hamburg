from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Category, CartItem, Table, Comanda, ComandaItem, Extra, CartItemExtra
import qrcode
import io
import base64
from datetime import datetime

digital_menu_bp = Blueprint('digital_menu', __name__, url_prefix='/cardapio')

@digital_menu_bp.route('/')
def index():
    table_number = request.args.get('mesa')
    comanda_number = request.args.get('comanda')
    
    categories = Category.query.all()
    products = Product.query.filter_by(active=True).all()
    
    session['table_number'] = table_number
    session['comanda_number'] = comanda_number
    
    return render_template('digital_menu/index.html', 
                         categories=categories,
                         products=products,
                         table_number=table_number,
                         comanda_number=comanda_number)

@digital_menu_bp.route('/produto/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    extras = Extra.query.filter_by(active=True).all()
    
    return render_template('digital_menu/product_detail.html', 
                         product=product,
                         extras=extras)

@digital_menu_bp.route('/carrinho-temp')
def temp_cart():
    cart_items = session.get('temp_cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    return render_template('digital_menu/cart.html', 
                         cart_items=cart_items,
                         total=total)

@digital_menu_bp.route('/adicionar-temp/<int:product_id>', methods=['POST'])
def add_to_temp_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = request.form.get('quantity', 1, type=int)
    
    temp_cart = session.get('temp_cart', [])
    
    cart_item = {
        'product_id': product.id,
        'product_name': product.name,
        'price': product.price,
        'quantity': quantity,
        'image_url': product.image_url
    }
    
    temp_cart.append(cart_item)
    session['temp_cart'] = temp_cart
    
    flash(f'{product.name} adicionado ao carrinho!', 'success')
    return redirect(url_for('digital_menu.temp_cart'))

@digital_menu_bp.route('/finalizar-pedido', methods=['POST'])
def finalize_order():
    cart_items = session.get('temp_cart', [])
    if not cart_items:
        flash('Carrinho vazio!', 'warning')
        return redirect(url_for('digital_menu.index'))
    
    table_number = session.get('table_number')
    comanda_number = session.get('comanda_number')
    customer_name = request.form.get('customer_name', 'Cliente')
    
    comanda = None
    
    if comanda_number:
        comanda = Comanda.query.filter_by(comanda_number=comanda_number, status='open').first()
    
    if not comanda and table_number:
        table = Table.query.filter_by(table_number=table_number).first()
        if table:
            comanda = Comanda(
                comanda_number=f'AUTO-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                table_id=table.id,
                customer_name=customer_name
            )
            db.session.add(comanda)
            db.session.flush()
    
    if not comanda:
        comanda = Comanda(
            comanda_number=f'DIGITAL-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            customer_name=customer_name
        )
        db.session.add(comanda)
        db.session.flush()
    
    for item in cart_items:
        comanda_item = ComandaItem(
            comanda_id=comanda.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(comanda_item)
    
    comanda.total = comanda.calculate_total()
    db.session.commit()
    
    session.pop('temp_cart', None)
    session.pop('table_number', None)
    session.pop('comanda_number', None)
    
    flash(f'Pedido #{comanda.comanda_number} enviado com sucesso!', 'success')
    return redirect(url_for('digital_menu.order_success'))

@digital_menu_bp.route('/pedido-enviado')
def order_success():
    return render_template('digital_menu/order_success.html')

@digital_menu_bp.route('/acessar-mesa')
def customer_login():
    return render_template('digital_menu/customer_login.html')

@digital_menu_bp.route('/validar-pin', methods=['POST'])
def validate_pin():
    comanda_number = request.form.get('comanda_number')
    pin = request.form.get('pin')
    
    if not comanda_number or not pin:
        flash('Por favor, preencha todos os campos.', 'danger')
        return redirect(url_for('digital_menu.customer_login'))
    
    comanda = Comanda.query.filter_by(
        comanda_number=comanda_number,
        access_pin=pin,
        status='open'
    ).first()
    
    if not comanda:
        flash('Número da comanda ou PIN incorreto.', 'danger')
        return redirect(url_for('digital_menu.customer_login'))
    
    session['customer_comanda_id'] = comanda.id
    session['customer_authenticated'] = True
    
    flash(f'Bem-vindo! Você está acessando a comanda #{comanda.comanda_number}', 'success')
    return redirect(url_for('digital_menu.track_order'))

@digital_menu_bp.route('/acompanhar-pedido')
def track_order():
    if not session.get('customer_authenticated'):
        flash('Você precisa fazer login primeiro.', 'warning')
        return redirect(url_for('digital_menu.customer_login'))
    
    comanda_id = session.get('customer_comanda_id')
    if not comanda_id:
        flash('Sessão expirada. Faça login novamente.', 'warning')
        return redirect(url_for('digital_menu.customer_login'))
    
    comanda = Comanda.query.get_or_404(comanda_id)
    
    if comanda.status != 'open':
        flash('Esta comanda já foi fechada.', 'info')
        session.pop('customer_comanda_id', None)
        session.pop('customer_authenticated', None)
        return redirect(url_for('digital_menu.customer_login'))
    
    return render_template('digital_menu/track_order.html', comanda=comanda)

@digital_menu_bp.route('/sair-mesa')
def customer_logout():
    session.pop('customer_comanda_id', None)
    session.pop('customer_authenticated', None)
    flash('Você saiu da mesa com sucesso.', 'info')
    return redirect(url_for('digital_menu.customer_login'))

@digital_menu_bp.route('/api/status-pedido/<int:comanda_id>')
def get_order_status(comanda_id):
    if not session.get('customer_authenticated') or session.get('customer_comanda_id') != comanda_id:
        return jsonify({'error': 'Não autorizado'}), 403
    
    comanda = Comanda.query.get_or_404(comanda_id)
    
    items_data = []
    for item in comanda.items:
        items_data.append({
            'id': item.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.price),
            'status': item.status,
            'sent_to_kitchen': item.sent_to_kitchen,
            'notes': item.notes,
            'created_at': item.created_at.strftime('%H:%M')
        })
    
    return jsonify({
        'comanda_number': comanda.comanda_number,
        'table_number': comanda.table.table_number if comanda.table else 'Balcão',
        'total': float(comanda.calculate_total()),
        'items': items_data,
        'status': comanda.status
    })

@digital_menu_bp.route('/admin/gerar-qrcode/<int:table_id>')
@login_required
def generate_qrcode(table_id):
    if not current_user.is_admin:
        flash('Acesso restrito.', 'danger')
        return redirect(url_for('main.index'))
    
    table = Table.query.get_or_404(table_id)
    
    url = url_for('digital_menu.index', mesa=table.table_number, _external=True)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('digital_menu/qrcode.html', 
                         table=table,
                         qr_code=img_base64,
                         url=url)
