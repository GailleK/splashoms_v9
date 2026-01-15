from django.db import models

class Customer(models.Model):
    customer_id = models.BigAutoField(primary_key=True)
    customer_name = models.CharField(max_length=200, blank=False)
    phone = models.CharField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=200, blank=True)
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Customers'

    def __str__(self):
        return self.customer_name


class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=200, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Users'

    def __str__(self):
        return self.username


class ProductCategory(models.Model):
    category_id = models.BigAutoField(primary_key=True)
    category_name = models.CharField(max_length=200, blank=False, unique=True)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'Product Categories'

    def __str__(self):
        return self.category_name


class Product(models.Model):
    product_id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        db_column='category_id',
        related_name='products',
    )
    product_name = models.CharField(max_length=200, blank=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Products'

    def __str__(self):
        return self.product_name


class ProductVariant(models.Model):
    variant_id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='variants',
    )
    variant_name = models.CharField(max_length=200, blank=False)
    size_value = models.IntegerField()
    size_unit = models.CharField(max_length=200, blank=False)
    sku = models.CharField(max_length=200, blank=True)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    cost_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Product Variants'

    def __str__(self):
        return f'{self.product} - {self.variant_name} ({self.sku})'


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'

    class PaymentStatus(models.TextChoices):
        UNPAID = 'Unpaid', 'Unpaid'
        PARTIALLY_PAID = 'Partially Paid', 'Partially Paid'
        PAID = 'Paid', 'Paid'
        REFUNDED = 'Refunded', 'Refunded'

    order_id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        db_column='customer_id',
        related_name='orders',
    )
    order_date = models.DateTimeField()
    order_status = models.CharField(
        max_length=255,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    payment_status = models.CharField(
        max_length=255,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Order'

    def __str__(self):
        return f'Order #{self.order_id}'


class OrderItem(models.Model):
    order_item_id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='items',
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        db_column='variant_id',
        related_name='order_items',
    )
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Order Items'

    def __str__(self):
        return f'OrderItem #{self.order_item_id} (Order #{self.order_id})'


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'Cash', 'Cash'
        GCASH = 'Gcash', 'Gcash'

    payment_id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='payments',
    )
    payment_date = models.DateTimeField()
    payment_method = models.CharField(
        max_length=255,
        choices=PaymentMethod.choices,
    )
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    reference_number = models.CharField(max_length=200, blank=False)
    notes = models.TextField()
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'Payments'

    def __str__(self):
        return f'Payment #{self.payment_id} for Order #{self.order_id}'
