from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
import os

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    
    cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '*')
    if cors_origins != '*':
        cors_origins = cors_origins.split(',')
    
    socketio.init_app(app, cors_allowed_origins=cors_origins, async_mode='threading')
    
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.cart import cart_bp
    from app.routes.wishlist import wishlist_bp
    from app.routes.reviews import reviews_bp
    from app.routes.payment import payment_bp
    from app.routes.cep_api import cep_api_bp
    from app.routes.pdv import pdv_bp
    from app.routes.ingredients import ingredients_bp
    from app.routes.kitchen import kitchen_bp
    from app.routes.loyalty import loyalty_bp
    from app.routes.digital_menu import digital_menu_bp
    from app.routes.table_menu import table_menu_bp
    from app.routes.chatbot import chatbot_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(payment_bp, url_prefix='/pagamento')
    app.register_blueprint(cep_api_bp)
    app.register_blueprint(pdv_bp)
    app.register_blueprint(ingredients_bp)
    app.register_blueprint(kitchen_bp)
    app.register_blueprint(loyalty_bp)
    app.register_blueprint(digital_menu_bp)
    app.register_blueprint(table_menu_bp)
    app.register_blueprint(chatbot_bp)
    
    @app.context_processor
    def inject_categories():
        from app.models import Category
        categories = Category.query.all()
        return dict(categories=categories)
    
    @app.context_processor
    def inject_store_settings():
        from app.models import StoreSettings
        store_settings = {
            'store_name': StoreSettings.get_setting('store_name', 'TCB - The Country Burger Artesanal'),
            'store_logo': StoreSettings.get_setting('store_logo', '/static/images/tcb_logo.jpg'),
            'store_description': StoreSettings.get_setting('store_description', 'Hamburgueria Artesanal'),
            'store_phone': StoreSettings.get_setting('store_phone', '(31) 98765-4321'),
            'store_whatsapp': StoreSettings.get_setting('store_whatsapp', '5531987654321'),
            'store_email': StoreSettings.get_setting('store_email', 'contato@tcb.com.br'),
            'store_address': StoreSettings.get_setting('pickup_address', 'R. Judith Naves de Lima, 469 – Santa Edwiges, Contagem – MG, 32040-275, Brasil'),
            'opening_hours_monday': StoreSettings.get_setting('opening_hours_monday', '18:00 - 23:59'),
            'opening_hours_tuesday': StoreSettings.get_setting('opening_hours_tuesday', 'Fechado'),
            'opening_hours_wednesday': StoreSettings.get_setting('opening_hours_wednesday', '18:00 - 23:59'),
            'opening_hours_thursday': StoreSettings.get_setting('opening_hours_thursday', '18:00 - 23:59'),
            'opening_hours_friday': StoreSettings.get_setting('opening_hours_friday', '18:00 - 23:59'),
            'opening_hours_saturday': StoreSettings.get_setting('opening_hours_saturday', '18:00 - 23:59'),
            'opening_hours_sunday': StoreSettings.get_setting('opening_hours_sunday', '18:00 - 23:59')
        }
        return dict(store_settings=store_settings)
    
    with app.app_context():
        db.create_all()
        from app.models import User, Category, Product
        
        if User.query.count() == 0:
            admin_password = os.environ.get('ADMIN_PASSWORD')
            if not admin_password:
                admin_password = '30031936Vo.'
                print("WARNING: Using default admin password. Set ADMIN_PASSWORD environment variable for production!")
            
            admin = User(
                username='admin',
                email='admin@hamburguer.com',
                is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created with email: admin@hamburguer.com")
        
        if Category.query.count() == 0:
            categories = [
                Category(name='Hambúrgueres', description='Deliciosos hambúrgueres artesanais', image_url='/static/images/delicious_gourmet_bu_7f0e20b3.jpg'),
                Category(name='Sanduíches Clássicos', description='Sanduíches tradicionais e saborosos', image_url='/static/images/fresh_sandwich_food__12966558.jpg'),
                Category(name='Wraps', description='Wraps saudáveis e nutritivos', image_url='/static/images/wrap_sandwich_health_20806737.jpg'),
                Category(name='Sanduíches Naturais', description='Opções leves e naturais', image_url='/static/images/fresh_sandwich_food__fc23202b.jpg'),
                Category(name='Combos', description='Combos com batata e refri', image_url='/static/images/gourmet_burger_resta_e9bba5c2.jpg'),
                Category(name='Especiais', description='Criações exclusivas do chef', image_url='/static/images/delicious_gourmet_bu_3904a411.jpg'),
                Category(name='Vegetarianos', description='Opções vegetarianas deliciosas', image_url='/static/images/fresh_sandwich_food__e532af6a.jpg'),
                Category(name='Bebidas', description='Refrigerantes, sucos e água', image_url='/static/images/food_banner_fast_foo_3736efc2.jpg'),
                Category(name='Frituras', description='Batata frita, onion rings e mais'),
                Category(name='Molhos', description='Molhos especiais para acompanhar')
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("Categories created")
        
        if Product.query.count() == 0:
            burger_cat = Category.query.filter_by(name='Hambúrgueres').first()
            classic_cat = Category.query.filter_by(name='Sanduíches Clássicos').first()
            wrap_cat = Category.query.filter_by(name='Wraps').first()
            combo_cat = Category.query.filter_by(name='Combos').first()
            special_cat = Category.query.filter_by(name='Especiais').first()
            bebidas_cat = Category.query.filter_by(name='Bebidas').first()
            frituras_cat = Category.query.filter_by(name='Frituras').first()
            molhos_cat = Category.query.filter_by(name='Molhos').first()
            
            products = [
                Product(
                    name='X-Bacon Gourmet',
                    code='BURG-001',
                    description='Hambúrguer artesanal 200g, bacon crocante, queijo cheddar, alface, tomate e molho especial',
                    price=28.90,
                    stock=50,
                    category_id=burger_cat.id if burger_cat else 1,
                    image_url='/static/images/delicious_gourmet_bu_7f0e20b3.jpg',
                    featured=True
                ),
                Product(
                    name='Cheese Burger Clássico',
                    code='BURG-002',
                    description='Hambúrguer 150g, queijo prato, picles, cebola, ketchup e mostarda',
                    price=22.90,
                    stock=100,
                    category_id=burger_cat.id if burger_cat else 1,
                    image_url='/static/images/delicious_gourmet_bu_57b25bfa.jpg',
                    featured=True
                ),
                Product(
                    name='Sanduíche Natural de Frango',
                    code='NAT-001',
                    description='Peito de frango grelhado, alface, tomate, cenoura ralada e maionese light em pão integral',
                    price=18.90,
                    stock=30,
                    category_id=classic_cat.id if classic_cat else 2,
                    image_url='/static/images/fresh_sandwich_food__12966558.jpg',
                    featured=True
                ),
                Product(
                    name='Wrap Caesar',
                    code='WRAP-001',
                    description='Tortilla recheada com frango grelhado, alface romana, parmesão e molho caesar',
                    price=24.90,
                    stock=75,
                    category_id=wrap_cat.id if wrap_cat else 3,
                    image_url='/static/images/wrap_sandwich_health_20806737.jpg',
                    featured=True
                ),
                Product(
                    name='Club Sandwich',
                    code='CLAS-001',
                    description='Triplo de pão de forma, frango, bacon, alface, tomate, ovo e maionese',
                    price=26.90,
                    stock=60,
                    category_id=classic_cat.id if classic_cat else 2,
                    image_url='/static/images/fresh_sandwich_food__fc23202b.jpg',
                    featured=True
                ),
                Product(
                    name='Combo X-Burguer',
                    code='COMBO-001',
                    description='X-Burguer + Batata Frita Média + Refrigerante 350ml',
                    price=28.90,
                    stock=100,
                    category_id=combo_cat.id if combo_cat else 5,
                    image_url='/static/images/gourmet_burger_resta_41d51929.jpg',
                    featured=True
                ),
                Product(
                    name='Combo X-Salada',
                    code='COMBO-002',
                    description='X-Salada + Batata Frita Média + Refrigerante 350ml',
                    price=32.90,
                    stock=100,
                    category_id=combo_cat.id if combo_cat else 5,
                    image_url='/static/images/fresh_sandwich_food__033e68ac.jpg',
                    featured=True
                ),
                Product(
                    name='Combo X-Bacon',
                    code='COMBO-003',
                    description='X-Bacon + Batata Frita Grande + Refrigerante 600ml',
                    price=38.90,
                    stock=100,
                    category_id=combo_cat.id if combo_cat else 5,
                    image_url='/static/images/delicious_gourmet_bu_3904a411.jpg',
                    featured=True
                ),
                Product(
                    name='Combo Wrap',
                    code='COMBO-004',
                    description='Wrap de Frango + Batata Frita Pequena + Suco Natural',
                    price=26.90,
                    stock=100,
                    category_id=combo_cat.id if combo_cat else 5,
                    image_url='/static/images/wrap_sandwich_health_18fc4927.jpg',
                    featured=True
                ),
                Product(
                    name='Burger BBQ Premium',
                    code='SPEC-001',
                    description='Hambúrguer premium 250g, cebola caramelizada, queijo gorgonzola e molho barbecue caseiro',
                    price=34.90,
                    stock=40,
                    category_id=special_cat.id if special_cat else 6,
                    image_url='/static/images/delicious_gourmet_bu_3904a411.jpg',
                    featured=True
                ),
                Product(
                    name='Sanduíche Vegetariano',
                    code='VEG-001',
                    description='Hambúrguer de grão-de-bico, queijo, rúcula, tomate seco e maionese de ervas',
                    price=25.90,
                    stock=45,
                    category_id=classic_cat.id if classic_cat else 2,
                    image_url='/static/images/fresh_sandwich_food__e532af6a.jpg',
                    featured=True
                ),
                Product(
                    name='Coca-Cola 350ml',
                    code='BEB-001',
                    description='Refrigerante Coca-Cola lata 350ml',
                    price=5.00,
                    stock=200,
                    category_id=bebidas_cat.id if bebidas_cat else 8,
                    featured=False
                ),
                Product(
                    name='Guaraná Antarctica 350ml',
                    code='BEB-002',
                    description='Refrigerante Guaraná Antarctica lata 350ml',
                    price=5.00,
                    stock=200,
                    category_id=bebidas_cat.id if bebidas_cat else 8,
                    featured=False
                ),
                Product(
                    name='Refrigerante 2L',
                    code='BEB-003',
                    description='Refrigerante 2 litros (Coca, Guaraná, Fanta)',
                    price=12.00,
                    stock=100,
                    category_id=bebidas_cat.id if bebidas_cat else 8,
                    featured=False
                ),
                Product(
                    name='Suco Natural 500ml',
                    code='BEB-004',
                    description='Suco natural de laranja, limão ou morango',
                    price=8.00,
                    stock=50,
                    category_id=bebidas_cat.id if bebidas_cat else 8,
                    featured=False
                ),
                Product(
                    name='Água Mineral 500ml',
                    code='BEB-005',
                    description='Água mineral sem gás',
                    price=3.00,
                    stock=150,
                    category_id=bebidas_cat.id if bebidas_cat else 8,
                    featured=False
                ),
                Product(
                    name='Batata Frita Pequena',
                    code='FRIT-001',
                    description='Porção pequena de batata frita crocante',
                    price=8.00,
                    stock=150,
                    category_id=frituras_cat.id if frituras_cat else 9,
                    featured=False
                ),
                Product(
                    name='Batata Frita Média',
                    code='FRIT-002',
                    description='Porção média de batata frita crocante',
                    price=12.00,
                    stock=150,
                    category_id=frituras_cat.id if frituras_cat else 9,
                    featured=True
                ),
                Product(
                    name='Batata Frita Grande',
                    code='FRIT-003',
                    description='Porção grande de batata frita crocante',
                    price=18.00,
                    stock=150,
                    category_id=frituras_cat.id if frituras_cat else 9,
                    featured=False
                ),
                Product(
                    name='Onion Rings',
                    code='FRIT-004',
                    description='Anéis de cebola empanados e fritos',
                    price=15.00,
                    stock=80,
                    category_id=frituras_cat.id if frituras_cat else 9,
                    featured=False
                ),
                Product(
                    name='Nuggets (10 unid)',
                    code='FRIT-005',
                    description='Nuggets de frango crocantes',
                    price=16.00,
                    stock=100,
                    category_id=frituras_cat.id if frituras_cat else 9,
                    featured=False
                ),
                Product(
                    name='Molho Barbecue',
                    code='MOL-001',
                    description='Molho barbecue especial',
                    price=2.00,
                    stock=200,
                    category_id=molhos_cat.id if molhos_cat else 10,
                    featured=False
                ),
                Product(
                    name='Molho Cheddar',
                    code='MOL-002',
                    description='Molho de queijo cheddar cremoso',
                    price=3.00,
                    stock=200,
                    category_id=molhos_cat.id if molhos_cat else 10,
                    featured=False
                ),
                Product(
                    name='Maionese da Casa',
                    code='MOL-003',
                    description='Maionese temperada especial',
                    price=2.00,
                    stock=200,
                    category_id=molhos_cat.id if molhos_cat else 10,
                    featured=False
                ),
                Product(
                    name='Molho Picante',
                    code='MOL-004',
                    description='Molho picante de pimenta',
                    price=2.00,
                    stock=200,
                    category_id=molhos_cat.id if molhos_cat else 10,
                    featured=False
                )
            ]
            db.session.add_all(products)
            db.session.commit()
            print("Sample products created")
    
    from app.routes import websocket
    
    return app
