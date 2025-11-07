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
        phone = request.form.get('phone')
        
        if not phone:
            flash('Por favor, digite seu telefone.', 'danger')
            return render_template('login.html')
        
        phone_normalized = ''.join(filter(str.isdigit, phone))
        
        user = User.query.filter_by(phone=phone_normalized).first()
        
        if user:
            login_user(user)
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Telefone não encontrado. Cadastre-se primeiro.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        
        if not username or not phone:
            flash('Nome e telefone são obrigatórios.', 'danger')
            return render_template('register.html')
        
        phone_normalized = ''.join(filter(str.isdigit, phone))
        
        if len(phone_normalized) < 10:
            flash('Telefone inválido. Digite um número válido.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(phone=phone_normalized).first():
            flash('Este telefone já está cadastrado.', 'danger')
            return render_template('register.html')
        
        user = User(username=username, phone=phone_normalized)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('main.index'))
    
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
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verificar se usuário tem senha atual (se não tiver, é cadastro por telefone)
        if current_user.has_password():
            # Se tem senha, precisa confirmar a senha atual
            if not current_password:
                flash('Digite sua senha atual.', 'danger')
                return render_template('change_password.html')
            
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
