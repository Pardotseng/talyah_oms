from flask import Flask, redirect, url_for, session, request
from .models import db, User, Customer, CustomerLevel, TieredPlan, Brand, SKU, AuditLog
from .routes.orders import order_bp
from .routes.auth import auth_bp
from .routes.customers import customer_bp
from .routes.products import product_bp

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///talyah_oms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'talyah-oms-secret-key'
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # 建立預設管理員帳號 (預設帳號: admin / 密碼: admin123)
        if not User.query.filter_by(username="admin").first():
            from werkzeug.security import generate_password_hash
            default_admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123")
            )
            db.session.add(default_admin)
            db.session.commit()
            
        if not Customer.query.first():
            plan = TieredPlan(name="標準分級計畫")
            db.session.add(plan)
            db.session.commit()
            
            level = CustomerLevel(name="VIP 等級", tiered_plan_id=plan.id)
            db.session.add(level)
            db.session.commit()
            
            sample_customer = Customer(
                code="MWZX",
                name="範例股份有限公司",
                address="新北市板橋區民生路一段1號",
                tax_id="12345678",
                phone="02-29998888",
                customer_level_id=level.id
            )
            db.session.add(sample_customer)
            
            brand = Brand(code="TY", name="TalYah 品牌", pricing_model="tiered")
            db.session.add(brand)
            db.session.commit()
            
            sample_sku = SKU(
                sku_code="TY-SKU-001",
                brand_id=brand.id,
                description="智慧監控感測器 (示範商品)",
                unit="PCS",
                original_price=1200,
                air_price=1500,
                sea_price=1100
            )
            db.session.add(sample_sku)
            db.session.commit()

    # 註冊藍圖
    app.register_blueprint(order_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(product_bp)
    
    # 權限保護攔截器：未登入者強制導向登入頁
    @app.before_request
    def require_login():
        allowed_endpoints = ['auth_bp.login', 'static']
        if 'user_id' not in session and request.endpoint not in allowed_endpoints:
            return redirect(url_for('auth_bp.login'))

    @app.route('/')
    def index_redirect():
        return redirect(url_for('order_bp.order_list'))
    
    return app
