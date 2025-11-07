from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app.utils.timezone import utcnow_brasilia
import secrets

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    cpf = db.Column(db.String(14), nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='customer')
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    
    wishlists = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def has_password(self):
        return self.password_hash is not None and self.password_hash != ''

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500))
    image_url_2 = db.Column(db.String(500))
    image_url_3 = db.Column(db.String(500))
    image_url_4 = db.Column(db.String(500))
    image_url_5 = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    
    def get_all_images(self):
        images = []
        for i in range(1, 6):
            if i == 1:
                url = self.image_url
            else:
                url = getattr(self, f'image_url_{i}', None)
            if url:
                images.append(url)
        return images

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_code = db.Column(db.String(50), unique=True, nullable=True)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pendente')
    payment_status = db.Column(db.String(50), default='Pendente')
    payment_id = db.Column(db.String(200))
    payment_method = db.Column(db.String(50))
    payment_confirmed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    payment_confirmed_at = db.Column(db.DateTime, nullable=True)
    payment_confirmation_notes = db.Column(db.Text, nullable=True)
    delivery_type = db.Column(db.String(20), default='delivery')
    delivery_address = db.Column(db.Text)
    customer_name = db.Column(db.String(200))
    customer_phone = db.Column(db.String(50))
    shipping_cost = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    coupon_code = db.Column(db.String(50))
    observations = db.Column(db.Text)
    estimated_prep_time = db.Column(db.Integer, default=30)
    estimated_delivery_time = db.Column(db.Integer, default=45)
    accepted_at = db.Column(db.DateTime, nullable=True)
    ready_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=True)
    comanda_id = db.Column(db.Integer, db.ForeignKey('comanda.id'), nullable=True)
    table_session_id = db.Column(db.Integer, db.ForeignKey('table_session.id'), nullable=True)
    origin = db.Column(db.String(20), default='delivery')
    received_at = db.Column(db.DateTime, nullable=True)
    preparing_at = db.Column(db.DateTime, nullable=True)
    kitchen_ready_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    updated_at = db.Column(db.DateTime, default=utcnow_brasilia, onupdate=utcnow_brasilia)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', backref='order', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('OrderNote', backref='order', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', foreign_keys=[user_id], backref='orders')
    payment_confirmer = db.relationship('User', foreign_keys=[payment_confirmed_by], backref='confirmed_payments')
    
    @property
    def order_number(self):
        """Retorna código do pedido (custom ou PED + id)"""
        return self.order_code if self.order_code else f"PED{self.id:06d}"
    
    def get_subtotal(self):
        return sum(item.price * item.quantity for item in self.items)
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items)

class Extra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    observations = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pendente')
    received_at = db.Column(db.DateTime, nullable=True)
    preparing_at = db.Column(db.DateTime, nullable=True)
    ready_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    product = db.relationship('Product')
    extras = db.relationship('OrderItemExtra', backref='order_item', lazy=True, cascade='all, delete-orphan')

class OrderItemExtra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'), nullable=False)
    extra_id = db.Column(db.Integer, db.ForeignKey('extra.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    extra = db.relationship('Extra')

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    observations = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')
    user = db.relationship('User')
    extras = db.relationship('CartItemExtra', backref='cart_item', lazy=True, cascade='all, delete-orphan')

class CartItemExtra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_item_id = db.Column(db.Integer, db.ForeignKey('cart_item.id'), nullable=False)
    extra_id = db.Column(db.Integer, db.ForeignKey('extra.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    
    extra = db.relationship('Extra')

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)
    discount_value = db.Column(db.Float, nullable=False)
    min_purchase = db.Column(db.Float, default=0)
    max_uses = db.Column(db.Integer, default=None, nullable=True)
    times_used = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_valid(self):
        if not self.active:
            return False, "Cupom inativo"
        
        now = datetime.utcnow()
        if self.valid_from and now < self.valid_from:
            return False, "Cupom ainda não está válido"
        
        if self.valid_until and now > self.valid_until:
            return False, "Cupom expirado"
        
        if self.max_uses and self.times_used >= self.max_uses:
            return False, "Cupom atingiu o limite de uso"
        
        return True, "Cupom válido"
    
    def calculate_discount(self, total):
        if self.discount_type == 'percentage':
            return total * (self.discount_value / 100)
        else:
            return min(self.discount_value, total)

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    verified_purchase = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)
    
    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at

class StoreSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_setting(key, default=None):
        setting = StoreSettings.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default
    
    @staticmethod
    def set_setting(key, value):
        setting = StoreSettings.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = StoreSettings(setting_key=key, setting_value=value)
            db.session.add(setting)
        db.session.commit()
        return setting

class Slide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    link = db.Column(db.String(500))
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OrderStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50), nullable=False)
    changed_by = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OrderNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.String(200))
    is_internal = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(20), unique=True, nullable=False)
    capacity = db.Column(db.Integer, default=4)
    status = db.Column(db.String(20), default='available')
    current_order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    opened_at = db.Column(db.DateTime, nullable=True)
    waiter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    qr_code_url = db.Column(db.String(500), nullable=True)
    access_pin = db.Column(db.String(4), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    
    waiter = db.relationship('User', foreign_keys=[waiter_id])
    current_order = db.relationship('Order', foreign_keys=[current_order_id], post_update=True)
    
    def get_status_display(self):
        status_map = {
            'available': 'Disponível',
            'occupied': 'Ocupada',
            'reserved': 'Reservada',
            'cleaning': 'Limpeza'
        }
        return status_map.get(self.status, self.status)
    
    def get_qr_code_data(self):
        from flask import url_for
        return url_for('table_menu.table_access', table_number=self.table_number, _external=True)

class Comanda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comanda_number = db.Column(db.String(20), unique=True, nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=True)
    customer_name = db.Column(db.String(200))
    status = db.Column(db.String(20), default='open')
    total = db.Column(db.Float, default=0)
    opened_at = db.Column(db.DateTime, default=utcnow_brasilia)
    closed_at = db.Column(db.DateTime, nullable=True)
    waiter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    access_pin = db.Column(db.String(4), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    
    table = db.relationship('Table', backref='comandas')
    waiter = db.relationship('User', foreign_keys=[waiter_id])
    items = db.relationship('ComandaItem', backref='comanda', lazy=True, cascade='all, delete-orphan')
    
    def calculate_total(self):
        return sum(item.calculate_item_total() for item in self.items)

class ComandaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comanda_id = db.Column(db.Integer, db.ForeignKey('comanda.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    sent_to_kitchen = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    
    product = db.relationship('Product')
    extras = db.relationship('ComandaItemExtra', backref='comanda_item', lazy=True, cascade='all, delete-orphan')
    
    def calculate_item_total(self):
        product_total = self.price * self.quantity
        extras_total = sum(extra.price * extra.quantity for extra in self.extras)
        return product_total + extras_total

class ComandaItemExtra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comanda_item_id = db.Column(db.Integer, db.ForeignKey('comanda_item.id'), nullable=False)
    extra_id = db.Column(db.Integer, db.ForeignKey('extra.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    extra = db.relationship('Extra')

class CashRegister(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    opening_balance = db.Column(db.Float, default=0)
    closing_balance = db.Column(db.Float, nullable=True)
    expected_balance = db.Column(db.Float, nullable=True)
    difference = db.Column(db.Float, nullable=True)
    opened_at = db.Column(db.DateTime, default=utcnow_brasilia)
    closed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='open')
    notes = db.Column(db.Text)
    
    user = db.relationship('User')
    movements = db.relationship('CashMovement', backref='cash_register', lazy=True, cascade='all, delete-orphan')
    
    def calculate_expected_balance(self):
        total_in = sum(m.amount for m in self.movements if m.movement_type == 'in')
        total_out = sum(m.amount for m in self.movements if m.movement_type == 'out')
        return self.opening_balance + total_in - total_out

class CashMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cash_register_id = db.Column(db.Integer, db.ForeignKey('cash_register.id'), nullable=False)
    movement_type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    order = db.relationship('Order')
    user = db.relationship('User')

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    cost_per_unit = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Float, default=0)
    min_stock = db.Column(db.Float, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)

class ProductIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product', backref='ingredients')
    ingredient = db.relationship('Ingredient')

class LoyaltyPoints(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    total_earned = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=utcnow_brasilia, onupdate=utcnow_brasilia)
    
    user = db.relationship('User', backref='loyalty_points', uselist=False)
    transactions = db.relationship('LoyaltyTransaction', backref='loyalty_account', lazy=True, cascade='all, delete-orphan')

class LoyaltyTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loyalty_points_id = db.Column(db.Integer, db.ForeignKey('loyalty_points.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    
    order = db.relationship('Order')

class TableSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    comanda_id = db.Column(db.Integer, db.ForeignKey('comanda.id'), nullable=True)
    session_token = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')
    opened_at = db.Column(db.DateTime, default=utcnow_brasilia)
    closed_at = db.Column(db.DateTime, nullable=True)
    waiter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    table = db.relationship('Table', backref='sessions')
    user = db.relationship('User', foreign_keys=[user_id], backref='table_sessions')
    waiter = db.relationship('User', foreign_keys=[waiter_id])
    comanda = db.relationship('Comanda', backref='session')
    orders = db.relationship('Order', backref='table_session', lazy=True)

class KitchenNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    recipient_type = db.Column(db.String(20), nullable=False)
    recipient_id = db.Column(db.Integer, nullable=True)
    notification_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    
    order = db.relationship('Order', backref='notifications')

class ChatConversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user_name = db.Column(db.String(200), nullable=True)
    user_phone = db.Column(db.String(50), nullable=True)
    context_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
    updated_at = db.Column(db.DateTime, default=utcnow_brasilia, onupdate=utcnow_brasilia)
    
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, cascade='all, delete-orphan', order_by='ChatMessage.created_at')
    user = db.relationship('User', backref='chat_conversations')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversation.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    extra_data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_brasilia)
