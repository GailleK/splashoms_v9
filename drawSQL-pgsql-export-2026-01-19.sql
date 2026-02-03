CREATE TABLE "Order Items"(
    "order_item_id" bigserial NOT NULL,
    "order_id" BIGINT NOT NULL,
    "sku" VARCHAR(255) NOT NULL,
    "quantity" INTEGER NOT NULL,
    "unit_price" DECIMAL(8, 2) NOT NULL,
    "total" DECIMAL(8, 2) NOT NULL,
    "created_at" TIMESTAMP(0) WITH
        TIME zone NOT NULL DEFAULT 'now()',
        "updated_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL
);
ALTER TABLE
    "Order Items" ADD PRIMARY KEY("order_item_id");
CREATE TABLE "Order"(
    "order_id" bigserial NOT NULL,
    "customer_id" BIGINT NOT NULL,
    "order_date" TIMESTAMP(0) WITH
        TIME zone NOT NULL DEFAULT 'now()',
        "order_status" VARCHAR(255)
    CHECK
        (
            "order_status" IN('Pending', 'Completed', 'Cancelled')
        ) NOT NULL DEFAULT 'Pending',
        "payment_id" BIGINT NOT NULL,
        "payment_status" VARCHAR(255)
    CHECK
        (
            "payment_status" IN(
                'Unpaid',
                'Partially Paid',
                'Paid',
                'Refunded'
            )
        ) NOT NULL DEFAULT 'Unpaid',
        "notes" VARCHAR(255) NOT NULL,
        "created_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL DEFAULT 'now()',
        "updated_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL DEFAULT 'now()'
);
ALTER TABLE
    "Order" ADD PRIMARY KEY("order_id");
CREATE TABLE "Product Variants"(
    "variant_id" bigserial NOT NULL,
    "product_id" BIGINT NOT NULL,
    "scent" VARCHAR(255) NOT NULL,
    "size" VARCHAR(255) CHECK
        ("size" IN('1', '500')) NOT NULL,
        "size_unit" VARCHAR(255)
    CHECK
        (
            "size_unit" IN('Liter', 'Kilo', 'Gallon')
        ) NOT NULL,
        "is_active" BOOLEAN NOT NULL DEFAULT '1',
        "created_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL DEFAULT 'now()',
        "updated_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL DEFAULT 'now()'
);
ALTER TABLE
    "Product Variants" ADD PRIMARY KEY("variant_id");
CREATE TABLE "Products"(
    "product_id" bigserial NOT NULL,
    "category_id" BIGINT NOT NULL,
    "product_name" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT '1',
    "created_at" TIMESTAMP(0) WITH
        TIME zone NOT NULL DEFAULT 'now()',
        "updated_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL DEFAULT 'now()'
);
ALTER TABLE
    "Products" ADD PRIMARY KEY("product_id");
CREATE TABLE "Product Category"(
    "category_id" bigserial NOT NULL,
    "category_name" VARCHAR(255) NOT NULL,
    "description" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP(0) WITH
        TIME zone NOT NULL DEFAULT 'now()',
        "updated_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL
);
ALTER TABLE
    "Product Category" ADD PRIMARY KEY("category_id");
ALTER TABLE
    "Product Category" ADD CONSTRAINT "product category_category_name_unique" UNIQUE("category_name");
CREATE TABLE "Customers"(
    "customer_id" bigserial NOT NULL,
    "customer_name" VARCHAR(255) NOT NULL,
    "phone" VARCHAR(255) NULL,
    "email" VARCHAR(255) NULL,
    "address" VARCHAR(255) NULL,
    "notes" TEXT NOT NULL,
    "created_at" TIMESTAMP(0) WITH
        TIME zone NOT NULL DEFAULT 'now()',
        "updated_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL DEFAULT 'now()'
);
ALTER TABLE
    "Customers" ADD PRIMARY KEY("customer_id");
CREATE TABLE "Payments"(
    "payment_id" bigserial NOT NULL,
    "payment_date" TIMESTAMP(0) WITH
        TIME zone NOT NULL DEFAULT 'now()',
        "payment_method" VARCHAR(255)
    CHECK
        (
            "payment_method" IN('Cash', 'Gcash')
        ) NOT NULL,
        "amount_paid" DECIMAL(8, 2) NOT NULL,
        "notes" VARCHAR(255) NOT NULL,
        "created_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL DEFAULT 'now()',
        "updated_at" TIMESTAMP(0)
    WITH
        TIME zone NOT NULL DEFAULT 'auto_now()'
);
ALTER TABLE
    "Payments" ADD PRIMARY KEY("payment_id");
CREATE TABLE "Scent"(
    "id" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL
);
ALTER TABLE
    "Scent" ADD PRIMARY KEY("id");
ALTER TABLE
    "Product Variants" ADD CONSTRAINT "product variants_product_id_foreign" FOREIGN KEY("product_id") REFERENCES "Products"("product_id");
ALTER TABLE
    "Order" ADD CONSTRAINT "order_payment_id_foreign" FOREIGN KEY("payment_id") REFERENCES "Payments"("payment_id");
ALTER TABLE
    "Order Items" ADD CONSTRAINT "order items_order_id_foreign" FOREIGN KEY("order_id") REFERENCES "Order"("order_id");
ALTER TABLE
    "Order" ADD CONSTRAINT "order_customer_id_foreign" FOREIGN KEY("customer_id") REFERENCES "Customers"("customer_id");
ALTER TABLE
    "Product Variants" ADD CONSTRAINT "product variants_scent_foreign" FOREIGN KEY("scent") REFERENCES "Scent"("id");
ALTER TABLE
    "Products" ADD CONSTRAINT "products_category_id_foreign" FOREIGN KEY("category_id") REFERENCES "Product Category"("category_id");