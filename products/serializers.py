from rest_framework import serializers
from django.conf import settings
from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = '__all__'

    def get_image_url(self, obj):
        if obj.image:
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.AWS_STORAGE_BUCKET_NAME}/{obj.image}"
        return None


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    discount_percentage = serializers.IntegerField(
        source='get_discount_percentage',
        read_only=True
    )

    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'