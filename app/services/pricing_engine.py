from decimal import Decimal, ROUND_HALF_UP

class PricingEngine:
    @staticmethod
    def five_six_round(value: Decimal) -> int:
        return int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    @classmethod
    def calculate_item_amount(cls, unit_price, quantity, mode='air', product=None):
        price = Decimal(str(unit_price))
        if product:
            if mode == 'air' and product.air_price:
                price = product.air_price
            elif mode == 'sea' and product.sea_price:
                price = product.sea_price
        raw_total = price * quantity
        return price, cls.five_six_round(raw_total)
