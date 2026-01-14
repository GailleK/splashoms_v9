# admin.py
from django.contrib import admin
from .models import (
    Customer,
    User,
    ProductCategory,
    Product,
    ProductVariant,
    Order,
    OrderItem,
    Payment,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "customer_name", "phone", "email", "created_at")
    search_fields = ("customer_name", "phone", "email")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "username", "created_at")
    search_fields = ("username",)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("category_id", "category_name", "created_at")
    search_fields = ("category_name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "product_name", "category", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("product_name",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "variant_id",
        "product",
        "variant_name",
        "sku",
        "unit_price",
        "is_active",
    )
    search_fields = ("variant_name", "sku")
    list_filter = ("is_active",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_id",
        "customer",
        "order_date",
        "order_status",
        "payment_status",
    )
    list_filter = ("order_status", "payment_status")
    search_fields = ("order_id", "customer__customer_name")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order_item_id",
        "order",
        "variant",
        "quantity",
        "unit_price",
        "total",
    )
    search_fields = ("order__order_id", "variant__sku")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_id",
        "order",
        "payment_method",
        "amount_paid",
        "payment_date",
    )
    list_filter = ("payment_method",)
