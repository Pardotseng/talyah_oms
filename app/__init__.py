import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(os.path.dirname(base_dir), 'templates')
    
    app = Flask(__name__, template_folder=template_dir)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///talyah_enterprise.db'
    app.config['SECRET_KEY'] = 'talyah_enterprise_production_key_2026'
    db.init_app(app)
    
    from app.models import User, Customer, Product, Order, OrderItem, AuditLog
    
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            default_user = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                role="Admin"
            )
            db.session.add(default_user)
            db.session.commit()
            
        if Product.query.count() == 0:
            db.session.add(Product(sku_code="SKU-PRO-01", description="企業級高效能主機", origin_price=50000, air_price=52000, sea_price=49000, stock_quantity=50))
            db.session.add(Product(sku_code="SKU-PRO-02", description="精密工業感測器", origin_price=8000, air_price=8500, sea_price=8200, stock_quantity=200))
            db.session.commit()
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login_page'))
    
    from app.routes.auth import auth_bp
    from app.routes.oms import oms_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(oms_bp)
    
    return app
