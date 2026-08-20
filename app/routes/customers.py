from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import db, Customer, CustomerLevel

customer_bp = Blueprint('customer_bp', __name__, url_prefix='/customers')

@customer_bp.route('/')
def customer_list():
    customers = Customer.query.all()
    return render_template('customers/list.html', customers=customers)

@customer_bp.route('/create', methods=['GET', 'POST'])
def create_customer():
    if request.method == 'POST':
        code = request.form.get('code').strip().upper()
        name = request.form.get('name')
        address = request.form.get('address')
        tax_id = request.form.get('tax_id')
        phone = request.form.get('phone')
        level_id = request.form.get('customer_level_id')

        if Customer.query.get(code):
            flash('客戶代碼已存在！', 'error')
            return redirect(url_for('customer_bp.create_customer'))

        new_customer = Customer(
            code=code,
            name=name,
            address=address,
            tax_id=tax_id,
            phone=phone,
            customer_level_id=level_id if level_id else None
        )
        db.session.add(new_customer)
        db.session.commit()
        flash(f'成功新增客戶：{name}', 'success')
        return redirect(url_for('customer_bp.customer_list'))

    levels = CustomerLevel.query.all()
    return render_template('customers/create.html', levels=levels)

@customer_bp.route('/<string:code>/edit', methods=['GET', 'POST'])
def edit_customer(code):
    customer = Customer.query.get_or_404(code)
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.address = request.form.get('address')
        customer.tax_id = request.form.get('tax_id')
        customer.phone = request.form.get('phone')
        customer.customer_level_id = request.form.get('customer_level_id') or None
        db.session.commit()
        flash(f'成功更新客戶：{customer.name}', 'success')
        return redirect(url_for('customer_bp.customer_list'))

    levels = CustomerLevel.query.all()
    return render_template('customers/edit.html', customer=customer, levels=levels)
