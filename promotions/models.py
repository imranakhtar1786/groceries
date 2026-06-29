from django.db import models

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('Percent', 'Percentage'),
        ('Flat', 'Flat Amount'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('UPI', 'UPI'),
        ('COD', 'Cash on Delivery'),
        ('ANY', 'Any'),
    )

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2) # percentage or flat amount
    
    # Validation fields
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Date/Time bounds
    start_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True) # acts as end_date
    
    # Flags/Rules
    is_active = models.BooleanField(default=True)
    is_first_order_only = models.BooleanField(default=False)
    is_free_delivery = models.BooleanField(default=False)
    
    # Payment method restriction
    applicable_payment_method = models.CharField(
        max_length=10, choices=PAYMENT_METHOD_CHOICES, default='ANY'
    )
    
    # Scope restrictions
    applicable_categories = models.ManyToManyField('products.Category', blank=True, related_name='coupons')
    applicable_products = models.ManyToManyField('products.Product', blank=True, related_name='coupons')
    
    # Limits
    usage_limit = models.IntegerField(null=True, blank=True, help_text="Global usage limit")
    used_count = models.IntegerField(default=0, help_text="Times used globally")
    user_usage_limit = models.IntegerField(default=1, null=True, blank=True, help_text="Usage limit per user")

    def __str__(self):
        return f"{self.code} - {self.discount_type} {self.value}"

class Banner(models.Model):
    image = models.ImageField(upload_to='banners/')
    title = models.CharField(max_length=100, blank=True, null=True)
    link_url = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title if self.title else f"Banner #{self.id}"
