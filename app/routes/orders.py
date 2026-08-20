from flask import Blueprint, render_template, request, redirect, url_for, flash
from decimal import Decimal
from ..models import db, Order, OrderItem, Customer, SKU
from ..utils import generate_invoice_no, talyah_round

order_bp = Blueprint('order_bp', __name__, url_prefix='/orders')

@order_bp.route('/')
def order_list():
    # 這裡直接使用正確的查詢排序，移除掉原本錯誤且冗餘的函數呼叫
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('orders/list.html', orders=orders)

@order_bp.route('/create', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        customer_code = request.form.get('customer_code')
        customer = Customer.query.get_or_404(customer_code)
        
        # 1. 自動產生訂單編號 {客戶簡碼}{西元年末兩位}{5位流水號}
        invoice_no = generate_invoice_no(customer_code, db.session, Order)
        
        # 2. 建立草稿訂單並寫入客戶快照
        new_order = Order(
            invoice_no=invoice_no,
            customer_id=customer.code,
            customer_name=customer.name,
            customer_address=customer.address,
            customer_tax_id=customer.tax_id,
            customer_phone=customer.phone,
            customer_level_name=customer.level.name if customer.level else '標準級',
            status='draft',
            total_quantity=0,
            total_amount=Decimal('0')
        )
        db.session.add(new_order)
        db.session.commit()
        
        flash(f'成功建立草稿訂單：{invoice_no}', 'success')
        return redirect(url_for('order_bp.edit_order', order_id=new_order.id))
        
    customers = Customer.query.all()
    return render_template('orders/create.html', customers=customers)

@order_bp.route('/<int:order_id>/edit', methods=['GET'])
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    skus = SKU.query.filter_by(is_active=True).all()
    
    # 計算每個 SKU 在本訂單中出現的次數（用來實作步驟 4 的重複警告）
    sku_counts = {}
    for item in order.items:
        sku_counts[item.product_id] = sku_counts.get(item.product_id, 0) + 1
        
    return render_template('orders/edit.html', order=order, skus=skus, sku_counts=sku_counts)

@order_bp.route('/<int:order_id>/add_item', methods=['POST'])
def add_item(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != 'draft':
        flash('已確認的訂單無法修改明細！', 'error')
        return redirect(url_for('order_bp.edit_order', order_id=order.id))
        
    sku_id = request.form.get('sku_id')
    quantity = int(request.form.get('quantity', 1))
    air_or_sea = request.form.get('air_or_sea', 'standard') # standard, air, sea
    
    sku = SKU.query.get_or_404(sku_id)
    
    # 步驟 6：依照價格模式計算建議單價
    unit_price = sku.original_price
    price_source = 'tiered'
    if air_or_sea == 'air':
        unit_price = sku.air_price
        price_source = 'air_freight'
    elif air_or_sea == 'sea':
        unit_price = sku.sea_price
        price_source = 'sea_freight'
        
    # 計算金額並套用五捨六入
    raw_amount = unit_price * quantity
    rounded_amount = talyah_round(raw_amount)
    
    # 建立訂單明細
    item = OrderItem(
        order_id=order.id,
        product_id=sku.id,
        sku_code=sku.sku_code,
        barcode=sku.barcode,
        description=sku.description,
        unit=sku.unit,
        quantity=quantity,
        price_source=price_source,
        air_or_sea=air_or_sea,
        unit_price=unit_price,
        amount=Decimal(rounded_amount),
        is_overridden=False
    )
    db.session.add(item)
    db.session.commit()
    
    # 重新計算訂單總數量與總金額
    recalculate_order_totals(order)
    
    flash(f'已成功加入明細：{sku.description}', 'success')
    return redirect(url_for('order_bp.edit_order', order_id=order.id))

@order_bp.route('/<int:order_id>/confirm', methods=['POST'])
def confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    if not order.items:
        flash('訂單無任何明細，無法進行確認！', 'error')
        return redirect(url_for('order_bp.edit_order', order_id=order.id))
        
    order.status = 'confirmed'
    db.session.commit()
    flash(f'訂單 {order.invoice_no} 已成功確認並鎖定快照！', 'success')
    return redirect(url_for('order_bp.edit_order', order_id=order.id))

@order_bp.route('/<int:order_id>/copy', methods=['POST'])
def copy_order(order_id):
    original = Order.query.get_or_404(order_id)
    
    # 產生新編號
    new_invoice_no = generate_invoice_no(original.customer_id, db.session, Order)
    
    # 複製表頭
    new_order = Order(
        invoice_no=new_invoice_no,
        customer_id=original.customer_id,
        customer_name=original.customer_name,
        customer_address=original.customer_address,
        customer_tax_id=original.customer_tax_id,
        customer_phone=original.customer_phone,
        customer_level_name=original.customer_level_name,
        status='draft',
        remarks=f"由訂單 {original.invoice_no} 複製而來",
        duplicated_from_order_id=original.id,
        total_quantity=original.total_quantity,
        total_amount=original.total_amount
    )
    db.session.add(new_order)
    db.session.flush() # 取得新 ID
    
    # 複製明細項目
    for orig_item in original.items:
        new_item = OrderItem(
            order_id=new_order.id,
            product_id=orig_item.product_id,
            sku_code=orig_item.sku_code,
            barcode=orig_item.barcode,
            description=orig_item.description,
            unit=orig_item.unit,
            quantity=orig_item.quantity,
            price_source=orig_item.price_source,
            air_or_sea=orig_item.air_or_sea,
            unit_price=orig_item.unit_price,
            amount=orig_item.amount,
            is_overridden=orig_item.is_overridden
        )
        db.session.add(new_item)
        
    db.session.commit()
    flash(f'已成功將訂單複製為新草稿：{new_invoice_no}', 'success')
    return redirect(url_for('order_bp.edit_order', order_id=new_order.id))

def recalculate_order_totals(order):
    total_qty = sum(item.quantity for item in order.items)
    total_amt = sum(item.amount for item in order.items)
    order.total_quantity = total_qty
    order.total_amount = total_amt
    db.session.commit()
