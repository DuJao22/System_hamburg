from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app import db
from app.models import Product, Category, Order, User, Coupon, StoreSettings, Slide, Extra
from datetime import datetime
import os
import secrets

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Estatísticas de estoque
    low_stock_products = Product.query.filter(Product.stock < 10).count()
    out_of_stock = Product.query.filter(Product.stock == 0).count()
    
    # Estatísticas de pedidos
    pending_orders = Order.query.filter_by(status='Pendente').count()
    confirmed_orders = Order.query.filter_by(status='Confirmado').count()
    
    # Receita total (apenas pedidos confirmados)
    total_revenue = db.session.query(db.func.sum(Order.total)).filter(Order.status == 'Confirmado').scalar() or 0
    
    # Produtos mais vendidos (top 5) - apenas pedidos confirmados
    from app.models import OrderItem
    from sqlalchemy import func
    best_sellers = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold')
    ).join(OrderItem).join(Order).filter(Order.status == 'Confirmado').group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_products=total_products,
                         total_orders=total_orders,
                         total_users=total_users,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products,
                         out_of_stock=out_of_stock,
                         pending_orders=pending_orders,
                         confirmed_orders=confirmed_orders,
                         total_revenue=total_revenue,
                         best_sellers=best_sellers)

@admin_bp.route('/produtos')
@login_required
@admin_required
def products():
    search = request.args.get('search', '')
    category_id = request.args.get('category', '')
    status = request.args.get('status', '')
    stock_alert = request.args.get('stock_alert', '')
    
    query = Product.query
    
    if search:
        query = query.filter(
            or_(
                Product.name.contains(search),
                Product.code.contains(search),
                Product.description.contains(search)
            )
        )
    
    if category_id and category_id.isdigit():
        query = query.filter_by(category_id=int(category_id))
    
    if status == 'active':
        query = query.filter_by(active=True)
    elif status == 'inactive':
        query = query.filter_by(active=False)
    
    if stock_alert == 'low':
        query = query.filter(Product.stock < 10)
    
    products = query.all()
    categories = Category.query.all()
    
    low_stock_count = Product.query.filter(Product.stock < 10).count()
    
    return render_template('admin/products.html', 
                         products=products, 
                         categories=categories,
                         low_stock_count=low_stock_count,
                         search=search,
                         category_id=category_id,
                         status=status,
                         stock_alert=stock_alert)

@admin_bp.route('/produtos/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        category_id = int(request.form.get('category_id'))
        image_url = request.form.get('image_url')
        image_url_2 = request.form.get('image_url_2')
        image_url_3 = request.form.get('image_url_3')
        image_url_4 = request.form.get('image_url_4')
        image_url_5 = request.form.get('image_url_5')
        featured = request.form.get('featured') == 'on'
        
        product = Product(
            name=name,
            code=code,
            description=description,
            price=price,
            stock=stock,
            category_id=category_id,
            image_url=image_url,
            image_url_2=image_url_2 if image_url_2 else None,
            image_url_3=image_url_3 if image_url_3 else None,
            image_url_4=image_url_4 if image_url_4 else None,
            image_url_5=image_url_5 if image_url_5 else None,
            featured=featured
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('admin.products'))
    
    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories)

@admin_bp.route('/produtos/editar/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.code = request.form.get('code')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.category_id = int(request.form.get('category_id'))
        product.image_url = request.form.get('image_url')
        product.image_url_2 = request.form.get('image_url_2') if request.form.get('image_url_2') else None
        product.image_url_3 = request.form.get('image_url_3') if request.form.get('image_url_3') else None
        product.image_url_4 = request.form.get('image_url_4') if request.form.get('image_url_4') else None
        product.image_url_5 = request.form.get('image_url_5') if request.form.get('image_url_5') else None
        product.featured = request.form.get('featured') == 'on'
        product.active = request.form.get('active') == 'on'
        
        db.session.commit()
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin.products'))
    
    categories = Category.query.all()
    return render_template('admin/edit_product.html', product=product, categories=categories)

@admin_bp.route('/produtos/deletar/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    
    flash('Produto deletado com sucesso!', 'success')
    return redirect(url_for('admin.products'))

@admin_bp.route('/categorias')
@login_required
@admin_required
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categorias/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        
        # Processar upload de imagem
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                # Gerar nome seguro para o arquivo
                filename = secure_filename(file.filename)
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Validar extensão
                allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
                if file_ext in allowed_extensions:
                    # Gerar nome único
                    unique_filename = f"category_{secrets.token_hex(8)}{file_ext}"
                    
                    # Salvar arquivo
                    upload_path = os.path.join('app', 'static', 'images', unique_filename)
                    file.save(upload_path)
                    
                    # Atualizar image_url com o caminho do arquivo
                    image_url = f'/static/images/{unique_filename}'
                else:
                    flash('Formato de imagem não permitido! Use JPG, PNG, GIF ou WEBP.', 'danger')
                    return redirect(url_for('admin.add_category'))
        
        category = Category(name=name, description=description, image_url=image_url)
        db.session.add(category)
        db.session.commit()
        
        flash('Categoria adicionada com sucesso!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/add_category.html')

@admin_bp.route('/categorias/editar/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        
        # Processar upload de nova imagem
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                # Gerar nome seguro para o arquivo
                filename = secure_filename(file.filename)
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Validar extensão
                allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
                if file_ext in allowed_extensions:
                    # Gerar nome único
                    unique_filename = f"category_{secrets.token_hex(8)}{file_ext}"
                    
                    # Salvar arquivo
                    upload_path = os.path.join('app', 'static', 'images', unique_filename)
                    file.save(upload_path)
                    
                    # Atualizar image_url com o caminho do arquivo
                    category.image_url = f'/static/images/{unique_filename}'
                else:
                    flash('Formato de imagem não permitido! Use JPG, PNG, GIF ou WEBP.', 'danger')
                    return redirect(url_for('admin.edit_category', category_id=category_id))
        
        # Se não houver upload, verificar se há URL
        if not category.image_url or request.form.get('image_url'):
            image_url = request.form.get('image_url')
            if image_url:
                category.image_url = image_url
        
        db.session.commit()
        
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/edit_category.html', category=category)

@admin_bp.route('/categorias/deletar/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    if category.products:
        flash('Não é possível deletar uma categoria com produtos.', 'danger')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Categoria deletada com sucesso!', 'success')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/pedidos')
@login_required
@admin_required
def orders():
    from sqlalchemy import func, or_
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = Order.query
    
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    payment_filter = request.args.get('payment_status')
    if payment_filter:
        query = query.filter_by(payment_status=payment_filter)
    
    search = request.args.get('search', '').strip()
    if search:
        search_digits = ''.join(filter(str.isdigit, search))
        query = query.join(User).filter(
            or_(
                Order.id == int(search) if search.isdigit() else False,
                User.username.contains(search),
                User.email.contains(search),
                User.cpf.contains(search_digits) if search_digits else False,
                Order.customer_phone.contains(search_digits) if search_digits else False,
                Order.customer_name.contains(search)
            )
        )
    
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Order.created_at >= date_from_obj)
    if date_to:
        from datetime import datetime
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
        query = query.filter(Order.created_at <= date_to_obj)
    
    min_value = request.args.get('min_value', type=float)
    max_value = request.args.get('max_value', type=float)
    if min_value is not None:
        query = query.filter(Order.total >= min_value)
    if max_value is not None:
        query = query.filter(Order.total <= max_value)
    
    delivery_type = request.args.get('delivery_type')
    if delivery_type:
        query = query.filter_by(delivery_type=delivery_type)
    
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_by == 'created_at':
        query = query.order_by(Order.created_at.desc() if sort_order == 'desc' else Order.created_at.asc())
    elif sort_by == 'total':
        query = query.order_by(Order.total.desc() if sort_order == 'desc' else Order.total.asc())
    elif sort_by == 'status':
        query = query.order_by(Order.status.asc() if sort_order == 'asc' else Order.status.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    orders_list = pagination.items
    
    total_orders = Order.query.count()
    total_revenue = db.session.query(func.sum(Order.total)).filter(Order.status.in_(['Confirmado', 'Enviado', 'Entregue'])).scalar() or 0
    pending_orders = Order.query.filter_by(status='Pendente').count()
    
    status_counts = {}
    for status in ['Pendente', 'Confirmado', 'Enviado', 'Entregue', 'Cancelado']:
        status_counts[status] = Order.query.filter_by(status=status).count()
    
    return render_template('admin/orders.html', 
                         orders=orders_list,
                         pagination=pagination,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         pending_orders=pending_orders,
                         status_counts=status_counts)

@admin_bp.route('/pedidos/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/pedidos/atualizar-status/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    from app.models import OrderStatusHistory
    
    order = Order.query.get_or_404(order_id)
    old_status = order.status
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    if old_status != new_status:
        order.status = new_status
        
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.username,
            notes=notes
        )
        db.session.add(history)
        db.session.commit()
        
        flash(f'Status do pedido atualizado de "{old_status}" para "{new_status}"!', 'success')
    else:
        flash('Status não foi alterado.', 'info')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

@admin_bp.route('/pedidos/<int:order_id>/aceitar', methods=['POST'])
@login_required
@admin_required
def accept_order(order_id):
    from app.models import OrderStatusHistory
    from app.routes.websocket import notify_order_update
    from flask import session
    
    if not session.get('csrf_token_validated'):
        data = request.get_json() or {}
        csrf_token = data.get('csrf_token') or request.headers.get('X-CSRFToken')
        if not csrf_token or csrf_token != session.get('_csrf_token'):
            return jsonify({'success': False, 'message': 'Token CSRF inválido'}), 403
    
    order = Order.query.get_or_404(order_id)
    
    if order.status == 'Pendente':
        old_status = order.status
        order.status = 'Confirmado'
        order.accepted_at = datetime.utcnow()
        
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status='Confirmado',
            changed_by=current_user.username,
            notes='Pedido aceito automaticamente'
        )
        db.session.add(history)
        db.session.commit()
        
        notify_order_update(order)
        
        return jsonify({'success': True, 'message': 'Pedido aceito!', 'status': 'Confirmado'})
    
    return jsonify({'success': False, 'message': 'Pedido já foi processado'})

@admin_bp.route('/pedidos/<int:order_id>/rejeitar', methods=['POST'])
@login_required
@admin_required
def reject_order(order_id):
    from app.models import OrderStatusHistory
    from app.routes.websocket import notify_order_update
    from flask import session
    
    if not session.get('csrf_token_validated'):
        data_check = request.get_json() or {}
        csrf_token = data_check.get('csrf_token') or request.headers.get('X-CSRFToken')
        if not csrf_token or csrf_token != session.get('_csrf_token'):
            return jsonify({'success': False, 'message': 'Token CSRF inválido'}), 403
    
    order = Order.query.get_or_404(order_id)
    data = request.get_json() or {}
    reason = data.get('reason', 'Pedido rejeitado pelo administrador')
    
    if order.status == 'Pendente':
        old_status = order.status
        order.status = 'Cancelado'
        
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status='Cancelado',
            changed_by=current_user.username,
            notes=reason
        )
        db.session.add(history)
        db.session.commit()
        
        notify_order_update(order)
        
        return jsonify({'success': True, 'message': 'Pedido rejeitado!', 'status': 'Cancelado'})
    
    return jsonify({'success': False, 'message': 'Pedido já foi processado'})

@admin_bp.route('/pedidos/<int:order_id>/tempo-estimado', methods=['POST'])
@login_required
@admin_required
def update_estimated_time(order_id):
    from app.routes.websocket import notify_order_update
    
    order = Order.query.get_or_404(order_id)
    data = request.get_json() or {}
    
    prep_time = data.get('prep_time')
    delivery_time = data.get('delivery_time')
    
    if prep_time is not None:
        order.estimated_prep_time = int(prep_time)
    
    if delivery_time is not None:
        order.estimated_delivery_time = int(delivery_time)
    
    db.session.commit()
    
    notify_order_update(order)
    
    return jsonify({'success': True, 'message': 'Tempo estimado atualizado!'})

@admin_bp.route('/pedidos/<int:order_id>/imprimir', methods=['GET'])
@login_required
@admin_required
def print_order(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/print_order.html', order=order)

@admin_bp.route('/pedidos/<int:order_id>/nota', methods=['POST'])
@login_required
@admin_required
def add_order_note(order_id):
    from app.models import OrderNote
    
    order = Order.query.get_or_404(order_id)
    note_text = request.form.get('note', '').strip()
    is_internal = request.form.get('is_internal') == 'on'
    
    if note_text:
        note = OrderNote(
            order_id=order.id,
            note=note_text,
            created_by=current_user.username,
            is_internal=is_internal
        )
        db.session.add(note)
        db.session.commit()
        flash('Nota adicionada com sucesso!', 'success')
    else:
        flash('Nota não pode ser vazia.', 'warning')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

@admin_bp.route('/pedidos/exportar')
@login_required
@admin_required
def export_orders():
    import csv
    from io import StringIO
    from flask import make_response
    
    status_filter = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Order.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if date_from:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Order.created_at >= date_from_obj)
    
    if date_to:
        from datetime import datetime
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
        query = query.filter(Order.created_at <= date_to_obj)
    
    orders_list = query.order_by(Order.created_at.desc()).all()
    
    si = StringIO()
    writer = csv.writer(si)
    
    writer.writerow(['ID', 'Data', 'Cliente', 'Email', 'CPF', 'Telefone', 'Total', 'Status', 
                     'Status Pagamento', 'Tipo Entrega', 'Endereço', 'Frete', 'Desconto'])
    
    for order in orders_list:
        cpf = ''
        if order.user.cpf and len(order.user.cpf) == 11:
            cpf = f"{order.user.cpf[0:3]}.{order.user.cpf[3:6]}.{order.user.cpf[6:9]}-{order.user.cpf[9:11]}"
        elif order.user.cpf:
            cpf = order.user.cpf
        
        writer.writerow([
            order.id,
            order.created_at.strftime('%d/%m/%Y %H:%M'),
            order.user.username,
            order.user.email,
            cpf,
            order.customer_phone or order.user.phone or '',
            f'R$ {order.total:.2f}',
            order.status,
            order.payment_status,
            'Retirada' if order.delivery_type == 'pickup' else 'Entrega',
            order.delivery_address or '',
            f'R$ {order.shipping_cost:.2f}' if order.shipping_cost else 'R$ 0,00',
            f'R$ {order.discount_amount:.2f}' if hasattr(order, 'discount_amount') and order.discount_amount else 'R$ 0,00'
        ])
    
    output = make_response(si.getvalue())
    output.headers['Content-Disposition'] = 'attachment; filename=pedidos.csv'
    output.headers['Content-type'] = 'text/csv; charset=utf-8'
    
    return output

@admin_bp.route('/pedidos/estatisticas')
@login_required
@admin_required
def order_statistics():
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'today': {
            'orders': Order.query.filter(func.date(Order.created_at) == today).count(),
            'revenue': db.session.query(func.sum(Order.total)).filter(
                func.date(Order.created_at) == today,
                Order.status.in_(['Confirmado', 'Enviado', 'Entregue'])
            ).scalar() or 0
        },
        'week': {
            'orders': Order.query.filter(func.date(Order.created_at) >= week_ago).count(),
            'revenue': db.session.query(func.sum(Order.total)).filter(
                func.date(Order.created_at) >= week_ago,
                Order.status.in_(['Confirmado', 'Enviado', 'Entregue'])
            ).scalar() or 0
        },
        'month': {
            'orders': Order.query.filter(func.date(Order.created_at) >= month_ago).count(),
            'revenue': db.session.query(func.sum(Order.total)).filter(
                func.date(Order.created_at) >= month_ago,
                Order.status.in_(['Confirmado', 'Enviado', 'Entregue'])
            ).scalar() or 0
        }
    }
    
    from app.models import OrderItem
    best_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
    ).join(OrderItem).join(Order).filter(
        Order.status.in_(['Confirmado', 'Enviado', 'Entregue']),
        func.date(Order.created_at) >= month_ago
    ).group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc()).limit(10).all()
    
    daily_sales = db.session.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('orders'),
        func.sum(Order.total).label('revenue')
    ).filter(
        func.date(Order.created_at) >= month_ago,
        Order.status.in_(['Confirmado', 'Enviado', 'Entregue'])
    ).group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()
    
    return jsonify({
        'stats': stats,
        'best_products': [{'name': p[0], 'quantity': int(p[1]), 'revenue': float(p[2])} for p in best_products],
        'daily_sales': [{'date': str(d[0]), 'orders': d[1], 'revenue': float(d[2] or 0)} for d in daily_sales]
    })

@admin_bp.route('/cupons')
@login_required
@admin_required
def coupons():
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)

@admin_bp.route('/cupons/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_coupon():
    if request.method == 'POST':
        code = request.form.get('code').strip().upper()
        discount_type = request.form.get('discount_type')
        discount_value = float(request.form.get('discount_value'))
        min_purchase = float(request.form.get('min_purchase', 0))
        max_uses = request.form.get('max_uses')
        valid_until = request.form.get('valid_until')
        
        if Coupon.query.filter_by(code=code).first():
            flash('Código de cupom já existe!', 'danger')
            return redirect(url_for('admin.add_coupon'))
        
        coupon = Coupon(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            min_purchase=min_purchase,
            max_uses=int(max_uses) if max_uses else None,
            valid_until=datetime.strptime(valid_until, '%Y-%m-%d') if valid_until else None
        )
        
        db.session.add(coupon)
        db.session.commit()
        
        flash('Cupom criado com sucesso!', 'success')
        return redirect(url_for('admin.coupons'))
    
    return render_template('admin/add_coupon.html')

@admin_bp.route('/cupons/editar/<int:coupon_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    
    if request.method == 'POST':
        coupon.discount_type = request.form.get('discount_type')
        coupon.discount_value = float(request.form.get('discount_value'))
        coupon.min_purchase = float(request.form.get('min_purchase', 0))
        max_uses = request.form.get('max_uses')
        coupon.max_uses = int(max_uses) if max_uses else None
        valid_until = request.form.get('valid_until')
        coupon.valid_until = datetime.strptime(valid_until, '%Y-%m-%d') if valid_until else None
        coupon.active = request.form.get('active') == 'on'
        
        db.session.commit()
        flash('Cupom atualizado com sucesso!', 'success')
        return redirect(url_for('admin.coupons'))
    
    return render_template('admin/edit_coupon.html', coupon=coupon)

@admin_bp.route('/cupons/deletar/<int:coupon_id>', methods=['POST'])
@login_required
@admin_required
def delete_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    db.session.delete(coupon)
    db.session.commit()
    
    flash('Cupom deletado com sucesso!', 'success')
    return redirect(url_for('admin.coupons'))

@admin_bp.route('/cupons/toggle/<int:coupon_id>', methods=['POST'])
@login_required
@admin_required
def toggle_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    coupon.active = not coupon.active
    db.session.commit()
    
    status = 'ativado' if coupon.active else 'desativado'
    flash(f'Cupom {status} com sucesso!', 'success')
    return redirect(url_for('admin.coupons'))

@admin_bp.route('/extras')
@login_required
@admin_required
def extras():
    extras_list = Extra.query.order_by(Extra.created_at.desc()).all()
    return render_template('admin/extras.html', extras=extras_list)

@admin_bp.route('/extras/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_extra():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        active = request.form.get('active') == 'on'
        
        extra = Extra(name=name, description=description, price=price, active=active)
        db.session.add(extra)
        db.session.commit()
        
        flash('Extra adicionado com sucesso!', 'success')
        return redirect(url_for('admin.extras'))
    
    return render_template('admin/add_extra.html')

@admin_bp.route('/extras/editar/<int:extra_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_extra(extra_id):
    extra = Extra.query.get_or_404(extra_id)
    
    if request.method == 'POST':
        extra.name = request.form.get('name')
        extra.description = request.form.get('description')
        extra.price = float(request.form.get('price'))
        extra.active = request.form.get('active') == 'on'
        
        db.session.commit()
        flash('Extra atualizado com sucesso!', 'success')
        return redirect(url_for('admin.extras'))
    
    return render_template('admin/edit_extra.html', extra=extra)

@admin_bp.route('/extras/deletar/<int:extra_id>', methods=['POST'])
@login_required
@admin_required
def delete_extra(extra_id):
    csrf_token = request.form.get('csrf_token')
    if not csrf_token or csrf_token != session.get('_csrf_token'):
        flash('Ação não autorizada.', 'danger')
        return redirect(url_for('admin.extras'))
    
    extra = Extra.query.get_or_404(extra_id)
    db.session.delete(extra)
    db.session.commit()
    
    flash('Extra deletado com sucesso!', 'success')
    return redirect(url_for('admin.extras'))

@admin_bp.route('/extras/toggle/<int:extra_id>', methods=['POST'])
@login_required
@admin_required
def toggle_extra(extra_id):
    csrf_token = request.form.get('csrf_token')
    if not csrf_token or csrf_token != session.get('_csrf_token'):
        flash('Ação não autorizada.', 'danger')
        return redirect(url_for('admin.extras'))
    
    extra = Extra.query.get_or_404(extra_id)
    extra.active = not extra.active
    db.session.commit()
    
    status = 'ativado' if extra.active else 'desativado'
    flash(f'Extra {status} com sucesso!', 'success')
    return redirect(url_for('admin.extras'))

@admin_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
@admin_required
def store_settings():
    if request.method == 'POST':
        StoreSettings.set_setting('store_name', request.form.get('store_name', 'Sandwich Gourmet'))
        StoreSettings.set_setting('store_logo', request.form.get('store_logo', ''))
        StoreSettings.set_setting('store_description', request.form.get('store_description', ''))
        StoreSettings.set_setting('pickup_enabled', 'true' if request.form.get('pickup_enabled') else 'false')
        StoreSettings.set_setting('pickup_address', request.form.get('pickup_address', ''))
        StoreSettings.set_setting('delivery_enabled', 'true' if request.form.get('delivery_enabled') else 'false')
        StoreSettings.set_setting('free_shipping_min', request.form.get('free_shipping_min', '300'))
        StoreSettings.set_setting('shipping_cost', request.form.get('shipping_cost', '15'))
        
        flash('Configurações atualizadas com sucesso!', 'success')
        return redirect(url_for('admin.store_settings'))
    
    settings = {
        'store_name': StoreSettings.get_setting('store_name', 'Sandwich Gourmet'),
        'store_logo': StoreSettings.get_setting('store_logo', ''),
        'store_description': StoreSettings.get_setting('store_description', 'Os melhores sanduíches da cidade'),
        'pickup_enabled': StoreSettings.get_setting('pickup_enabled', 'true') == 'true',
        'pickup_address': StoreSettings.get_setting('pickup_address', ''),
        'delivery_enabled': StoreSettings.get_setting('delivery_enabled', 'true') == 'true',
        'free_shipping_min': float(StoreSettings.get_setting('free_shipping_min', '300')),
        'shipping_cost': float(StoreSettings.get_setting('shipping_cost', '15'))
    }
    
    return render_template('admin/store_settings.html', settings=settings)

@admin_bp.route('/slides')
@login_required
@admin_required
def slides():
    slides = Slide.query.order_by(Slide.order, Slide.created_at.desc()).all()
    return render_template('admin/slides.html', slides=slides)

@admin_bp.route('/slides/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_slide():
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('image_url')
        link = request.form.get('link')
        
        order_value = request.form.get('order', '0')
        try:
            order = int(order_value) if order_value and order_value.strip() else 0
        except ValueError:
            order = 0
        
        active = request.form.get('active') == 'on'
        
        slide = Slide(
            title=title,
            image_url=image_url,
            link=link,
            order=order,
            active=active
        )
        
        db.session.add(slide)
        db.session.commit()
        
        flash('Slide adicionado com sucesso!', 'success')
        return redirect(url_for('admin.slides'))
    
    return render_template('admin/add_slide.html')

@admin_bp.route('/slides/editar/<int:slide_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_slide(slide_id):
    slide = Slide.query.get_or_404(slide_id)
    
    if request.method == 'POST':
        slide.title = request.form.get('title')
        slide.image_url = request.form.get('image_url')
        slide.link = request.form.get('link')
        
        order_value = request.form.get('order', '0')
        try:
            slide.order = int(order_value) if order_value and order_value.strip() else 0
        except ValueError:
            slide.order = 0
        
        slide.active = request.form.get('active') == 'on'
        
        db.session.commit()
        
        flash('Slide atualizado com sucesso!', 'success')
        return redirect(url_for('admin.slides'))
    
    return render_template('admin/edit_slide.html', slide=slide)

@admin_bp.route('/slides/deletar/<int:slide_id>', methods=['POST'])
@login_required
@admin_required
def delete_slide(slide_id):
    slide = Slide.query.get_or_404(slide_id)
    db.session.delete(slide)
    db.session.commit()
    
    flash('Slide deletado com sucesso!', 'success')
    return redirect(url_for('admin.slides'))

@admin_bp.route('/slides/toggle/<int:slide_id>', methods=['POST'])
@login_required
@admin_required
def toggle_slide(slide_id):
    slide = Slide.query.get_or_404(slide_id)
    slide.active = not slide.active
    db.session.commit()
    
    status = 'ativado' if slide.active else 'desativado'
    flash(f'Slide {status} com sucesso!', 'success')
    return redirect(url_for('admin.slides'))
