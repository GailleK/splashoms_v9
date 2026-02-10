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
    ProductVariantAdminViewSet
)

router = DefaultRouter()
router.register(r"customers", CustomerViewSet)
router.register(r"categories", ProductCategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"scents", ScentViewSet)
router.register(r"payments", PaymentViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"order-items", OrderItemViewSet)
router.register(r"variants", ProductVariantViewSet, basename="variants-pos")          # GET only, POS
router.register(r"variants-admin", ProductVariantAdminViewSet, basename="variants-admin")  # CRUD

urlpatterns = [
    path("", include(router.urls)),
]
