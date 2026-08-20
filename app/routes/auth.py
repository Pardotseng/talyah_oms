from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from ..models import db, User, AuditLog

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            
            # 記錄登入稽核日誌
            log = AuditLog(action=f"使用者 {username} 登入系統")
            db.session.add(log)
            db.session.commit()
            
            flash('登入成功！歡迎回來。', 'success')
            return redirect(url_for('order_bp.order_list'))
        else:
            flash('帳號或密碼錯誤，請重新輸入。', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    if 'username' in session:
        log = AuditLog(action=f"使用者 {session['username']} 登出系統")
        db.session.add(log)
        db.session.commit()
        
    session.clear()
    flash('已安全登出系統。', 'success')
    return redirect(url_for('auth_bp.login'))
