from flask import Blueprint, render_template, request
from app.models import Product, Category, Slide, Extra
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)

@main_bp.route('/cart-demo')
def cart_demo():
    return render_template('cart_demo.html')

@main_bp.route('/')
def index():
    categories = Category.query.all()
    featured_products = Product.query.filter_by(featured=True, active=True).limit(12).all()
    slides = Slide.query.filter_by(active=True).order_by(Slide.order, Slide.created_at.desc()).all()
    
    if not featured_products:
        featured_products = Product.query.filter_by(active=True).limit(12).all()
    
    category_products = {}
    for category in categories:
        category_products[category.id] = Product.query.filter_by(
            category_id=category.id,
            active=True
        ).limit(6).all()
    
    return render_template('index.html', categories=categories, products=featured_products, slides=slides, category_products=category_products)

@main_bp.route('/produto/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.active == True
    ).limit(4).all()
    extras = Extra.query.filter_by(active=True).all()
    
    return render_template('product_detail.html', product=product, categories=categories, related_products=related_products, extras=extras)

@main_bp.route('/categoria/<int:category_id>')
def category_products(category_id):
    category = Category.query.get_or_404(category_id)
    categories = Category.query.all()
    products = Product.query.filter_by(category_id=category_id, active=True).all()
    
    return render_template('category.html', category=category, categories=categories, products=products)

@main_bp.route('/buscar')
def search():
    query = request.args.get('q', '')
    categories = Category.query.all()
    
    if query:
        products = Product.query.filter(
            or_(
                Product.name.contains(query),
                Product.description.contains(query),
                Product.code.contains(query)
            ),
            Product.active == True
        ).all()
    else:
        products = []
    
    return render_template('search.html', query=query, products=products, categories=categories)
