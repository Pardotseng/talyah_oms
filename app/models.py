from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 1. 兼容原有專案初始化所需的身分與日誌模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# 2. 對應 PRD 的客戶與等級模型
class Customer(db.Model):
    __tablename__ = 'customers'
    code = db.Column(db.String(20), primary_key=True) # 客戶簡碼 (例如 MWZX)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    tax_id = db.Column(db.String(20)) # 統一編號
    phone = db.Column(db.String(50))
    customer_level_id = db.Column(db.Integer, db.ForeignKey('customer_levels.id'))
    
    level = db.relationship('CustomerLevel', backref='customers')

class CustomerLevel(db.Model):
    __tablename__ = 'customer_levels'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    tiered_plan_id = db.Column(db.Integer, db.ForeignKey('tiered_plans.id'), nullable=False) # 1對1綁定
    
    tiered_plan = db.relationship('TieredPlan', backref='levels')

class TieredPlan(db.Model):
    __tablename__ = 'tiered_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    pricing_model = db.Column(db.String(20), nullable=False) # 'tiered' 或 'air_sea'

class SKU(db.Model):
    __tablename__ = 'skus'
    id = db.Column(db.Integer, primary_key=True)
    sku_code = db.Column(db.String(50), unique=True, nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    barcode = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    unit = db.Column(db.String(20), default='PCS')
    original_price = db.Column(db.Numeric(10, 2), default=0)
    air_price = db.Column(db.Numeric(10, 2), default=0) # 空運價
    sea_price = db.Column(db.Numeric(10, 2), default=0) # 海運價
    is_active = db.Column(db.Boolean, default=True)
    
    brand = db.relationship('Brand', backref='skus')

# 讓 Product 名稱對應到 SKU，確保舊程式碼或 __init__.py 不會報錯
Product = SKU

# 3. 對應 PRD 的訂單與明細模型
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False) # 例如 MWZX260001
    order_date = db.Column(db.Date, default=datetime.utcnow)
    
    # 客戶快照欄位
    customer_id = db.Column(db.String(20), db.ForeignKey('customers.code'), nullable=False)
    customer_name = db.Column(db.String(100))
    customer_address = db.Column(db.String(200))
    customer_tax_id = db.Column(db.String(20))
    customer_phone = db.Column(db.String(50))
    customer_level_name = db.Column(db.String(50))
    
    status = db.Column(db.String(20), default='draft') # draft (草稿), confirmed (已確認), cancelled (已取消)
    remarks = db.Column(db.Text)
    duplicated_from_order_id = db.Column(db.Integer, nullable=True) # 複製來源訂單ID
    
    total_quantity = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Numeric(10, 2), default=0)
    
    currency = db.Column(db.String(10), default='TWD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')
    customer = db.relationship('Customer', backref='orders')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('skus.id'), nullable=False)
    
    # 商品快照欄位（Confirm 時凍結）
    sku_code = db.Column(db.String(50), nullable=False)
    barcode = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_source = db.Column(db.String(50)) # tiered, air, sea, fixed_freight, override
    air_or_sea = db.Column(db.String(20), nullable=True) # air / sea
    
    unit_price = db.Column(db.Numeric(10, 2), nullable=False) # 預覽值或凍結快照
    amount = db.Column(db.Numeric(10, 2), nullable=False) # unit_price * quantity (含五捨六入)
    
    # 人工覆寫記錄
    is_overridden = db.Column(db.Boolean, default=False)
    override_reason = db.Column(db.Text, nullable=True)
    overridden_by = db.Column(db.String(50), nullable=True)
    overridden_at = db.Column(db.DateTime, nullable=True)
    
    product = db.relationship('SKU')
