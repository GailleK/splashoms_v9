from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum

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
    AddPaymentSerializer,     
    ProductDetailSerializer,
    OrderSerializer,
    OrderEditSerializer,       
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("-created_at")
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["customer_name", "phone", "email"]


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all().order_by("category_name")
    serializer_class = ProductCategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = (
        Product.objects
        .select_related("category")
        .annotate(variants_count=Count("variants"))
        .all()
        .order_by("-created_at")
    )
    serializer_class = ProductSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductSerializer


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

    @action(detail=True, methods=["post"], url_path="add-payment")
    def add_payment(self, request, pk=None):
        order = self.get_object()
        s = AddPaymentSerializer(data=request.data, context={"order": order})
        s.is_valid(raise_exception=True)
        payment = s.save()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["patch"], url_path="edit")
    def edit_order(self, request, pk=None):
        order = self.get_object()

        ser = OrderEditSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        with transaction.atomic():
            # 1) customer
            customer_id = data.get("customer_id")
            if customer_id:
                order.customer = Customer.objects.get(pk=customer_id)

            # 2) update quantities
            items_payload = data.get("items", [])
            items_by_id = {}
            for it in items_payload:
                item_id = it.get("order_item_id") or it.get("id")
                items_by_id[int(item_id)] = int(it["quantity"])

            # lock items rows
            qs = OrderItem.objects.select_for_update().filter(order=order)

            for oi in qs:
                # IMPORTANT: check both possible pk names
                # if your model uses order_item_id as pk, oi.pk still works.
                if oi.pk in items_by_id:
                    oi.quantity = items_by_id[oi.pk]
                    # also update total per line if you store it
                    if hasattr(oi, "total"):
                        oi.total = Decimal(str(oi.unit_price)) * Decimal(str(oi.quantity))
                    oi.save()

            # 3) recompute subtotal/total
            subtotal = Decimal("0.00")
            for oi in OrderItem.objects.filter(order=order):
                line = Decimal(str(oi.unit_price)) * Decimal(str(oi.quantity))
                subtotal += line

            # you currently store subtotal_amount and total_amount
            if hasattr(order, "subtotal_amount"):
                order.subtotal_amount = subtotal
            order.total_amount = subtotal

            # 4) payment fields
            method = data["payment_method"]
            utang_duration = data.get("utang_duration")
            paid_total = Decimal(str(data["paid_amount_total"]))

            if paid_total < 0:
                paid_total = Decimal("0.00")
            if paid_total > order.total_amount:
                paid_total = order.total_amount

            # compute due date if Utang
            utang_due_date = None
            if method == "Utang":
                # your PaymentSerializer expects utang_duration
                if not utang_duration:
                    utang_duration = "7D"

                days = 30 if utang_duration == "1M" else 7
                utang_due_date = (timezone.now() + timedelta(days=days)).date()
            else:
                utang_duration = None
                utang_due_date = None

            # 5) reset payments (simple)
            Payment.objects.filter(order=order).delete()
            Payment.objects.create(
                customer=order.customer,
                order=order,
                payment_method=method,
                utang_duration=utang_duration,
                utang_due_date=utang_due_date,
                amount_paid=paid_total,
                notes=getattr(order, "notes", "") or "",
            )

            # 6) payment_status
            if paid_total <= 0:
                order.payment_status = Order.PaymentStatus.UNPAID
            elif paid_total < order.total_amount:
                order.payment_status = Order.PaymentStatus.PARTIALLY_PAID
            else:
                order.payment_status = Order.PaymentStatus.PAID

            order.save()

        order.refresh_from_db()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        order = self.get_object()

        ser = OrderEditSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        with transaction.atomic():
            # 1) customer
            customer_id = data.get("customer_id", None)
            if customer_id is None:
                order.customer = None
            else:
                order.customer = Customer.objects.get(pk=customer_id)

            # 2) update item quantities
            items_payload = data["items"]
            items_by_id = {it["order_item_id"]: it["quantity"] for it in items_payload}

            # IMPORTANT: only update items that belong to this order
            qs = OrderItem.objects.select_for_update().filter(order=order)
            for oi in qs:
                if oi.order_item_id in items_by_id:
                    oi.quantity = items_by_id[oi.order_item_id]
                    oi.save(update_fields=["quantity"])

            # 3) recompute total_amount from DB (trusted)
            qs = OrderItem.objects.filter(order=order)
            total = Decimal("0.00")
            for oi in qs:
                total += (Decimal(str(oi.unit_price)) * Decimal(str(oi.quantity)))
            order.total_amount = total

            # 4) payment method + due date (if Utang)
            payment_method = data["payment_method"]
            utang_duration = data.get("utang_duration")

            # compute due date if Utang
            utang_due_date = None
            if payment_method == "Utang":
                if utang_duration == "1_month":
                    utang_due_date = (timezone.now() + timedelta(days=30)).date()
                else:
                    utang_due_date = (timezone.now() + timedelta(days=7)).date()

            # 5) adjust payments to match paid_amount_total
            # This is the key part: instead of editing old payment rows,
            # we create ONE "Edit Adjustment" entry so total paid becomes exactly what user wants.

            desired_paid = Decimal(str(data["paid_amount_total"]))
            if desired_paid < 0:
                desired_paid = Decimal("0.00")
            if desired_paid > total:
                desired_paid = total

            current_paid = Decimal("0.00")
            for p in Payment.objects.filter(order=order):
                current_paid += Decimal(str(p.amount_paid))

            diff = desired_paid - current_paid

            # If diff != 0, create an adjustment payment
            # (If diff is negative, it means user reduced paid total; this records a correction)
            if diff != 0:
                Payment.objects.create(
                    order=order,
                    payment_method=payment_method,
                    amount_paid=diff,
                    payment_date=timezone.now(),
                    utang_due_date=utang_due_date,  # only meaningful for Utang
                    notes="Edit adjustment",  # if you have a notes field; remove if not
                )

            # 6) update order.payment_status based on desired_paid vs total
            if total == 0:
                order.payment_status = "Unpaid"
            elif desired_paid <= 0:
                order.payment_status = "Unpaid"
            elif desired_paid >= total:
                order.payment_status = "Paid"
            else:
                order.payment_status = "Partially Paid"

            order.save()

        # return updated order
        order.refresh_from_db()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related("order", "variant", "variant__product", "variant__scent").all().order_by("-created_at")
    serializer_class = OrderItemSerializer

class ProductVariantAdminViewSet(viewsets.ModelViewSet):
    queryset = (
        ProductVariant.objects
        .select_related("product", "product__category", "scent")
        .all()
        .order_by("-created_at")
    )
    serializer_class = ProductVariantSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs

    @action(detail=False, methods=["get"], url_path="choices")
    def choices(self, request):
        return Response({
            "size": [{"value": v, "label": l} for v, l in ProductVariant.Size.choices],
            "size_unit": [{"value": v, "label": l} for v, l in ProductVariant.SizeUnit.choices],
        })