from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Wishlist, Product

wishlist_bp = Blueprint('wishlist', __name__, url_prefix='/wishlist')

@wishlist_bp.route('/')
@login_required
def view_wishlist():
    wishlists = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', wishlists=wishlists)

@wishlist_bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing:
        flash('Produto já está na sua lista de desejos!', 'info')
    else:
        wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash('Produto adicionado à lista de desejos!', 'success')
    
    return redirect(request.referrer or url_for('main.index'))

@wishlist_bp.route('/remove/<int:wishlist_id>', methods=['POST'])
@login_required
def remove_from_wishlist(wishlist_id):
    wishlist_item = Wishlist.query.get_or_404(wishlist_id)
    
    if wishlist_item.user_id != current_user.id:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('wishlist.view_wishlist'))
    
    db.session.delete(wishlist_item)
    db.session.commit()
    flash('Produto removido da lista de desejos!', 'success')
    
    return redirect(url_for('wishlist.view_wishlist'))

@wishlist_bp.route('/check/<int:product_id>')
@login_required
def check_in_wishlist(product_id):
    exists = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first() is not None
    
    return jsonify({'in_wishlist': exists})
