from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Order, StoreSettings
import mercadopago
import os

payment_bp = Blueprint('payment', __name__)

def get_mp_sdk():
    access_token = os.getenv('MERCADOPAGO_ACCESS_TOKEN')
    if not access_token:
        return None
    return mercadopago.SDK(access_token)

@payment_bp.route('/criar-preferencia/<int:order_id>', methods=['GET', 'POST'])
@login_required
def create_preference(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('cart.my_orders'))
    
    sdk = get_mp_sdk()
    if not sdk:
        flash('Configuração de pagamento não encontrada. Entre em contato com o suporte.', 'danger')
        return redirect(url_for('cart.my_orders'))
    
    base_url = request.url_root.rstrip('/')
    
    items = []
    for item in order.items:
        items.append({
            "title": item.product.name,
            "quantity": item.quantity,
            "unit_price": float(item.price),
            "currency_id": "BRL"
        })
    
    if order.shipping_cost > 0:
        items.append({
            "title": "Frete",
            "quantity": 1,
            "unit_price": float(order.shipping_cost),
            "currency_id": "BRL"
        })
    
    preference_data = {
        "items": items,
        "payer": {
            "name": order.customer_name,
            "phone": {
                "number": order.customer_phone
            },
            "email": current_user.email
        },
        "back_urls": {
            "success": f"{base_url}/pagamento/sucesso",
            "failure": f"{base_url}/pagamento/falha",
            "pending": f"{base_url}/pagamento/pendente"
        },
        "auto_return": "approved",
        "external_reference": str(order.id),
        "notification_url": f"{base_url}/pagamento/webhook",
        "statement_descriptor": "SANDWICH GOURMET"
    }
    
    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        
        return redirect(preference["init_point"])
    except Exception as e:
        flash(f'Erro ao criar pagamento: {str(e)}', 'danger')
        return redirect(url_for('cart.my_orders'))

@payment_bp.route('/sucesso')
@login_required
def payment_success():
    payment_id = request.args.get('payment_id')
    status = request.args.get('status')
    external_reference = request.args.get('external_reference')
    
    order = None
    if external_reference:
        order = Order.query.get(int(external_reference))
        if order and order.user_id == current_user.id:
            order.payment_status = 'Aprovado'
            order.payment_id = payment_id
            order.status = 'Confirmado'
            db.session.commit()
    
    return render_template('payment_success.html', payment_id=payment_id, order=order)

@payment_bp.route('/falha')
@login_required
def payment_failure():
    payment_id = request.args.get('payment_id')
    external_reference = request.args.get('external_reference')
    
    order = None
    if external_reference:
        order = Order.query.get(int(external_reference))
        if order and order.user_id == current_user.id:
            order.payment_status = 'Rejeitado'
            order.payment_id = payment_id
            db.session.commit()
    
    return render_template('payment_failure.html', order=order)

@payment_bp.route('/pendente')
@login_required
def payment_pending():
    payment_id = request.args.get('payment_id')
    external_reference = request.args.get('external_reference')
    
    order = None
    if external_reference:
        order = Order.query.get(int(external_reference))
        if order and order.user_id == current_user.id:
            order.payment_status = 'Pendente'
            order.payment_id = payment_id
            db.session.commit()
    
    return render_template('payment_pending.html', order=order)

@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    topic = request.args.get('topic') or request.args.get('type')
    
    if topic == 'payment':
        payment_id = request.args.get('id') or request.args.get('data.id')
        
        sdk = get_mp_sdk()
        if not sdk:
            return jsonify({'error': 'SDK not configured'}), 500
        
        try:
            payment_info = sdk.payment().get(payment_id)
            payment = payment_info["response"]
            
            external_reference = payment.get('external_reference')
            if external_reference:
                order = Order.query.get(int(external_reference))
                if order:
                    order.payment_id = str(payment['id'])
                    
                    if payment['status'] == 'approved':
                        order.payment_status = 'Aprovado'
                        order.status = 'Confirmado'
                    elif payment['status'] == 'pending':
                        order.payment_status = 'Pendente'
                    elif payment['status'] == 'rejected':
                        order.payment_status = 'Rejeitado'
                    elif payment['status'] == 'refunded':
                        order.payment_status = 'Reembolsado'
                        order.status = 'Cancelado'
                    
                    db.session.commit()
        except Exception as e:
            print(f"Webhook error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'status': 'ok'}), 200
