from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import LoyaltyPoints, LoyaltyTransaction, User, Order, Coupon
from datetime import datetime, timedelta

loyalty_bp = Blueprint('loyalty', __name__, url_prefix='/fidelidade')

@loyalty_bp.route('/')
@login_required
def index():
    loyalty = LoyaltyPoints.query.filter_by(user_id=current_user.id).first()
    if not loyalty:
        loyalty = LoyaltyPoints(user_id=current_user.id)
        db.session.add(loyalty)
        db.session.commit()
    
    transactions = LoyaltyTransaction.query.filter_by(loyalty_points_id=loyalty.id).order_by(LoyaltyTransaction.created_at.desc()).limit(20).all()
    
    available_rewards = []
    if loyalty.points >= 100:
        available_rewards.append({'points': 100, 'reward': 'Desconto de R$ 10,00', 'value': 10})
    if loyalty.points >= 250:
        available_rewards.append({'points': 250, 'reward': 'Desconto de R$ 30,00', 'value': 30})
    if loyalty.points >= 500:
        available_rewards.append({'points': 500, 'reward': 'Desconto de R$ 70,00', 'value': 70})
    
    return render_template('loyalty/index.html', 
                         loyalty=loyalty, 
                         transactions=transactions,
                         available_rewards=available_rewards)

@loyalty_bp.route('/resgatar/<int:points_cost>', methods=['POST'])
@login_required
def redeem_points(points_cost):
    loyalty = LoyaltyPoints.query.filter_by(user_id=current_user.id).first()
    
    if not loyalty or loyalty.points < points_cost:
        flash('Pontos insuficientes!', 'danger')
        return redirect(url_for('loyalty.index'))
    
    rewards = {
        100: 10,
        250: 30,
        500: 70
    }
    
    if points_cost not in rewards:
        flash('Recompensa inválida!', 'danger')
        return redirect(url_for('loyalty.index'))
    
    discount_value = rewards[points_cost]
    
    coupon_code = f'FIDELIDADE{current_user.id}{datetime.now().strftime("%Y%m%d%H%M%S")}'
    coupon = Coupon(
        code=coupon_code,
        discount_type='fixed',
        discount_value=discount_value,
        min_purchase=0,
        max_uses=1,
        valid_until=datetime.utcnow() + timedelta(days=30),
        active=True
    )
    db.session.add(coupon)
    
    loyalty.points -= points_cost
    loyalty.total_spent += points_cost
    
    transaction = LoyaltyTransaction(
        loyalty_points_id=loyalty.id,
        points=-points_cost,
        transaction_type='redeem',
        description=f'Resgate: Cupom de R$ {discount_value:.2f} - Código: {coupon_code}'
    )
    db.session.add(transaction)
    db.session.commit()
    
    flash(f'Parabéns! Seu cupom {coupon_code} de R$ {discount_value:.2f} foi criado! Válido por 30 dias.', 'success')
    return redirect(url_for('loyalty.index'))

def add_points_for_order(order_id):
    order = Order.query.get(order_id)
    if not order or order.payment_status != 'Aprovado':
        return
    
    loyalty = LoyaltyPoints.query.filter_by(user_id=order.user_id).first()
    if not loyalty:
        loyalty = LoyaltyPoints(user_id=order.user_id)
        db.session.add(loyalty)
    
    points_earned = int(order.total)
    
    loyalty.points += points_earned
    loyalty.total_earned += points_earned
    
    transaction = LoyaltyTransaction(
        loyalty_points_id=loyalty.id,
        points=points_earned,
        transaction_type='earn',
        description=f'Pedido #{order.id}',
        order_id=order.id
    )
    db.session.add(transaction)
    db.session.commit()
    
    return points_earned
