from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Coupon
from .serializers import CouponSerializer, CouponValidationRequestSerializer, CouponValidationResponseSerializer
from .services import validate_and_calculate_discount

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all().order_by('-id')
    serializer_class = CouponSerializer
    # Allow anyone to read coupons, but only admin/staff to create/update them
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        # If user is not staff, only return active coupons
        if self.request.user and not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    @action(detail=False, methods=['post'], url_path='validate')
    def validate_coupon(self, request):
        """
        POST body:
        {
            "code": "WELCOME100",
            "cart_items": [{"product_id": 1, "quantity": 2}],
            "payment_method": "UPI",
            "delivery_charge": 50.00
        }
        """
        serializer = CouponValidationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "valid": False,
                "message": "Invalid validation request format.",
                "errors": serializer.errors
            }, status=status.HTTP_200_OK)

        code = serializer.validated_data['code']
        cart_items = serializer.validated_data['cart_items']
        payment_method = serializer.validated_data.get('payment_method', 'ANY')
        delivery_charge = serializer.validated_data.get('delivery_charge', 0)

        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            return Response({
                "valid": False,
                "message": "Coupon code is invalid or does not exist."
            }, status=status.HTTP_200_OK)

        try:
            result = validate_and_calculate_discount(
                coupon=coupon,
                user=request.user,
                cart_items=cart_items,
                payment_method=payment_method,
                delivery_charge=delivery_charge
            )
            
            discount = result['discount_amount']
            msg = f"Coupon applied successfully! You got ₹{discount:.2f} off."
            if result['is_free_delivery']:
                msg += " Plus, you get Free Delivery!"

            response_data = {
                "valid": True,
                **result,
                "message": msg
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except ValidationError as e:
            # e.messages is a list of error messages, or we can just use e.message
            err_msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            # Remove any brackets/quotes
            err_msg = err_msg.replace("['", "").replace("']", "")
            return Response({
                "valid": False,
                "message": err_msg
            }, status=status.HTTP_200_OK)
