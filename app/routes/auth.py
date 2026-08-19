from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models import User, AuditLog
from werkzeug.security import check_password_hash
from app import db

auth_bp = Blueprint('auth', __name__)

def log_action(action, details=""):
    try:
        log = AuditLog(username=session.get('username', 'system'), action=action, details=details)
        db.session.add(log)
        db.session.commit()
    except:
        db.session.rollback()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username') or (request.json.get('username') if request.is_json else None)
        password = request.form.get('password') or (request.json.get('password') if request.is_json else None)
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            log_action("使用者登入", f"帳號 {username} 成功登入系統")
            if request.is_json:
                return jsonify({"message": "登入成功", "redirect": "/dashboard"})
            return redirect(url_for('auth.dashboard'))
        
        if request.is_json:
            return jsonify({"error": "帳號或密碼錯誤"}), 401
        return render_template('login.html', error="帳號或密碼錯誤 (預設: admin / admin123)")
        
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    log_action("使用者登出", f"帳號 {session.get('username')} 登出")
    session.clear()
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('auth.login_page'))
    return render_template('dashboard.html', user=session.get('username'), role=session.get('role'))

@auth_bp.route('/customers')
def customers_page():
    if 'user_id' not in session: return redirect(url_for('auth.login_page'))
    return render_template('customers.html', user=session.get('username'))

@auth_bp.route('/inventory')
def inventory_page():
    if 'user_id' not in session: return redirect(url_for('auth.login_page'))
    return render_template('inventory.html', user=session.get('username'))

@auth_bp.route('/orders')
def orders_page():
    if 'user_id' not in session: return redirect(url_for('auth.login_page'))
    return render_template('orders.html', user=session.get('username'))

@auth_bp.route('/finance')
def finance_page():
    if 'user_id' not in session: return redirect(url_for('auth.login_page'))
    return render_template('finance.html', user=session.get('username'))
