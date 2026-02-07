from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .models import ProductVariant, Order, OrderItem, Customer, Product, ProductCategory, Scent, Payment
from .serializers import (
    CustomerSerializer,
    ProductCategorySerializer,
    ProductSerializer,
    ScentSerializer,
    ProductVariantSerializer,
    ProductVariantPOSSerializer,   
    PaymentSerializer,
    OrderSerializer,
    OrderItemSerializer,
    CheckoutSerializer,           
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("-created_at")
    serializer_class = CustomerSerializer


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all().order_by("category_name")
    serializer_class = ProductCategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all().order_by("-created_at")
    serializer_class = ProductSerializer


class ScentViewSet(viewsets.ModelViewSet):
    queryset = Scent.objects.all().order_by("name")
    serializer_class = ScentSerializer


class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        ProductVariant.objects
        .select_related("product", "product__category", "scent")
        .filter(is_active=True, product__is_active=True)
        .order_by("-created_at")
    )
    serializer_class = ProductVariantPOSSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by("-payment_date")
    serializer_class = PaymentSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (
        Order.objects
        .select_related("customer")
        .prefetch_related("items", "items__variant", "payments")
        .all()
        .order_by("-created_at")
    )
    serializer_class = OrderSerializer

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        s = CheckoutSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        order = s.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related("order", "variant", "variant__product", "variant__scent").all().order_by("-created_at")
    serializer_class = OrderItemSerializer
