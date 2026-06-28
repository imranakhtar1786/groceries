from django.urls import path, include
from rest_framework.routers import DefaultRouter
from locations.views import LocationViewSet, LeadViewSet
from products.views import CategoryViewSet, ProductViewSet
from users.views import UserViewSet, AddressViewSet
from orders.views import OrderViewSet

router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'leads', LeadViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'users', UserViewSet)
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]
