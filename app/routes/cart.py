from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models import Product, CartItem, Order, OrderItem, Coupon, StoreSettings, Extra, CartItemExtra, OrderItemExtra

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/carrinho')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(
        (item.product.price + sum(extra.extra.price for extra in item.extras)) * item.quantity 
        for item in cart_items
    )
    
    coupon_code = session.get('coupon_code')
    coupon = None
    discount = 0
    total = subtotal
    
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        if coupon:
            is_valid, message = coupon.is_valid()
            if is_valid and subtotal >= coupon.min_purchase:
                discount = coupon.calculate_discount(subtotal)
                total = subtotal - discount
            else:
                session.pop('coupon_code', None)
                coupon = None
    
    pickup_enabled = StoreSettings.get_setting('pickup_enabled', 'true') == 'true'
    pickup_address = StoreSettings.get_setting('pickup_address', '')
    delivery_enabled = StoreSettings.get_setting('delivery_enabled', 'true') == 'true'
    shipping_cost = float(StoreSettings.get_setting('shipping_cost', '15'))
    free_shipping_min = float(StoreSettings.get_setting('free_shipping_min', '300'))
    
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal, 
                         discount=discount, total=total, coupon=coupon,
                         pickup_enabled=pickup_enabled, pickup_address=pickup_address,
                         delivery_enabled=delivery_enabled, shipping_cost=shipping_cost,
                         free_shipping_min=free_shipping_min)

@cart_bp.route('/adicionar-carrinho/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    extra_ids = request.form.getlist('extras')
    
    if product.stock < quantity:
        flash('Quantidade indisponível em estoque.', 'warning')
        return redirect(url_for('main.product_detail', product_id=product_id))
    
    cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
    db.session.add(cart_item)
    db.session.flush()
    
    if extra_ids:
        for extra_id in extra_ids:
            extra = Extra.query.get(int(extra_id))
            if extra and extra.active:
                cart_item_extra = CartItemExtra(cart_item_id=cart_item.id, extra_id=extra.id, quantity=1)
                db.session.add(cart_item_extra)
    
    db.session.commit()
    flash(f'{product.name} adicionado ao carrinho!', 'success')
    
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/remover-carrinho/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removido do carrinho.', 'info')
    
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/atualizar-carrinho/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity < 1:
        return jsonify({'success': False, 'message': 'Quantidade inválida'}), 400
    
    if cart_item.product.stock < quantity:
        return jsonify({'success': False, 'message': 'Quantidade indisponível'}), 400
    
    cart_item.quantity = quantity
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Carrinho atualizado'})

@cart_bp.route('/aplicar-cupom', methods=['POST'])
@login_required
def apply_coupon():
    coupon_code = request.form.get('coupon_code', '').strip().upper()
    
    if not coupon_code:
        flash('Digite um código de cupom.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    coupon = Coupon.query.filter_by(code=coupon_code).first()
    
    if not coupon:
        flash('Cupom inválido.', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    is_valid, message = coupon.is_valid()
    if not is_valid:
        flash(message, 'danger')
        return redirect(url_for('cart.view_cart'))
    
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    
    if subtotal < coupon.min_purchase:
        flash(f'Compra mínima de R$ {coupon.min_purchase:.2f} necessária para usar este cupom.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    session['coupon_code'] = coupon_code
    flash(f'Cupom {coupon_code} aplicado com sucesso!', 'success')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/remover-cupom', methods=['POST'])
@login_required
def remove_coupon():
    session.pop('coupon_code', None)
    flash('Cupom removido.', 'info')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/finalizar-compra', methods=['POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Seu carrinho está vazio.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    delivery_type = request.form.get('delivery_type', 'delivery')
    customer_name = request.form.get('customer_name', '').strip()
    customer_phone = request.form.get('customer_phone', '').strip()
    delivery_address = request.form.get('delivery_address', '').strip()
    observations = request.form.get('observations', '').strip()
    
    if not customer_name or not customer_phone:
        flash('Por favor, preencha seu nome e telefone.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    if delivery_type == 'delivery' and not delivery_address:
        flash('Por favor, preencha o endereço de entrega.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    subtotal = sum(
        (item.product.price + sum(extra.extra.price for extra in item.extras)) * item.quantity 
        for item in cart_items
    )
    discount = 0
    applied_coupon = None
    
    coupon_code = session.get('coupon_code')
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        if coupon:
            is_valid, message = coupon.is_valid()
            if not is_valid:
                session.pop('coupon_code', None)
                flash(f'Cupom não pôde ser aplicado: {message}', 'warning')
            elif subtotal < coupon.min_purchase:
                session.pop('coupon_code', None)
                flash(f'Cupom não pôde ser aplicado: compra mínima de R$ {coupon.min_purchase:.2f} necessária.', 'warning')
            else:
                discount = coupon.calculate_discount(subtotal)
                applied_coupon = coupon
    
    shipping_cost = 0
    if delivery_type == 'delivery':
        shipping_cost_setting = float(StoreSettings.get_setting('shipping_cost', '15'))
        free_shipping_min = float(StoreSettings.get_setting('free_shipping_min', '300'))
        if subtotal < free_shipping_min:
            shipping_cost = shipping_cost_setting
    
    total = subtotal - discount + shipping_cost
    
    order = Order(
        user_id=current_user.id, 
        total=total, 
        status='Pendente',
        payment_status='Pendente',
        delivery_type=delivery_type,
        delivery_address=delivery_address if delivery_type == 'delivery' else None,
        customer_name=customer_name,
        customer_phone=customer_phone,
        shipping_cost=shipping_cost,
        discount_amount=discount,
        coupon_code=coupon_code if applied_coupon else None,
        observations=observations
    )
    db.session.add(order)
    db.session.flush()
    
    for cart_item in cart_items:
        if cart_item.product.stock < cart_item.quantity:
            flash(f'Produto {cart_item.product.name} sem estoque suficiente.', 'danger')
            db.session.rollback()
            return redirect(url_for('cart.view_cart'))
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=cart_item.product.price
        )
        db.session.add(order_item)
        db.session.flush()
        
        for cart_extra in cart_item.extras:
            order_item_extra = OrderItemExtra(
                order_item_id=order_item.id,
                extra_id=cart_extra.extra_id,
                quantity=cart_extra.quantity,
                price=cart_extra.extra.price
            )
            db.session.add(order_item_extra)
        
        cart_item.product.stock -= cart_item.quantity
        db.session.delete(cart_item)
    
    if applied_coupon:
        applied_coupon.times_used += 1
        db.session.add(applied_coupon)
    
    db.session.commit()
    session.pop('coupon_code', None)
    
    flash(f'Pedido #{order.id} criado! Prossiga para o pagamento.', 'success')
    return redirect(url_for('payment.create_preference', order_id=order.id))

@cart_bp.route('/meus-pedidos')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)
