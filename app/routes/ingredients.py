from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Ingredient, Product, ProductIngredient

ingredients_bp = Blueprint('ingredients', __name__, url_prefix='/ingredientes')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@ingredients_bp.route('/')
@login_required
@admin_required
def index():
    ingredients = Ingredient.query.filter_by(active=True).all()
    low_stock = Ingredient.query.filter(Ingredient.stock <= Ingredient.min_stock, Ingredient.active == True).all()
    
    return render_template('ingredients/index.html', 
                         ingredients=ingredients,
                         low_stock=low_stock)

@ingredients_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        unit = request.form.get('unit')
        cost_per_unit = request.form.get('cost_per_unit', type=float)
        stock = request.form.get('stock', 0, type=float)
        min_stock = request.form.get('min_stock', 0, type=float)
        
        ingredient = Ingredient(
            name=name,
            unit=unit,
            cost_per_unit=cost_per_unit,
            stock=stock,
            min_stock=min_stock
        )
        db.session.add(ingredient)
        db.session.commit()
        
        flash(f'Ingrediente {name} adicionado com sucesso!', 'success')
        return redirect(url_for('ingredients.index'))
    
    return render_template('ingredients/add.html')

@ingredients_bp.route('/editar/<int:ingredient_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    
    if request.method == 'POST':
        ingredient.name = request.form.get('name')
        ingredient.unit = request.form.get('unit')
        ingredient.cost_per_unit = request.form.get('cost_per_unit', type=float)
        ingredient.stock = request.form.get('stock', type=float)
        ingredient.min_stock = request.form.get('min_stock', type=float)
        
        db.session.commit()
        
        flash(f'Ingrediente {ingredient.name} atualizado!', 'success')
        return redirect(url_for('ingredients.index'))
    
    return render_template('ingredients/edit.html', ingredient=ingredient)

@ingredients_bp.route('/produto/<int:product_id>/ficha-tecnica', methods=['GET', 'POST'])
@login_required
@admin_required
def product_recipe(product_id):
    product = Product.query.get_or_404(product_id)
    all_ingredients = Ingredient.query.filter_by(active=True).all()
    
    if request.method == 'POST':
        ProductIngredient.query.filter_by(product_id=product_id).delete()
        
        for ingredient in all_ingredients:
            quantity = request.form.get(f'ingredient_{ingredient.id}', type=float)
            if quantity and quantity > 0:
                product_ingredient = ProductIngredient(
                    product_id=product_id,
                    ingredient_id=ingredient.id,
                    quantity=quantity
                )
                db.session.add(product_ingredient)
        
        db.session.commit()
        flash(f'Ficha técnica do produto {product.name} atualizada!', 'success')
        return redirect(url_for('admin.products'))
    
    product_ingredients = {pi.ingredient_id: pi.quantity for pi in ProductIngredient.query.filter_by(product_id=product_id).all()}
    
    total_cost = sum(
        pi.ingredient.cost_per_unit * pi.quantity 
        for pi in ProductIngredient.query.filter_by(product_id=product_id).all()
    )
    
    cmv_percentage = (total_cost / product.price * 100) if product.price > 0 else 0
    
    return render_template('ingredients/product_recipe.html', 
                         product=product,
                         all_ingredients=all_ingredients,
                         product_ingredients=product_ingredients,
                         total_cost=total_cost,
                         cmv_percentage=cmv_percentage)
