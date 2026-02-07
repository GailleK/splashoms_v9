from django.contrib import admin
from django.db.models import Sum
from decimal import Decimal

from .models import (
    Customer,
    ProductCategory,
    Product,
    Scent,
    ProductVariant,
    Payment,
    Order,
    OrderItem,
)


# ---------- Inlines ----------

class PaymentInline(admin.TabularInline):
    """
    Show payments under a Customer.
    Requires: Payment.customer FK (related_name="payments" recommended)
    """
    model = Payment
    extra = 0
    fields = ("payment_date", "order", "payment_method", "utang_duration", "utang_due_date", "amount_paid", "notes")
    readonly_fields = ("payment_date",)
    ordering = ("-payment_date",)


class OrderPaymentInline(admin.TabularInline):
    """
    Show payments under an Order (installments, follow-up payments).
    Requires: Payment.order FK with related_name="payments"
    """
    model = Payment
    extra = 0
    fields = ("payment_date", "customer", "payment_method", "utang_duration", "utang_due_date", "amount_paid", "notes")
    readonly_fields = ("payment_date",)
    ordering = ("-payment_date",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("variant", "sku", "quantity", "unit_price", "total")
    readonly_fields = ("total",)


# ---------- Customer ----------

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "customer_name", "phone", "email", "created_at", "updated_at")
    search_fields = ("customer_name", "phone", "email")
    ordering = ("-created_at",)
    inlines = [PaymentInline]  # ✅ payments per customer


# ---------- Product Catalog ----------

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("category_id", "category_name", "created_at", "updated_at")
    search_fields = ("category_name",)
    ordering = ("category_name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "product_name", "category", "is_active", "created_at", "updated_at")
    search_fields = ("product_name",)
    list_filter = ("is_active", "category")
    ordering = ("product_name",)


@admin.register(Scent)
class ScentAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "variant_id", "product", "scent", "size", "size_unit",
        "unit_price", "is_active", "created_at", "updated_at"
    )
    search_fields = ("product__product_name", "scent__name")
    list_filter = ("is_active", "size_unit", "size", "scent")
    ordering = ("-created_at",)


# ---------- Payments ----------

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_id",
        "customer",
        "order",
        "payment_date",
        "payment_method",
        "utang_duration",
        "utang_due_date",
        "amount_paid",
        "created_at",
        "updated_at",
    )
    search_fields = ("payment_id", "notes", "customer__customer_name", "customer__phone", "order__order_id")
    list_filter = ("payment_method", "utang_duration")
    ordering = ("-payment_date",)


# ---------- Orders ----------

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_id",
        "customer",
        "order_date",
        "order_status",
        "payment_status",
        "subtotal_amount",
        "total_amount",
        "payments_count",
        "paid_amount",
        "balance_amount",
        "created_at",
        "updated_at",
    )
    search_fields = ("order_id", "customer__customer_name")
    list_filter = ("order_status", "payment_status")
    ordering = ("-order_date",)
    inlines = [OrderItemInline, OrderPaymentInline]  # ✅ show items + payments on the order page

    def payments_count(self, obj):
        return obj.payments.count()
    payments_count.short_description = "Payments"

    def paid_amount(self, obj):
        agg = obj.payments.aggregate(s=Sum("amount_paid"))
        return agg["s"] or Decimal("0.00")
    paid_amount.short_description = "Paid"

    def balance_amount(self, obj):
        paid = self.paid_amount(obj)
        total = obj.total_amount or Decimal("0.00")
        return total - paid
    balance_amount.short_description = "Balance"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order_item_id", "order", "variant", "sku", "quantity", "unit_price", "total", "created_at", "updated_at")
    search_fields = ("sku", "order__order_id", "variant__variant_id", "variant__product__product_name")
    ordering = ("-created_at",)