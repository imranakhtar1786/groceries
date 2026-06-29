from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Order, OrderItem
from products.models import Product
from products.serializers import ProductSerializer
from promotions.models import Coupon
from promotions.services import validate_and_calculate_discount
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    input_items = OrderItemInputSerializer(many=True, write_only=True)
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'address', 'coupon', 'coupon_code', 'status', 
            'total_amount', 'discount_amount', 'delivery_charge', 
            'final_amount', 'payment_method', 'delivery_instructions', 
            'created_at', 'updated_at', 'items', 'input_items'
        ]
        read_only_fields = [
            'user', 'coupon', 'status', 'total_amount', 
            'discount_amount', 'delivery_charge', 'final_amount'
        ]

    def validate(self, attrs):
        user = self.context['request'].user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to place an order.")
        
        input_items = attrs.get('input_items')
        if not input_items:
            raise serializers.ValidationError({"input_items": "This field is required and cannot be empty."})
            
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        input_items = validated_data.pop('input_items')
        coupon_code = validated_data.pop('coupon_code', None)
        
        cart_items_data = []
        for item in input_items:
            product = item['product']
            quantity = item['quantity']
            cart_items_data.append({
                'product_id': product.id,
                'quantity': quantity
            })
            
        payment_method = validated_data.get('payment_method', 'ANY')
        delivery_charge = Decimal('50.00')
        
        coupon = None
        discount_amount = Decimal('0.00')
        is_free_delivery = False
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                result = validate_and_calculate_discount(
                    coupon=coupon,
                    user=user,
                    cart_items=cart_items_data,
                    payment_method=payment_method,
                    delivery_charge=delivery_charge
                )
                discount_amount = result['discount_amount']
                is_free_delivery = result['is_free_delivery']
                delivery_charge = result['new_delivery_charge']
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({"coupon_code": "Coupon code is invalid or does not exist."})
            except DjangoValidationError as e:
                msg = e.messages[0] if hasattr(e, 'messages') else str(e)
                msg = msg.replace("['", "").replace("']", "")
                raise serializers.ValidationError({"coupon_code": msg})

        # Calculate total amount
        total_amount = Decimal('0.00')
        for item in input_items:
            product = item['product']
            qty = item['quantity']
            price = product.discount_price if product.discount_price is not None else product.original_price
            total_amount += price * Decimal(str(qty))
            
        # Free delivery policy: orders >= ₹500 get free delivery unless coupon forced free delivery
        if not is_free_delivery and total_amount >= Decimal('500.00'):
            delivery_charge = Decimal('0.00')
            
        final_amount = max(Decimal('0.00'), total_amount - discount_amount + delivery_charge)
        
        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                address=validated_data.get('address'),
                coupon=coupon,
                total_amount=total_amount,
                discount_amount=discount_amount,
                delivery_charge=delivery_charge,
                final_amount=final_amount,
                payment_method=payment_method,
                delivery_instructions=validated_data.get('delivery_instructions', '')
            )
            
            for item in input_items:
                product = item['product']
                qty = item['quantity']
                price = product.discount_price if product.discount_price is not None else product.original_price
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price_at_purchase=price
                )
                
                # Check stock and update
                if product.stock_quantity >= qty:
                    product.stock_quantity -= qty
                    product.save()
                else:
                    raise serializers.ValidationError(
                        {"input_items": f"Product '{product.name}' does not have enough stock. Available: {product.stock_quantity}."}
                    )
            
            if coupon:
                coupon.used_count += 1
                coupon.save()
                
        return order
