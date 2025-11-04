from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        cpf = request.form.get('cpf')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso.', 'danger')
            return render_template('register.html')
        
        cpf_normalized = ''.join(filter(str.isdigit, cpf)) if cpf else None
        
        if cpf_normalized and len(cpf_normalized) != 11:
            flash('CPF inválido. Digite 11 dígitos.', 'danger')
            return render_template('register.html')
        
        if cpf_normalized and User.query.filter_by(cpf=cpf_normalized).first():
            flash('Este CPF já está cadastrado.', 'danger')
            return render_template('register.html')
        
        user = User(username=username, email=email, cpf=cpf_normalized, phone=phone)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verificar senha atual
        if not current_user.check_password(current_password):
            flash('Senha atual incorreta.', 'danger')
            return render_template('change_password.html')
        
        # Verificar se as novas senhas coincidem
        if new_password != confirm_password:
            flash('As novas senhas não coincidem.', 'danger')
            return render_template('change_password.html')
        
        # Verificar tamanho mínimo da senha
        if len(new_password) < 6:
            flash('A nova senha deve ter no mínimo 6 caracteres.', 'danger')
            return render_template('change_password.html')
        
        # Atualizar senha
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('change_password.html')
