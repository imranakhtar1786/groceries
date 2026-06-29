from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from products.models import Category, Product
from users.models import Address
from orders.models import Order, OrderItem
from promotions.models import Coupon
from promotions.services import validate_and_calculate_discount

User = get_user_model()

class CouponTestCase(TestCase):
    def setUp(self):
        # Create categories
        self.grocery = Category.objects.create(name="Grocery")
        self.electronics = Category.objects.create(name="Electronics")
        
        # Create products
        self.apple = Product.objects.create(
            name="Apple",
            original_price=Decimal("100.00"),
            category=self.grocery,
            stock_quantity=100
        )
        self.orange = Product.objects.create(
            name="Orange",
            original_price=Decimal("50.00"),
            discount_price=Decimal("40.00"),  # discounted price is ₹40
            category=self.grocery,
            stock_quantity=100
        )
        self.laptop = Product.objects.create(
            name="Laptop",
            original_price=Decimal("50000.00"),
            category=self.electronics,
            stock_quantity=5
        )

        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword"
        )
        
        # Create address
        self.address = Address.objects.create(
            user=self.user,
            street="123 Street",
            city="City",
            area="Area",
            pin_code="123456"
        )

    def test_percentage_discount_coupon(self):
        # Coupon: 10% OFF
        coupon = Coupon.objects.create(
            code="PERCENT10",
            discount_type="Percent",
            value=Decimal("10.00")
        )
        cart_items = [
            {"product_id": self.apple.id, "quantity": 2},  # ₹200
            {"product_id": self.orange.id, "quantity": 1}   # ₹40
        ]
        
        result = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items,
            payment_method="COD",
            delivery_charge=Decimal("50.00")
        )
        
        # Total = 2*100 + 1*40 = 240
        # Discount = 10% of 240 = 24
        # Delivery = 50
        # Final = 240 - 24 + 50 = 266
        self.assertEqual(result["total_amount"], Decimal("240.00"))
        self.assertEqual(result["discount_amount"], Decimal("24.00"))
        self.assertEqual(result["final_amount"], Decimal("266.00"))

    def test_flat_discount_coupon(self):
        # Coupon: ₹100 OFF
        coupon = Coupon.objects.create(
            code="FLAT100",
            discount_type="Flat",
            value=Decimal("100.00")
        )
        cart_items = [
            {"product_id": self.apple.id, "quantity": 2}  # ₹200
        ]
        
        result = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items,
            payment_method="COD",
            delivery_charge=Decimal("50.00")
        )
        
        # Total = 200, Discount = 100, Delivery = 50, Final = 150
        self.assertEqual(result["total_amount"], Decimal("200.00"))
        self.assertEqual(result["discount_amount"], Decimal("100.00"))
        self.assertEqual(result["final_amount"], Decimal("150.00"))

    def test_minimum_order_value(self):
        # Coupon: ₹200 OFF on ₹1000+ order
        coupon = Coupon.objects.create(
            code="MIN1000",
            discount_type="Flat",
            value=Decimal("200.00"),
            min_order_value=Decimal("1000.00")
        )
        
        # 1. Under minimum order value
        cart_items_under = [{"product_id": self.apple.id, "quantity": 5}]  # ₹500
        with self.assertRaises(ValidationError) as ctx:
            validate_and_calculate_discount(
                coupon=coupon,
                user=self.user,
                cart_items=cart_items_under,
                payment_method="COD",
                delivery_charge=Decimal("50.00")
            )
        self.assertIn("minimum order value of ₹1000.00", str(ctx.exception))

        # 2. Over minimum order value
        cart_items_over = [{"product_id": self.apple.id, "quantity": 11}]  # ₹1100
        result = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items_over,
            payment_method="COD",
            delivery_charge=Decimal("50.00")
        )
        self.assertEqual(result["discount_amount"], Decimal("200.00"))

    def test_first_order_coupon(self):
        coupon = Coupon.objects.create(
            code="WELCOME100",
            discount_type="Flat",
            value=Decimal("100.00"),
            is_first_order_only=True
        )
        cart_items = [{"product_id": self.apple.id, "quantity": 2}]

        # 1. User has no orders -> valid
        result = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items,
            payment_method="COD"
        )
        self.assertEqual(result["discount_amount"], Decimal("100.00"))

        # Create an order for the user
        Order.objects.create(
            user=self.user,
            address=self.address,
            total_amount=Decimal("200.00"),
            discount_amount=Decimal("0.00"),
            delivery_charge=Decimal("50.00"),
            final_amount=Decimal("250.00"),
            payment_method="COD"
        )

        # 2. User has an existing order -> invalid
        with self.assertRaises(ValidationError) as ctx:
            validate_and_calculate_discount(
                coupon=coupon,
                user=self.user,
                cart_items=cart_items,
                payment_method="COD"
            )
        self.assertIn("only valid for your first order", str(ctx.exception))

    def test_category_coupon(self):
        # Coupon: 20% OFF on Grocery
        coupon = Coupon.objects.create(
            code="GROCERY20",
            discount_type="Percent",
            value=Decimal("20.00")
        )
        coupon.applicable_categories.add(self.grocery)

        # Cart contains Apple (Grocery, ₹100) and Laptop (Electronics, ₹50000)
        cart_items = [
            {"product_id": self.apple.id, "quantity": 2},     # ₹200 (eligible)
            {"product_id": self.laptop.id, "quantity": 1}     # ₹50000 (not eligible)
        ]
        
        result = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items,
            payment_method="COD"
        )
        
        # Eligible subtotal = ₹200. Discount = 20% of 200 = ₹40
        self.assertEqual(result["eligible_subtotal"], Decimal("200.00"))
        self.assertEqual(result["discount_amount"], Decimal("40.00"))

    def test_product_coupon(self):
        # Coupon: ₹50 OFF on Apple
        coupon = Coupon.objects.create(
            code="APPLE50",
            discount_type="Flat",
            value=Decimal("50.00")
        )
        coupon.applicable_products.add(self.apple)

        # Cart contains Apple (₹100) and Orange (₹40)
        cart_items = [
            {"product_id": self.apple.id, "quantity": 2},     # ₹200 (eligible)
            {"product_id": self.orange.id, "quantity": 1}     # ₹40 (not eligible)
        ]
        
        result = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items,
            payment_method="COD"
        )
        
        # Eligible subtotal = ₹200. Flat discount of 50 applies.
        self.assertEqual(result["eligible_subtotal"], Decimal("200.00"))
        self.assertEqual(result["discount_amount"], Decimal("50.00"))

    def test_max_discount_limit(self):
        # Coupon: 20% OFF up to ₹500
        coupon = Coupon.objects.create(
            code="SAVE20",
            discount_type="Percent",
            value=Decimal("20.00"),
            max_discount=Decimal("500.00")
        )
        
        # 1. Total ₹1000 -> 20% is 200 (below cap)
        cart_items_1 = [{"product_id": self.apple.id, "quantity": 10}] # ₹1000
        result_1 = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items_1,
            payment_method="COD"
        )
        self.assertEqual(result_1["discount_amount"], Decimal("200.00"))

        # 2. Total ₹4000 -> 20% is 800 (capped at 500)
        cart_items_2 = [{"product_id": self.apple.id, "quantity": 40}] # ₹4000
        result_2 = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items_2,
            payment_method="COD"
        )
        self.assertEqual(result_2["discount_amount"], Decimal("500.00"))

    def test_free_delivery_coupon(self):
        # Coupon: FREESHIP
        coupon = Coupon.objects.create(
            code="FREESHIP",
            discount_type="Flat",
            value=Decimal("0.00"),
            is_free_delivery=True
        )
        cart_items = [{"product_id": self.apple.id, "quantity": 1}]
        
        result = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items,
            payment_method="COD",
            delivery_charge=Decimal("50.00")
        )
        
        self.assertTrue(result["is_free_delivery"])
        self.assertEqual(result["new_delivery_charge"], Decimal("0.00"))
        self.assertEqual(result["discount_amount"], Decimal("0.00"))

    def test_payment_method_coupons(self):
        # UPI Coupon
        upi_coupon = Coupon.objects.create(
            code="UPI50",
            discount_type="Flat",
            value=Decimal("50.00"),
            applicable_payment_method="UPI"
        )
        cart_items = [{"product_id": self.apple.id, "quantity": 2}]

        # 1. Invalid payment method (COD)
        with self.assertRaises(ValidationError) as ctx:
            validate_and_calculate_discount(
                coupon=upi_coupon,
                user=self.user,
                cart_items=cart_items,
                payment_method="COD"
            )
        self.assertIn("only valid for UPI payments", str(ctx.exception))

        # 2. Valid payment method (UPI)
        result = validate_and_calculate_discount(
            coupon=upi_coupon,
            user=self.user,
            cart_items=cart_items,
            payment_method="UPI"
        )
        self.assertEqual(result["discount_amount"], Decimal("50.00"))

        # COD Coupon
        cod_coupon = Coupon.objects.create(
            code="COD10",
            discount_type="Percent",
            value=Decimal("10.00"),
            applicable_payment_method="COD"
        )
        
        # 1. Invalid payment method (UPI)
        with self.assertRaises(ValidationError) as ctx:
            validate_and_calculate_discount(
                coupon=cod_coupon,
                user=self.user,
                cart_items=cart_items,
                payment_method="UPI"
            )
        self.assertIn("only valid for Cash on Delivery", str(ctx.exception))

        # 2. Valid payment method (COD)
        result_cod = validate_and_calculate_discount(
            coupon=cod_coupon,
            user=self.user,
            cart_items=cart_items,
            payment_method="Cash on Delivery"
        )
        self.assertEqual(result_cod["discount_amount"], Decimal("20.00"))

    def test_time_based_coupon(self):
        now = timezone.now()
        
        # Coupon valid only in the future
        future_coupon = Coupon.objects.create(
            code="FUTURE",
            discount_type="Flat",
            value=Decimal("10.00"),
            start_date=now + timezone.timedelta(days=1),
            expiry_date=now + timezone.timedelta(days=2)
        )
        cart_items = [{"product_id": self.apple.id, "quantity": 1}]
        
        with self.assertRaises(ValidationError) as ctx:
            validate_and_calculate_discount(
                coupon=future_coupon,
                user=self.user,
                cart_items=cart_items,
                payment_method="COD"
            )
        self.assertIn("not yet valid", str(ctx.exception))

        # Coupon valid in the past
        past_coupon = Coupon.objects.create(
            code="EXPIRED",
            discount_type="Flat",
            value=Decimal("10.00"),
            start_date=now - timezone.timedelta(days=2),
            expiry_date=now - timezone.timedelta(days=1)
        )
        
        with self.assertRaises(ValidationError) as ctx:
            validate_and_calculate_discount(
                coupon=past_coupon,
                user=self.user,
                cart_items=cart_items,
                payment_method="COD"
            )
        self.assertIn("has expired", str(ctx.exception))

    def test_usage_limit_coupon(self):
        # Coupon limited to 1 use globally
        coupon = Coupon.objects.create(
            code="LIMIT1",
            discount_type="Flat",
            value=Decimal("10.00"),
            usage_limit=1,
            used_count=0
        )
        cart_items = [{"product_id": self.apple.id, "quantity": 1}]

        # 1. Valid first time
        result = validate_and_calculate_discount(
            coupon=coupon,
            user=self.user,
            cart_items=cart_items,
            payment_method="COD"
        )
        self.assertEqual(result["discount_amount"], Decimal("10.00"))

        # Increment used_count
        coupon.used_count = 1
        coupon.save()

        # 2. Invalid second time
        with self.assertRaises(ValidationError) as ctx:
            validate_and_calculate_discount(
                coupon=coupon,
                user=self.user,
                cart_items=cart_items,
                payment_method="COD"
            )
        self.assertIn("usage limit has been reached", str(ctx.exception))
