from rest_framework import serializers
from .models import Coupon
from products.serializers import CategorySerializer, ProductSerializer

class CouponSerializer(serializers.ModelSerializer):
    applicable_categories_details = CategorySerializer(source='applicable_categories', many=True, read_only=True)
    applicable_products_details = ProductSerializer(source='applicable_products', many=True, read_only=True)

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'value', 'min_order_value', 'max_discount',
            'start_date', 'expiry_date', 'is_active', 'is_first_order_only',
            'is_free_delivery', 'applicable_payment_method', 'applicable_categories',
            'applicable_products', 'applicable_categories_details', 'applicable_products_details',
            'usage_limit', 'used_count', 'user_usage_limit'
        ]
        read_only_fields = ['used_count']

class CartItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class CouponValidationRequestSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    cart_items = CartItemInputSerializer(many=True)
    payment_method = serializers.CharField(required=False, allow_blank=True, default='ANY')
    delivery_charge = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, default=0.00)

class CouponValidationResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    is_free_delivery = serializers.BooleanField(required=False)
    new_delivery_charge = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    eligible_subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    final_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    message = serializers.CharField()
