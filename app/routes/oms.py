from flask import Blueprint, request, jsonify, session
from app.models import db, Customer, Product, Order, OrderItem, AuditLog
from app.services.pricing_engine import PricingEngine
from decimal import Decimal
import datetime
from sqlalchemy import func

oms_bp = Blueprint('oms', __name__)

def log_action(action, details=""):
    try:
        log = AuditLog(username=session.get('username', 'system'), action=action, details=details)
        db.session.add(log)
        db.session.commit()
    except:
        db.session.rollback()

@oms_bp.route('/api/bi/stats', methods=['GET'])
def api_bi_stats():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    total_revenue = db.session.query(func.sum(Order.total_amount)).filter(Order.status != 'Cancelled').scalar() or 0
    return jsonify({
        "revenue": float(total_revenue),
        "customers_count": Customer.query.filter_by(is_active=True).count(),
        "products_count": Product.query.filter_by(is_active=True).count(),
        "pending_orders": Order.query.filter_by(status='Draft').count()
    })

@oms_bp.route('/api/customers', methods=['GET', 'POST'])
def api_customers():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    if request.method == 'POST':
        data = request.json or {}
        name = data.get('name', '').strip()
        tax_id = data.get('tax_id', '').strip()
        if not name or not tax_id: return jsonify({"error": "名稱與統編為必填"}), 400
        if Customer.query.filter_by(tax_id=tax_id).first(): return jsonify({"error": "統一編號已存在"}), 400
        
        cust = Customer(
            name=name, tax_id=tax_id,
            customer_code=data.get('customer_code'),
            phone=data.get('phone'), address=data.get('address'),
            credit_limit=Decimal(str(data.get('credit_limit', 500000)))
        )
        db.session.add(cust)
        db.session.commit()
        log_action("建立客戶", f"成功建立客戶 {name}")
        return jsonify({"message": "客戶建立成功"}), 201

    custs = Customer.query.filter_by(is_active=True).all()
    return jsonify([{
        "id": c.id, "name": c.name, "tax_id": c.tax_id,
        "customer_code": c.customer_code, "phone": c.phone,
        "credit_limit": float(c.credit_limit), "current_balance": float(c.current_balance)
    } for c in custs])

@oms_bp.route('/api/inventory', methods=['GET', 'POST'])
def api_inventory():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    if request.method == 'POST':
        data = request.json or {}
        sku_code = data.get('sku_code', '').strip()
        description = data.get('description', '').strip()
        origin_price = data.get('origin_price')
        
        if sku_code and description and origin_price is not None:
            if Product.query.filter_by(sku_code=sku_code).first(): return jsonify({"error": "SKU 已存在"}), 400
            prod = Product(
                sku_code=sku_code, description=description,
                origin_price=Decimal(str(origin_price)),
                air_price=Decimal(str(data.get('air_price'))) if data.get('air_price') else None,
                sea_price=Decimal(str(data.get('sea_price'))) if data.get('sea_price') else None,
                stock_quantity=int(data.get('stock_quantity', 100))
            )
            db.session.add(prod)
            db.session.commit()
            log_action("建立商品", f"成功建立 SKU {sku_code}")
            return jsonify({"message": "商品建立成功"}), 201
        
        prod_id = data.get('product_id')
        delta = int(data.get('delta', 0))
        prod = Product.query.get(prod_id)
        if not prod: return jsonify({"error": "找不到商品"}), 404
        prod.stock_quantity += delta
        db.session.commit()
        log_action("庫存調整", f"SKU {prod.sku_code} 調整: {delta}")
        return jsonify({"message": "庫存調整成功", "stock": prod.stock_quantity})

    prods = Product.query.all()
    return jsonify([{
        "id": p.id, "sku_code": p.sku_code, "description": p.description,
        "origin_price": float(p.origin_price),
        "air_price": float(p.air_price) if p.air_price else None,
        "sea_price": float(p.sea_price) if p.sea_price else None,
        "stock": p.stock_quantity, "safety_stock": p.safety_stock,
        "status": "充足" if p.stock_quantity > p.safety_stock else "⚠️ 告急"
    } for p in prods])

@oms_bp.route('/api/orders/status', methods=['POST'])
def api_update_order_status():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.json or {}
    order_id = data.get('order_id')
    new_status = data.get('status')
    order = Order.query.get(order_id)
    if not order: return jsonify({"error": "找不到訂單"}), 404
    
    old_status = order.status
    order.status = new_status
    
    if new_status == 'Confirmed' and old_status == 'Draft':
        cust = Customer.query.get(order.customer_id)
        if cust.current_balance + order.total_amount > cust.credit_limit:
            return jsonify({"error": "信用額度超標！無法確認訂單"}), 400
        
        items = OrderItem.query.filter_by(order_id=order.id).all()
        for item in items:
            prod = Product.query.get(item.product_id)
            if prod.stock_quantity < item.quantity:
                return jsonify({"error": f"SKU {prod.sku_code} 庫存不足"}), 400
            prod.stock_quantity -= item.quantity
        cust.current_balance += order.total_amount

    db.session.commit()
    log_action("訂單狀態變更", f"訂單 {order.order_number} 從 {old_status} 變更為 {new_status}")
    return jsonify({"message": f"狀態已更新為 {new_status}"})

@oms_bp.route('/api/orders', methods=['GET', 'POST'])
def api_orders():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    if request.method == 'POST':
        data = request.json or {}
        customer_id = data.get('customer_id')
        items = data.get('items', [])
        customer = Customer.query.get(customer_id)
        if not customer: return jsonify({"error": "找不到客戶"}), 404

        cust_code = customer.customer_code or "TAL"
        year_suffix = datetime.datetime.now().strftime("%y")
        count = Order.query.filter(Order.order_number.like(f"{cust_code}{year_suffix}%")).count() + 1
        order_number = f"{cust_code}{year_suffix}{count:05d}"

        new_order = Order(order_number=order_number, customer_id=customer_id, status="Draft", created_by=session.get('username'))
        db.session.add(new_order)
        db.session.flush()

        total_amount = Decimal('0')
        for item_data in items:
            prod = Product.query.get(item_data['product_id'])
            qty = int(item_data.get('quantity', 1))
            mode = item_data.get('air_or_sea', 'air')
            
            unit_price, amount = PricingEngine.calculate_item_amount(prod.origin_price, qty, mode, prod)

            order_item = OrderItem(
                order_id=new_order.id, product_id=prod.id,
                sku_code=prod.sku_code, description=prod.description,
                quantity=qty, unit_price=unit_price, amount=amount
            )
            db.session.add(order_item)
            total_amount += Decimal(amount)

        new_order.total_amount = total_amount
        db.session.commit()
        log_action("建立訂單", f"開立草稿訂單 {order_number}，金額: {total_amount}")
        return jsonify({"message": "訂單建立成功", "order_number": order_number}), 201

    orders = Order.query.all()
    result = []
    for o in orders:
        cust = Customer.query.get(o.customer_id)
        result.append({
            "id": o.id, "order_number": o.order_number,
            "customer_name": cust.name if cust else "未知",
            "total_amount": float(o.total_amount), "status": o.status,
            "created_by": o.created_by, "created_at": o.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return jsonify(result)
