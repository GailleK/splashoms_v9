from django.contrib import admin
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


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "customer_name", "phone", "email", "created_at", "updated_at")
    search_fields = ("customer_name", "phone", "email")
    list_filter = ()
    ordering = ("-created_at",)


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
    list_display = ("variant_id", "product", "scent", "size", "size_unit", "is_active", "created_at", "updated_at")
    search_fields = ("product__product_name", "scent__name")
    list_filter = ("is_active", "size_unit", "size", "scent")
    ordering = ("-created_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "payment_date", "payment_method", "amount_paid", "created_at", "updated_at")
    search_fields = ("payment_id", "notes")
    list_filter = ("payment_method",)
    ordering = ("-payment_date",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_id",
        "customer",
        "order_date",
        "order_status",
        "payment",
        "payment_status",
        "created_at",
        "updated_at",
    )
    search_fields = ("order_id", "customer__customer_name")
    list_filter = ("order_status", "payment_status")
    ordering = ("-order_date",)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order_item_id", "order", "sku", "quantity", "unit_price", "total", "created_at", "updated_at")
    search_fields = ("sku", "order__order_id")
    list_filter = ()
    ordering = ("-created_at",)
