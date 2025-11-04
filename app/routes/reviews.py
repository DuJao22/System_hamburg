from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Review, Product, Order, OrderItem

reviews_bp = Blueprint('reviews', __name__, url_prefix='/reviews')

@reviews_bp.route('/add/<int:product_id>', methods=['GET', 'POST'])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    
    existing_review = Review.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing_review:
        flash('Você já avaliou este produto!', 'info')
        return redirect(url_for('main.product_detail', product_id=product_id))
    
    if request.method == 'POST':
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '').strip()
        
        if rating < 1 or rating > 5:
            flash('Avaliação deve ser entre 1 e 5 estrelas!', 'danger')
            return redirect(url_for('reviews.add_review', product_id=product_id))
        
        verified_purchase = db.session.query(OrderItem).join(Order).filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == product_id
        ).first() is not None
        
        review = Review(
            user_id=current_user.id,
            product_id=product_id,
            rating=rating,
            comment=comment,
            verified_purchase=verified_purchase
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Avaliação enviada com sucesso!', 'success')
        return redirect(url_for('main.product_detail', product_id=product_id))
    
    return render_template('add_review.html', product=product)

@reviews_bp.route('/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id:
        flash('Você não pode editar esta avaliação!', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '').strip()
        
        if rating < 1 or rating > 5:
            flash('Avaliação deve ser entre 1 e 5 estrelas!', 'danger')
            return redirect(url_for('reviews.edit_review', review_id=review_id))
        
        review.rating = rating
        review.comment = comment
        db.session.commit()
        
        flash('Avaliação atualizada com sucesso!', 'success')
        return redirect(url_for('main.product_detail', product_id=review.product_id))
    
    return render_template('edit_review.html', review=review)

@reviews_bp.route('/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id and not current_user.is_admin:
        flash('Você não pode excluir esta avaliação!', 'danger')
        return redirect(url_for('main.index'))
    
    product_id = review.product_id
    db.session.delete(review)
    db.session.commit()
    
    flash('Avaliação excluída com sucesso!', 'success')
    return redirect(url_for('main.product_detail', product_id=product_id))
