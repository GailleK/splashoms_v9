from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet,
    ProductCategoryViewSet,
    ProductViewSet,
    ScentViewSet,
    ProductVariantViewSet,
    PaymentViewSet,
    OrderViewSet,
    OrderItemViewSet,
)

router = DefaultRouter()
router.register(r"customers", CustomerViewSet)
router.register(r"categories", ProductCategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"scents", ScentViewSet)
router.register(r"variants", ProductVariantViewSet)
router.register(r"payments", PaymentViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"order-items", OrderItemViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
