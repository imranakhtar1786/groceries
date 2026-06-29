from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from products.models import Product
from orders.models import Order

def validate_and_calculate_discount(coupon, user, cart_items, payment_method=None, delivery_charge=Decimal('0.00')):
    """
    Validates a coupon against cart items, user, payment method, and delivery charge.
    
    Parameters:
      - coupon: Coupon instance
      - user: User instance (can be AnonymousUser)
      - cart_items: list of dicts, e.g., [{"product_id": 1, "quantity": 2}]
      - payment_method: str (e.g. 'UPI', 'COD')
      - delivery_charge: Decimal
      
    Returns:
      dict: {
          "discount_amount": Decimal,
          "is_free_delivery": bool,
          "new_delivery_charge": Decimal,
          "eligible_subtotal": Decimal,
          "total_amount": Decimal,
          "final_amount": Decimal
      }
      
    Raises:
      ValidationError: If any rule is violated
    """
    if not coupon.is_active:
        raise ValidationError("This coupon is not active.")

    # Time-based validation
    now = timezone.now()
    if coupon.start_date and now < coupon.start_date:
        raise ValidationError("This coupon is not yet valid.")
    if coupon.expiry_date and now > coupon.expiry_date:
        raise ValidationError("This coupon has expired.")

    # Global usage limit validation
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise ValidationError("This coupon usage limit has been reached.")

    # Authentication validation for user-specific rules
    if coupon.is_first_order_only or coupon.user_usage_limit is not None:
        if not user or not user.is_authenticated:
            raise ValidationError("You must be logged in to use this coupon.")

    # First-order validation
    if coupon.is_first_order_only:
        existing_orders = Order.objects.filter(user=user).exclude(status='Cancelled')
        if existing_orders.exists():
            raise ValidationError("This coupon is only valid for your first order.")

    # User-specific usage limit validation
    if coupon.user_usage_limit is not None:
        # Note: We filter by the current coupon. Since we'll add the ForeignKey to Order, this works.
        times_used = Order.objects.filter(user=user, coupon=coupon).exclude(status='Cancelled').count()
        if times_used >= coupon.user_usage_limit:
            raise ValidationError(
                f"You have already used this coupon the maximum allowed {coupon.user_usage_limit} time(s)."
            )

    # Payment method validation
    if coupon.applicable_payment_method != 'ANY':
        if not payment_method:
            raise ValidationError(
                f"This coupon requires a payment method to be selected (applicable to {coupon.get_applicable_payment_method_display()})."
            )
        payment_method_upper = payment_method.upper()
        is_upi = "UPI" in payment_method_upper or "QR" in payment_method_upper or "ONLINE" in payment_method_upper
        is_cod = "COD" in payment_method_upper or "CASH" in payment_method_upper or "DELIVERY" in payment_method_upper

        if coupon.applicable_payment_method == 'UPI' and not is_upi:
            raise ValidationError("This coupon is only valid for UPI payments.")
        if coupon.applicable_payment_method == 'COD' and not is_cod:
            raise ValidationError("This coupon is only valid for Cash on Delivery (COD) payments.")

    # Cart calculation & eligibility checks
    if not cart_items:
        raise ValidationError("Your cart is empty.")

    product_ids = [item.get('product_id') or item.get('product') for item in cart_items if item.get('product_id') or item.get('product')]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

    total_amount = Decimal('0.00')
    eligible_subtotal = Decimal('0.00')

    has_restrictions = coupon.applicable_categories.exists() or coupon.applicable_products.exists()
    
    # Store category IDs and product IDs for fast lookup
    restricted_category_ids = set()
    if coupon.applicable_categories.exists():
        # Include categories and all their subcategories (recursively)
        for cat in coupon.applicable_categories.all():
            restricted_category_ids.add(cat.id)
            # Find subcategories
            for subcat in cat.subcategories.all():
                restricted_category_ids.add(subcat.id)

    restricted_product_ids = set()
    if coupon.applicable_products.exists():
        restricted_product_ids = set(coupon.applicable_products.values_list('id', flat=True))

    for item in cart_items:
        prod_id = item.get('product_id') or item.get('product')
        qty = item.get('quantity', 1)
        if not prod_id or prod_id not in products:
            continue
        
        product = products[prod_id]
        price = product.discount_price if product.discount_price is not None else product.original_price
        item_total = price * Decimal(str(qty))
        total_amount += item_total

        # Check if this item is eligible for the discount
        is_eligible = True
        if has_restrictions:
            is_eligible = False
            # Check product match
            if prod_id in restricted_product_ids:
                is_eligible = True
            # Check category match
            elif product.category_id in restricted_category_ids:
                is_eligible = True
            elif product.category.parent_id in restricted_category_ids:
                is_eligible = True

        if is_eligible:
            eligible_subtotal += item_total

    if has_restrictions and eligible_subtotal == Decimal('0.00'):
        raise ValidationError("This coupon is not applicable to any of the products in your cart.")

    # Minimum order value validation (checked against the entire cart subtotal)
    if total_amount < coupon.min_order_value:
        raise ValidationError(
            f"This coupon requires a minimum order value of ₹{coupon.min_order_value:.2f}. "
            f"Your current cart value is ₹{total_amount:.2f}."
        )

    # Calculate discount amount
    discount_amount = Decimal('0.00')
    if coupon.discount_type == 'Percent':
        discount_amount = eligible_subtotal * (coupon.value / Decimal('100.00'))
        if coupon.max_discount is not None:
            discount_amount = min(discount_amount, coupon.max_discount)
    elif coupon.discount_type == 'Flat':
        discount_amount = min(coupon.value, eligible_subtotal)

    # Round discount to 2 decimal places
    discount_amount = discount_amount.quantize(Decimal('0.01'))

    # Delivery charge logic
    is_free_delivery = coupon.is_free_delivery
    new_delivery_charge = Decimal('0.00') if is_free_delivery else Decimal(str(delivery_charge))

    # Calculate final amount (cannot go below 0)
    final_amount = max(Decimal('0.00'), total_amount - discount_amount + new_delivery_charge)

    return {
        "discount_amount": discount_amount,
        "is_free_delivery": is_free_delivery,
        "new_delivery_charge": new_delivery_charge,
        "eligible_subtotal": eligible_subtotal,
        "total_amount": total_amount,
        "final_amount": final_amount
    }
