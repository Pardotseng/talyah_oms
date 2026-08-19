from app import db
import uuid
import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="Sales")
    is_active = db.Column(db.Boolean, default=True)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_code = db.Column(db.String(50), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    tax_id = db.Column(db.String(20), unique=True, nullable=False)
    credit_limit = db.Column(db.Numeric(12, 2), default=500000.00)
    current_balance = db.Column(db.Numeric(12, 2), default=0.00)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku_code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    origin_price = db.Column(db.Numeric(10, 2), nullable=False)
    air_price = db.Column(db.Numeric(10, 2), nullable=True)
    sea_price = db.Column(db.Numeric(10, 2), nullable=True)
    stock_quantity = db.Column(db.Integer, default=100)
    safety_stock = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.String(36), nullable=False)
    status = db.Column(db.String(30), default="Draft")
    total_amount = db.Column(db.Numeric(10, 2), default=0)
    created_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), nullable=False)
    product_id = db.Column(db.String(36), nullable=False)
    sku_code = db.Column(db.String(50))
    description = db.Column(db.String(200))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2))
    amount = db.Column(db.Numeric(10, 2))
