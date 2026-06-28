from django.contrib import admin
from .models import Category, Product, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ['name', 'brand', 'original_price', 'discount_price', 'stock_quantity', 'is_active']
    list_filter = ['category', 'is_active', 'is_trending', 'is_popular']
    search_fields = ['name', 'brand']

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
