from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Table, Comanda, ComandaItem, Product, Order, OrderItem, User, CashRegister, CashMovement
from datetime import datetime

pdv_bp = Blueprint('pdv', __name__, url_prefix='/pdv')

def admin_or_waiter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Acesso restrito. Faça login.', 'danger')
            return redirect(url_for('auth.login'))
        if not (current_user.is_admin or current_user.role in ['waiter', 'manager']):
            flash('Acesso restrito a garçons e administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@pdv_bp.route('/')
@login_required
@admin_or_waiter_required
def index():
    tables = Table.query.order_by(Table.table_number).all()
    open_comandas = Comanda.query.filter_by(status='open').all()
    open_cash = CashRegister.query.filter_by(status='open').first()
    
    return render_template('pdv/index.html', 
                         tables=tables, 
                         open_comandas=open_comandas,
                         open_cash=open_cash)

@pdv_bp.route('/mesas')
@login_required
@admin_or_waiter_required
def tables():
    all_tables = Table.query.order_by(Table.table_number).all()
    return render_template('pdv/tables.html', tables=all_tables)

@pdv_bp.route('/mesa/adicionar', methods=['POST'])
@login_required
@admin_or_waiter_required
def add_table():
    table_number = request.form.get('table_number')
    capacity = request.form.get('capacity', 4, type=int)
    
    if Table.query.filter_by(table_number=table_number).first():
        flash('Mesa já existe!', 'warning')
        return redirect(url_for('pdv.tables'))
    
    table = Table(table_number=table_number, capacity=capacity)
    db.session.add(table)
    db.session.commit()
    
    flash(f'Mesa {table_number} adicionada com sucesso!', 'success')
    return redirect(url_for('pdv.tables'))

@pdv_bp.route('/mesa/<int:table_id>/abrir', methods=['POST'])
@login_required
@admin_or_waiter_required
def open_table(table_id):
    table = Table.query.get_or_404(table_id)
    
    if table.status == 'occupied':
        flash('Mesa já está ocupada!', 'warning')
        return redirect(url_for('pdv.tables'))
    
    try:
        table.status = 'occupied'
        table.opened_at = datetime.utcnow()
        table.waiter_id = current_user.id
        
        last_comanda = Comanda.query.order_by(Comanda.id.desc()).first()
        comanda_number = str((last_comanda.id if last_comanda else 0) + 1).zfill(6)
        
        comanda = Comanda(
            comanda_number=comanda_number,
            table_id=table_id,
            waiter_id=current_user.id
        )
        db.session.add(comanda)
        db.session.flush()
        db.session.commit()
        
        flash(f'Mesa {table.table_number} aberta! Comanda #{comanda_number} criada.', 'success')
        return redirect(url_for('pdv.comanda_detail', comanda_id=comanda.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao abrir mesa: {str(e)}', 'danger')
        return redirect(url_for('pdv.tables'))

@pdv_bp.route('/mesa/<int:table_id>')
@login_required
@admin_or_waiter_required
def table_detail(table_id):
    table = Table.query.get_or_404(table_id)
    products = Product.query.filter_by(active=True).all()
    comandas = Comanda.query.filter_by(table_id=table_id, status='open').all()
    
    return render_template('pdv/table_detail.html', 
                         table=table, 
                         products=products,
                         comandas=comandas)

@pdv_bp.route('/mesa/<int:table_id>/fechar', methods=['POST'])
@login_required
@admin_or_waiter_required
def close_table(table_id):
    table = Table.query.get_or_404(table_id)
    
    open_comandas = Comanda.query.filter_by(table_id=table_id, status='open').all()
    if open_comandas:
        flash('Feche todas as comandas antes de fechar a mesa!', 'danger')
        return redirect(url_for('pdv.table_detail', table_id=table_id))
    
    table.status = 'available'
    table.opened_at = None
    table.waiter_id = None
    table.current_order_id = None
    db.session.commit()
    
    flash(f'Mesa {table.table_number} fechada!', 'success')
    return redirect(url_for('pdv.tables'))

@pdv_bp.route('/comanda/criar', methods=['POST'])
@login_required
@admin_or_waiter_required
def create_comanda():
    table_id = request.form.get('table_id', type=int)
    customer_name = request.form.get('customer_name', '')
    
    last_comanda = Comanda.query.order_by(Comanda.id.desc()).first()
    comanda_number = str((last_comanda.id if last_comanda else 0) + 1).zfill(6)
    
    comanda = Comanda(
        comanda_number=comanda_number,
        table_id=table_id,
        customer_name=customer_name,
        waiter_id=current_user.id
    )
    db.session.add(comanda)
    db.session.commit()
    
    flash(f'Comanda #{comanda_number} criada!', 'success')
    return redirect(url_for('pdv.comanda_detail', comanda_id=comanda.id))

@pdv_bp.route('/comanda/<int:comanda_id>')
@login_required
@admin_or_waiter_required
def comanda_detail(comanda_id):
    from app.models import Category, Extra
    
    comanda = Comanda.query.get_or_404(comanda_id)
    categories = Category.query.all()
    products = Product.query.filter_by(active=True).all()
    extras = Extra.query.filter_by(active=True).all()
    
    return render_template('pdv/comanda_detail.html', 
                         comanda=comanda,
                         categories=categories, 
                         products=products,
                         extras=extras)

@pdv_bp.route('/comanda/<int:comanda_id>/adicionar-item', methods=['POST'])
@login_required
@admin_or_waiter_required
def add_comanda_item(comanda_id):
    from app.models import ComandaItemExtra, Extra
    
    comanda = Comanda.query.get_or_404(comanda_id)
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    notes = request.form.get('notes', '')
    
    product = Product.query.get_or_404(product_id)
    
    item = ComandaItem(
        comanda_id=comanda_id,
        product_id=product_id,
        quantity=quantity,
        price=product.price,
        notes=notes
    )
    db.session.add(item)
    db.session.flush()
    
    for field_name in request.form:
        if field_name.startswith('extra_'):
            extra_id = int(field_name.replace('extra_', ''))
            extra_quantity = int(request.form.get(field_name, 0))
            
            if extra_quantity > 0:
                extra = Extra.query.get(extra_id)
                if extra and extra.active:
                    comanda_item_extra = ComandaItemExtra(
                        comanda_item_id=item.id,
                        extra_id=extra.id,
                        quantity=extra_quantity,
                        price=extra.price
                    )
                    db.session.add(comanda_item_extra)
    
    comanda.total = comanda.calculate_total()
    db.session.commit()
    
    flash(f'{product.name} adicionado à comanda!', 'success')
    return redirect(url_for('pdv.comanda_detail', comanda_id=comanda_id))

@pdv_bp.route('/comanda/<int:comanda_id>/remover-item/<int:item_id>', methods=['POST'])
@login_required
@admin_or_waiter_required
def remove_comanda_item(comanda_id, item_id):
    item = ComandaItem.query.get_or_404(item_id)
    comanda = Comanda.query.get_or_404(comanda_id)
    
    db.session.delete(item)
    comanda.total = comanda.calculate_total()
    db.session.commit()
    
    flash('Item removido da comanda!', 'success')
    return redirect(url_for('pdv.comanda_detail', comanda_id=comanda_id))

@pdv_bp.route('/comanda/<int:comanda_id>/fechar', methods=['POST'])
@login_required
@admin_or_waiter_required
def close_comanda(comanda_id):
    comanda = Comanda.query.get_or_404(comanda_id)
    payment_method = request.form.get('payment_method', 'Dinheiro')
    
    comanda.status = 'closed'
    comanda.closed_at = datetime.utcnow()
    comanda.total = comanda.calculate_total()
    
    open_cash = CashRegister.query.filter_by(status='open').first()
    if open_cash:
        movement = CashMovement(
            cash_register_id=open_cash.id,
            movement_type='in',
            amount=comanda.total,
            description=f'Comanda #{comanda.comanda_number} - {payment_method}',
            created_by=current_user.id
        )
        db.session.add(movement)
    
    db.session.commit()
    
    flash(f'Comanda #{comanda.comanda_number} fechada! Total: R$ {comanda.total:.2f}', 'success')
    
    if comanda.table_id:
        return redirect(url_for('pdv.table_detail', table_id=comanda.table_id))
    return redirect(url_for('pdv.index'))

@pdv_bp.route('/comanda/<int:comanda_id>/enviar-cozinha', methods=['POST'])
@login_required
@admin_or_waiter_required
def send_to_kitchen(comanda_id):
    from app.models import KitchenOrder, KitchenOrderItem
    from flask_socketio import emit
    from app import socketio
    
    try:
        comanda = Comanda.query.get_or_404(comanda_id)
        
        pending_items = [item for item in comanda.items if not item.sent_to_kitchen]
        
        if not pending_items:
            return jsonify({'success': False, 'message': 'Nenhum item pendente para enviar'})
        
        kitchen_order = KitchenOrder(
            comanda_id=comanda_id,
            table_number=comanda.table.table_number if comanda.table else 'Balcão',
            waiter_id=current_user.id,
            status='pending'
        )
        db.session.add(kitchen_order)
        db.session.flush()
        
        for item in pending_items:
            item.sent_to_kitchen = True
            
            extras_list = ', '.join([f"{e.extra.name} ({e.quantity}x)" for e in item.extras]) if item.extras else None
            
            kitchen_item = KitchenOrderItem(
                kitchen_order_id=kitchen_order.id,
                product_name=item.product.name,
                quantity=item.quantity,
                extras=extras_list,
                notes=item.notes
            )
            db.session.add(kitchen_item)
        
        db.session.commit()
        
        try:
            socketio.emit('new_kitchen_order', {
                'order_id': kitchen_order.id,
                'table': kitchen_order.table_number,
                'items_count': len(pending_items)
            }, namespace='/kitchen')
        except:
            pass
        
        return jsonify({
            'success': True, 
            'message': f'{len(pending_items)} item(ns) enviado(s) para a cozinha'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@pdv_bp.route('/caixa')
@login_required
@admin_or_waiter_required
def cash_register():
    open_cash = CashRegister.query.filter_by(status='open').first()
    cash_history = CashRegister.query.filter_by(status='closed').order_by(CashRegister.closed_at.desc()).limit(10).all()
    
    return render_template('pdv/cash_register.html', 
                         open_cash=open_cash, 
                         cash_history=cash_history)

@pdv_bp.route('/caixa/abrir', methods=['POST'])
@login_required
@admin_or_waiter_required
def open_cash_register():
    existing_cash = CashRegister.query.filter_by(status='open').first()
    if existing_cash:
        flash('Já existe um caixa aberto!', 'warning')
        return redirect(url_for('pdv.cash_register'))
    
    opening_balance = request.form.get('opening_balance', 0, type=float)
    notes = request.form.get('notes', '')
    
    cash = CashRegister(
        user_id=current_user.id,
        opening_balance=opening_balance,
        notes=notes
    )
    db.session.add(cash)
    db.session.commit()
    
    flash('Caixa aberto com sucesso!', 'success')
    return redirect(url_for('pdv.cash_register'))

@pdv_bp.route('/caixa/fechar', methods=['POST'])
@login_required
@admin_or_waiter_required
def close_cash_register():
    cash = CashRegister.query.filter_by(status='open').first()
    if not cash:
        flash('Nenhum caixa aberto!', 'warning')
        return redirect(url_for('pdv.cash_register'))
    
    closing_balance = request.form.get('closing_balance', type=float)
    notes = request.form.get('notes', '')
    
    cash.closing_balance = closing_balance
    cash.expected_balance = cash.calculate_expected_balance()
    cash.difference = closing_balance - cash.expected_balance
    cash.closed_at = datetime.utcnow()
    cash.status = 'closed'
    if notes:
        cash.notes = f"{cash.notes}\n\nFechamento: {notes}" if cash.notes else notes
    
    db.session.commit()
    
    flash(f'Caixa fechado! Diferença: R$ {cash.difference:.2f}', 'success')
    return redirect(url_for('pdv.cash_register'))

@pdv_bp.route('/caixa/movimento', methods=['POST'])
@login_required
@admin_or_waiter_required
def add_cash_movement():
    cash = CashRegister.query.filter_by(status='open').first()
    if not cash:
        flash('Nenhum caixa aberto!', 'warning')
        return redirect(url_for('pdv.cash_register'))
    
    movement_type = request.form.get('movement_type')
    amount = request.form.get('amount', type=float)
    description = request.form.get('description', '')
    
    movement = CashMovement(
        cash_register_id=cash.id,
        movement_type=movement_type,
        amount=amount,
        description=description,
        created_by=current_user.id
    )
    db.session.add(movement)
    db.session.commit()
    
    flash('Movimentação registrada!', 'success')
    return redirect(url_for('pdv.cash_register'))
