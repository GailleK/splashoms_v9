from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Customer(models.Model):
    customer_id = models.BigAutoField(primary_key=True)
    customer_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True) 
    address = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      

    class Meta:
        db_table = "Customers"


class ProductCategory(models.Model):
    category_id = models.BigAutoField(primary_key=True)
    category_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)                   

    class Meta:
        db_table = "Product Category"


class Product(models.Model):
    product_id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        db_column="category_id",
        related_name="products",
        null=True, blank=True
    )
    product_name = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      

    class Meta:
        db_table = "Products"


class Scent(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "Scent"


class ProductVariant(models.Model):
    class Size(models.TextChoices):
        ONE = "1", "1"
        FIVE_HUNDRED = "500", "500"

    class SizeUnit(models.TextChoices):
        LITER = "Liter", "Liter"
        KILO = "Kilo", "Kilo"
        GALLON = "Gallon", "Gallon"

    variant_id = models.BigAutoField(primary_key=True)

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        db_column="product_id",
        related_name="variants",
        null=True, blank=True
    )

    # SQL: FOREIGN KEY("scent") REFERENCES "Scent"("id")
    scent = models.ForeignKey(
        Scent,
        on_delete=models.PROTECT,
        db_column="scent",
        related_name="product_variants",
        null=True,
        blank=True
    )

    size = models.CharField(max_length=255, choices=Size.choices, null=True, blank=True)
    size_unit = models.CharField(max_length=255, choices=SizeUnit.choices, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      

    class Meta:
        db_table = "Product Variants"


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "Cash", "Cash"
        GCASH = "Gcash", "Gcash"
        UTANG = "Utang", "Utang"

    class UtangDuration(models.TextChoices):
        DAYS_7 = "7D", "7 days"
        MONTH_1 = "1M", "1 month"

    payment_id = models.BigAutoField(primary_key=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    payment_method = models.CharField(
        max_length=255,
        choices=PaymentMethod.choices
    )

    utang_duration = models.CharField(
        max_length=2,
        choices=UtangDuration.choices,
        null=True,
        blank=True,
    )
    utang_due_date = models.DateField(null=True, blank=True)

    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    notes = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validate consistency
        if self.payment_method == self.PaymentMethod.UTANG:
            if not self.utang_duration:
                raise ValidationError({"utang_duration": "Required when payment_method is Utang."})
            # due date can be auto-computed, so allow blank during create if you compute in save()
        else:
            # Not Utang => these should be empty
            if self.utang_duration or self.utang_due_date:
                raise ValidationError("Utang fields must be empty unless payment_method is Utang.")

    def save(self, *args, **kwargs):
        # Auto compute due date for Utang
        if self.payment_method == self.PaymentMethod.UTANG and self.utang_duration:
            base_date = (self.payment_date or timezone.now()).date()

            if self.utang_duration == self.UtangDuration.DAYS_7:
                self.utang_due_date = base_date + timedelta(days=7)
            elif self.utang_duration == self.UtangDuration.MONTH_1:
                # simplest “1 month” approximation is 30 days;
                # if you want true calendar months, use dateutil.relativedelta in app code.
                self.utang_due_date = base_date + timedelta(days=30)

        super().save(*args, **kwargs)

    class Meta:
        db_table = "Payments"


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "Unpaid", "Unpaid"
        PARTIALLY_PAID = "Partially Paid", "Partially Paid"
        PAID = "Paid", "Paid"
        REFUNDED = "Refunded", "Refunded"

    order_id = models.BigAutoField(primary_key=True)

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        db_column="customer_id",
        related_name="orders",
        null=True, blank=True
    )

    order_date = models.DateTimeField(auto_now_add=True)  

    order_status = models.CharField(
        max_length=255,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        db_column="payment_id",
        related_name="orders",
        null=True,
        blank=True
    )

    payment_status = models.CharField(
        max_length=255,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )

    notes = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      

    class Meta:
        db_table = "Order"


class OrderItem(models.Model):
    order_item_id = models.BigAutoField(primary_key=True)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column="order_id",
        related_name="items",
    )

    sku = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total = models.DecimalField(max_digits=8, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      

    class Meta:
        db_table = "Order Items"
