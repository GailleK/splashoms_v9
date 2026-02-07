# serializers.py
from decimal import Decimal
from django.db import transaction
from rest_framework import serializers

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

# -------------------------
# Simple / base serializers
# -------------------------

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = "__all__"


class ScentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scent
        fields = "__all__"


# -------------------------
# Product + Variants
# -------------------------

class ProductSerializer(serializers.ModelSerializer):
    # Read: show the nested category (nice for UI)
    category = ProductCategorySerializer(read_only=True)

    # Write: allow category_id on create/update
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=ProductCategory.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Product
        fields = "__all__"


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Full serializer (admin/backoffice)
    """
    # Read: show nested product + scent
    product = ProductSerializer(read_only=True)
    scent = ScentSerializer(read_only=True)

    # Write: accept product_id + scent_id from Vue
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    scent_id = serializers.PrimaryKeyRelatedField(
        source="scent",
        queryset=Scent.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ProductVariant
        fields = "__all__"


class ProductVariantPOSSerializer(serializers.ModelSerializer):
    """
    POS-friendly: flat fields for product tiles.
    Your Vue wants: { id, name, size, price, category, scent? }
    """

    id = serializers.IntegerField(source="variant_id", read_only=True)
    name = serializers.CharField(source="product.product_name", read_only=True, allow_null=True)
    category = serializers.CharField(source="product.category.category_name", read_only=True, allow_null=True)
    scent = serializers.CharField(source="scent.name", read_only=True, allow_null=True)
    price = serializers.DecimalField(source="unit_price", max_digits=10, decimal_places=2, read_only=True)

    size = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ["id", "name", "size", "price", "category", "scent", "is_active"]

    def get_size(self, obj):
        """
        Convert size + size_unit to something displayable.
        Examples: "1L", "500L", "500kg", "1gal"
        (You can adjust mapping if you want mL, etc.)
        """
        if not obj.size:
            return None

        unit_map = {
            "Liter": "L",
            "Kilo": "kg",
            "Gallon": "gal",
        }
        u = unit_map.get(obj.size_unit, obj.size_unit or "")
        return f"{obj.size}{u}"


# -------------------------
# Payment (validate clean())
# -------------------------

class PaymentSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        payment_method = attrs.get("payment_method", getattr(self.instance, "payment_method", None))
        utang_duration = attrs.get("utang_duration", getattr(self.instance, "utang_duration", None))
        utang_due_date = attrs.get("utang_due_date", getattr(self.instance, "utang_due_date", None))

        if payment_method == Payment.PaymentMethod.UTANG:
            if not utang_duration:
                raise serializers.ValidationError({"utang_duration": "Required when payment_method is Utang."})
        else:
            # ✅ normalize: force clear utang fields
            attrs["utang_duration"] = None
            attrs["utang_due_date"] = None

        return attrs

    class Meta:
        model = Payment
        fields = "__all__"


# -------------------------
# Orders + Items
# -------------------------

class OrderItemSerializer(serializers.ModelSerializer):
    # Read: show variant details (handy for UI/history)
    variant = ProductVariantSerializer(read_only=True)

    # Write: accept variant_id
    variant_id = serializers.PrimaryKeyRelatedField(
        source="variant",
        queryset=ProductVariant.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ("order",)


class OrderSerializer(serializers.ModelSerializer):
    # Read
    customer = CustomerSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    # ✅ NEW: reverse relation (Payment.order related_name="payments")
    payments = PaymentSerializer(many=True, read_only=True)

    # Write
    customer_id = serializers.PrimaryKeyRelatedField(
        source="customer",
        queryset=Customer.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    # Optional: allow creating/updating items in the same request (non-POS admin usage)
    items_payload = OrderItemSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Order
        fields = "__all__"

    def create(self, validated_data):
        items_data = validated_data.pop("items_payload", [])
        order = super().create(validated_data)

        # create items (if provided)
        for item in items_data:
            # item is already validated by OrderItemSerializer
            # OrderItemSerializer should accept variant_id via source="variant"
            OrderItem.objects.create(order=order, **item)

        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_payload", None)
        order = super().update(instance, validated_data)

        # If items_payload is provided, replace items
        if items_data is not None:
            order.items.all().delete()
            for item in items_data:
                OrderItem.objects.create(order=order, **item)

        return order


# -------------------------
# POS Checkout (recommended)
# -------------------------

class CheckoutItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    customer_name = serializers.CharField()
    payment_method = serializers.ChoiceField(choices=["Cash", "Gcash", "Utang"])
    utang_duration = serializers.ChoiceField(choices=["7D", "1M"], required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    amount_paid = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)

    # accept either qty or quantity from UI by normalizing in validate_items()
    items = serializers.ListField(child=serializers.DictField())

    def validate(self, attrs):
        pm = attrs.get("payment_method")
        ud = attrs.get("utang_duration")

        if pm == "Utang":
            if not ud:
                raise serializers.ValidationError({"utang_duration": "Required when payment_method is Utang."})
        else:
            # if not Utang, ignore utang_duration
            attrs["utang_duration"] = None

        # normalize items payload
        attrs["items"] = self._normalize_items(attrs.get("items", []))
        if not attrs["items"]:
            raise serializers.ValidationError({"items": "At least one item is required."})

        # normalize amount_paid
        ap = attrs.get("amount_paid", None)
        if ap in (None, ""):
            attrs["amount_paid"] = Decimal("0.00")
        else:
            # make sure it's not negative
            if ap < 0:
                raise serializers.ValidationError({"amount_paid": "Must be >= 0."})

        return attrs

    def _normalize_items(self, items):
        """
        Supports:
          {variant_id: 123, qty: 2}
          {variant_id: 123, quantity: 2}
        Returns a list of dicts: [{"variant_id": int, "qty": int}, ...]
        """
        normalized = []
        for raw in items or []:
            if not isinstance(raw, dict):
                continue
            variant_id = raw.get("variant_id")
            qty = raw.get("qty", raw.get("quantity"))
            if variant_id is None or qty is None:
                continue
            try:
                variant_id = int(variant_id)
                qty = int(qty)
            except (TypeError, ValueError):
                continue
            if qty < 1:
                continue
            normalized.append({"variant_id": variant_id, "qty": qty})
        return normalized

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items")
        notes = validated_data.get("notes", "") or ""

        # 1) customer
        customer_name = validated_data["customer_name"].strip()
        if not customer_name:
            raise serializers.ValidationError({"customer_name": "Customer name is required."})

        customer, _ = Customer.objects.get_or_create(customer_name=customer_name)

        payment_method = validated_data["payment_method"]
        utang_duration = validated_data.get("utang_duration")  # already normalized in validate()
        amount_paid = validated_data.get("amount_paid") or Decimal("0.00")

        # 2) compute subtotal first + build order items data
        subtotal = Decimal("0.00")
        order_items_to_create = []

        # fetch variants in one query
        variant_ids = [it["variant_id"] for it in items]
        variants_by_id = {
            v.variant_id: v
            for v in ProductVariant.objects.filter(variant_id__in=variant_ids).select_related("product", "scent")
        }

        missing = [vid for vid in variant_ids if vid not in variants_by_id]
        if missing:
            raise serializers.ValidationError({"items": f"Invalid variant_id(s): {missing}"})

        for it in items:
            variant = variants_by_id[it["variant_id"]]
            qty = it["qty"]

            unit_price = Decimal(str(variant.unit_price or 0))
            line_total = (unit_price * Decimal(qty)).quantize(Decimal("0.01"))
            subtotal += line_total

            order_items_to_create.append(
                OrderItem(
                    variant=variant,
                    quantity=qty,
                    unit_price=unit_price,
                    sku=str(variant.variant_id),
                    total=line_total,
                )
            )

        total = subtotal  # no tax

        # 3) create order FIRST (no payment FK on Order anymore)
        order = Order.objects.create(
            customer=customer,
            notes=notes,
            subtotal_amount=subtotal,
            total_amount=total,
            payment_status=Order.PaymentStatus.UNPAID,  # will finalize below
        )

        # 4) create payment (linked to customer + order)
        payment = Payment.objects.create(
            customer=customer,
            order=order,
            payment_method=payment_method,
            utang_duration=utang_duration if payment_method == "Utang" else None,
            amount_paid=amount_paid,
            notes=notes,
        )

        # 5) create order items
        for oi in order_items_to_create:
            oi.order = order
        OrderItem.objects.bulk_create(order_items_to_create)

        # 6) set payment_status
        if payment_method == "Utang":
            if payment.amount_paid <= 0:
                status_val = Order.PaymentStatus.UNPAID
            elif payment.amount_paid < order.total_amount:
                status_val = Order.PaymentStatus.PARTIALLY_PAID
            else:
                status_val = Order.PaymentStatus.PAID
        else:
            # Cash/Gcash typically means paid-in-full in this POS flow
            status_val = Order.PaymentStatus.PAID

        if order.payment_status != status_val:
            order.payment_status = status_val
            order.save(update_fields=["payment_status"])

        return order