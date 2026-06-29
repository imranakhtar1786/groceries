from django.urls import path, include
from rest_framework.routers import DefaultRouter
from locations.views import LocationViewSet, LeadViewSet, CheckDeliveryView
from products.views import CategoryViewSet, ProductViewSet
from users.views import UserViewSet, AddressViewSet
from orders.views import OrderViewSet
from promotions.views import CouponViewSet

router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'leads', LeadViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'users', UserViewSet)
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'coupons', CouponViewSet, basename='coupon')

urlpatterns = [
    path('check-delivery/', CheckDeliveryView.as_view(), name='check-delivery'),
    path('', include(router.urls)),
]
