from flask import Blueprint, render_template, request, redirect, url_for, flash
from decimal import Decimal
from ..models import db, SKU, Brand

product_bp = Blueprint('product_bp', __name__, url_prefix='/products')

@product_bp.route('/')
def product_list():
    skus = SKU.query.all()
    return render_template('products/list.html', skus=skus)

@product_bp.route('/create', methods=['GET', 'POST'])
def create_product():
    if request.method == 'POST':
        sku_code = request.form.get('sku_code')
        brand_id = request.form.get('brand_id')
        description = request.form.get('description')
        unit = request.form.get('unit')
        original_price = Decimal(request.form.get('original_price', '0'))
        air_price = Decimal(request.form.get('air_price', '0'))
        sea_price = Decimal(request.form.get('sea_price', '0'))

        new_sku = SKU(
            sku_code=sku_code,
            brand_id=brand_id,
            description=description,
            unit=unit,
            original_price=original_price,
            air_price=air_price,
            sea_price=sea_price,
            is_active=True
        )
        db.session.add(new_sku)
        db.session.commit()
        flash(f'成功新增產品 SKU：{sku_code}', 'success')
        return redirect(url_for('product_bp.product_list'))

    brands = Brand.query.all()
    return render_template('products/create.html', brands=brands)

@product_bp.route('/<int:sku_id>/edit', methods=['GET', 'POST'])
def edit_product(sku_id):
    sku = SKU.query.get_or_404(sku_id)
    if request.method == 'POST':
        sku.description = request.form.get('description')
        sku.unit = request.form.get('unit')
        sku.original_price = Decimal(request.form.get('original_price', '0'))
        sku.air_price = Decimal(request.form.get('air_price', '0'))
        sku.sea_price = Decimal(request.form.get('sea_price', '0'))
        sku.is_active = True if request.form.get('is_active') else False
        db.session.commit()
        flash(f'成功更新產品 SKU：{sku.sku_code}', 'success')
        return redirect(url_for('product_bp.product_list'))

    brands = Brand.query.all()
    return render_template('products/edit.html', sku=sku, brands=brands)
