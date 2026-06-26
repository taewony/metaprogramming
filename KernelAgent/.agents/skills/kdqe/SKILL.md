---
name: kdqe
description: Unified schema and instructions for querying the TechShop e-commerce database. Use this to translate natural language queries to SQLite SQL.
---
# TechShop Database Schema Specification

This document specifies the SQLite database schema for the TechShop e-commerce database. Use this schema to generate correct SQL queries to answer user questions.

## Tables

### Table: `categories`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `parent_id` | INTEGER | No | NULL | No |
| `name` | TEXT | Yes | NULL | No |
| `slug` | TEXT | Yes | NULL | No |
| `depth` | INTEGER | Yes | 0 | No |
| `sort_order` | INTEGER | Yes | 0 | No |
| `is_active` | INTEGER | Yes | 1 | No |
| `created_at` | TEXT | Yes | NULL | No |
| `updated_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id       INTEGER NULL REFERENCES categories(id),  -- parent category (NULL=root)
    name            TEXT NOT NULL,                           -- category name
    slug            TEXT NOT NULL UNIQUE,                    -- URL-safe identifier
    depth           INTEGER NOT NULL DEFAULT 0,              -- 0=top, 1=mid, 2=sub
    sort_order      INTEGER NOT NULL DEFAULT 0,              -- display order
    is_active       INTEGER NOT NULL DEFAULT 1,              -- active flag (0/1)
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
```

### Table: `suppliers`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `company_name` | TEXT | Yes | NULL | No |
| `business_number` | TEXT | Yes | NULL | No |
| `contact_name` | TEXT | Yes | NULL | No |
| `phone` | TEXT | Yes | NULL | No |
| `email` | TEXT | Yes | NULL | No |
| `address` | TEXT | No | NULL | No |
| `is_active` | INTEGER | Yes | 1 | No |
| `created_at` | TEXT | Yes | NULL | No |
| `updated_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE suppliers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name    TEXT NOT NULL,                           -- company name
    business_number TEXT NOT NULL,                           -- business registration number (fictional)
    contact_name    TEXT NOT NULL,                           -- contact person
    phone           TEXT NOT NULL,                           -- 020-XXXX-XXXX (fictional number)
    email           TEXT NOT NULL,                           -- contact@xxx.test.kr
    address         TEXT,                                    -- business address
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
```

### Table: `products`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `category_id` | INTEGER | Yes | NULL | No |
| `supplier_id` | INTEGER | Yes | NULL | No |
| `successor_id` | INTEGER | No | NULL | No |
| `name` | TEXT | Yes | NULL | No |
| `sku` | TEXT | Yes | NULL | No |
| `brand` | TEXT | Yes | NULL | No |
| `model_number` | TEXT | No | NULL | No |
| `description` | TEXT | No | NULL | No |
| `specs` | TEXT | No | NULL | No |
| `price` | REAL | Yes | NULL | No |
| `cost_price` | REAL | Yes | NULL | No |
| `stock_qty` | INTEGER | Yes | 0 | No |
| `weight_grams` | INTEGER | No | NULL | No |
| `is_active` | INTEGER | Yes | 1 | No |
| `discontinued_at` | TEXT | No | NULL | No |
| `created_at` | TEXT | Yes | NULL | No |
| `updated_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    supplier_id     INTEGER NOT NULL REFERENCES suppliers(id),
    successor_id    INTEGER NULL REFERENCES products(id),   -- next-generation replacement product
    name            TEXT NOT NULL,                           -- product name
    sku             TEXT NOT NULL UNIQUE,                    -- stock keeping unit (e.g. LA-GEN-Samsung-00001)
    brand           TEXT NOT NULL,                           -- brand name
    model_number    TEXT,                                    -- model number
    description     TEXT,                                    -- product description
    specs           TEXT NULL,                               -- JSON product specifications
    price           REAL NOT NULL CHECK(price >= 0),           -- current selling price (KRW)
    cost_price      REAL NOT NULL CHECK(cost_price >= 0),    -- cost price (KRW)
    stock_qty  INTEGER NOT NULL DEFAULT 0,              -- current stock quantity
    weight_grams    INTEGER,                                 -- shipping weight (g)
    is_active       INTEGER NOT NULL DEFAULT 1,              -- on sale flag
    discontinued_at TEXT NULL,                               -- discontinuation date (NULL=active)
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
```

### Table: `product_images`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `product_id` | INTEGER | Yes | NULL | No |
| `image_url` | TEXT | Yes | NULL | No |
| `file_name` | TEXT | Yes | NULL | No |
| `image_type` | TEXT | Yes | NULL | No |
| `alt_text` | TEXT | No | NULL | No |
| `width` | INTEGER | No | NULL | No |
| `height` | INTEGER | No | NULL | No |
| `file_size` | INTEGER | No | NULL | No |
| `sort_order` | INTEGER | Yes | 1 | No |
| `is_primary` | INTEGER | Yes | 0 | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE product_images (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    image_url       TEXT NOT NULL,                           -- image path/URL
    file_name       TEXT NOT NULL,                           -- filename (e.g. 42_1.jpg)
    image_type      TEXT NOT NULL,                           -- main/angle/side/back/detail/package/lifestyle/accessory/size_comparison
    alt_text        TEXT,                                    -- alt text
    width           INTEGER,                                 -- image width (px)
    height          INTEGER,                                 -- image height (px)
    file_size       INTEGER,                                 -- file size (bytes, after download)
    sort_order      INTEGER NOT NULL DEFAULT 1,              -- display order
    is_primary      INTEGER NOT NULL DEFAULT 0,              -- primary image flag
    created_at      TEXT NOT NULL
)
```

### Table: `product_prices`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `product_id` | INTEGER | Yes | NULL | No |
| `price` | REAL | Yes | NULL | No |
| `started_at` | TEXT | Yes | NULL | No |
| `ended_at` | TEXT | No | NULL | No |
| `change_reason` | TEXT | No | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE product_prices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    price           REAL NOT NULL,                           -- selling price for this period
    started_at      TEXT NOT NULL,                           -- effective start date
    ended_at        TEXT NULL,                               -- effective end date (NULL=current)
    change_reason   TEXT                                     -- regular/promotion/price_drop/cost_increase
)
```

### Table: `customers`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `email` | TEXT | Yes | NULL | No |
| `password_hash` | TEXT | Yes | NULL | No |
| `name` | TEXT | Yes | NULL | No |
| `phone` | TEXT | Yes | NULL | No |
| `birth_date` | TEXT | No | NULL | No |
| `gender` | TEXT | No | NULL | No |
| `grade` | TEXT | Yes | 'BRONZE' | No |
| `point_balance` | INTEGER | Yes | 0 | No |
| `acquisition_channel` | TEXT | No | NULL | No |
| `is_active` | INTEGER | Yes | 1 | No |
| `last_login_at` | TEXT | No | NULL | No |
| `created_at` | TEXT | Yes | NULL | No |
| `updated_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE customers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,                    -- email (fictional domain)
    password_hash   TEXT NOT NULL,                           -- SHA-256 hash (fictional)
    name            TEXT NOT NULL,                           -- customer name
    phone           TEXT NOT NULL,                           -- 020-XXXX-XXXX (fictional number)
    birth_date      TEXT NULL,                               -- birth date (YYYY-MM-DD, ~15% NULL)
    gender          TEXT NULL,                               -- M/F (NULL ~10%, male 65%)
    grade           TEXT NOT NULL DEFAULT 'BRONZE' CHECK(grade IN ('BRONZE','SILVER','GOLD','VIP')),
    point_balance   INTEGER NOT NULL DEFAULT 0 CHECK(point_balance >= 0),
    acquisition_channel TEXT NULL,                            -- organic/search_ad/social/referral/direct
    is_active       INTEGER NOT NULL DEFAULT 1,              -- active status (0=deactivated)
    last_login_at   TEXT NULL,                               -- last login (NULL=never logged in)
    created_at      TEXT NOT NULL,                           -- signup date
    updated_at      TEXT NOT NULL
)
```

### Table: `customer_addresses`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `customer_id` | INTEGER | Yes | NULL | No |
| `label` | TEXT | Yes | NULL | No |
| `recipient_name` | TEXT | Yes | NULL | No |
| `phone` | TEXT | Yes | NULL | No |
| `zip_code` | TEXT | Yes | NULL | No |
| `address1` | TEXT | Yes | NULL | No |
| `address2` | TEXT | No | NULL | No |
| `is_default` | INTEGER | Yes | 0 | No |
| `created_at` | TEXT | Yes | NULL | No |
| `updated_at` | TEXT | No | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE customer_addresses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    label           TEXT NOT NULL,                           -- home/office/other
    recipient_name  TEXT NOT NULL,                           -- recipient
    phone           TEXT NOT NULL,                           -- recipient phone
    zip_code        TEXT NOT NULL,                           -- postal code
    address1        TEXT NOT NULL,                           -- base address
    address2        TEXT,                                    -- detailed address
    is_default      INTEGER NOT NULL DEFAULT 0,              -- default address flag
    created_at      TEXT NOT NULL,
    updated_at      TEXT NULL                                -- address change date
)
```

### Table: `staff`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `manager_id` | INTEGER | No | NULL | No |
| `email` | TEXT | Yes | NULL | No |
| `name` | TEXT | Yes | NULL | No |
| `phone` | TEXT | Yes | NULL | No |
| `department` | TEXT | Yes | NULL | No |
| `role` | TEXT | Yes | NULL | No |
| `is_active` | INTEGER | Yes | 1 | No |
| `hired_at` | TEXT | Yes | NULL | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE staff (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    manager_id      INTEGER NULL REFERENCES staff(id),      -- supervisor (Self-Join / recursive CTE)
    email           TEXT NOT NULL UNIQUE,                    -- staffN@techshop-staff.kr
    name            TEXT NOT NULL,
    phone           TEXT NOT NULL,
    department      TEXT NOT NULL,                           -- sales/logistics/CS/marketing/dev/management
    role            TEXT NOT NULL,                           -- admin/manager/staff
    is_active       INTEGER NOT NULL DEFAULT 1,
    hired_at        TEXT NOT NULL,                           -- hire date
    created_at      TEXT NOT NULL
)
```

### Table: `orders`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `order_number` | TEXT | Yes | NULL | No |
| `customer_id` | INTEGER | Yes | NULL | No |
| `address_id` | INTEGER | Yes | NULL | No |
| `staff_id` | INTEGER | No | NULL | No |
| `status` | TEXT | Yes | NULL | No |
| `total_amount` | REAL | Yes | NULL | No |
| `discount_amount` | REAL | Yes | 0 | No |
| `shipping_fee` | REAL | Yes | 0 | No |
| `point_used` | INTEGER | Yes | 0 | No |
| `point_earned` | INTEGER | Yes | 0 | No |
| `notes` | TEXT | No | NULL | No |
| `ordered_at` | TEXT | Yes | NULL | No |
| `completed_at` | TEXT | No | NULL | No |
| `cancelled_at` | TEXT | No | NULL | No |
| `created_at` | TEXT | Yes | NULL | No |
| `updated_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number    TEXT NOT NULL UNIQUE,                    -- ORD-YYYYMMDD-NNNNN
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    address_id      INTEGER NOT NULL REFERENCES customer_addresses(id),
    staff_id        INTEGER NULL REFERENCES staff(id),      -- CS agent (for cancellations/returns)
    status          TEXT NOT NULL,                           -- pending/paid/preparing/shipped/delivered/confirmed/cancelled/return_requested/returned
    total_amount    REAL NOT NULL,                           -- final payment amount
    discount_amount REAL NOT NULL DEFAULT 0,                 -- total discount
    shipping_fee    REAL NOT NULL DEFAULT 0,                 -- shipping fee (free over 50,000 KRW)
    point_used      INTEGER NOT NULL DEFAULT 0,              -- points used
    point_earned    INTEGER NOT NULL DEFAULT 0,              -- points to be earned
    notes           TEXT NULL,                               -- delivery memo (~35%)
    ordered_at      TEXT NOT NULL,                           -- order datetime
    completed_at    TEXT NULL,                               -- purchase confirmation date
    cancelled_at    TEXT NULL,                               -- cancellation date
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
```

### Table: `order_items`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `order_id` | INTEGER | Yes | NULL | No |
| `product_id` | INTEGER | Yes | NULL | No |
| `quantity` | INTEGER | Yes | NULL | No |
| `unit_price` | REAL | Yes | NULL | No |
| `discount_amount` | REAL | Yes | 0 | No |
| `subtotal` | REAL | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE order_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    quantity        INTEGER NOT NULL CHECK(quantity > 0),     -- quantity
    unit_price      REAL NOT NULL CHECK(unit_price >= 0),    -- unit price at order time
    discount_amount REAL NOT NULL DEFAULT 0,                 -- item discount
    subtotal        REAL NOT NULL                            -- (unit_price x quantity) - discount
)
```

### Table: `payments`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `order_id` | INTEGER | Yes | NULL | No |
| `method` | TEXT | Yes | NULL | No |
| `amount` | REAL | Yes | NULL | No |
| `status` | TEXT | Yes | NULL | No |
| `pg_transaction_id` | TEXT | No | NULL | No |
| `card_issuer` | TEXT | No | NULL | No |
| `card_approval_no` | TEXT | No | NULL | No |
| `installment_months` | INTEGER | No | NULL | No |
| `bank_name` | TEXT | No | NULL | No |
| `account_no` | TEXT | No | NULL | No |
| `depositor_name` | TEXT | No | NULL | No |
| `easy_pay_method` | TEXT | No | NULL | No |
| `receipt_type` | TEXT | No | NULL | No |
| `receipt_no` | TEXT | No | NULL | No |
| `paid_at` | TEXT | No | NULL | No |
| `refunded_at` | TEXT | No | NULL | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    method          TEXT NOT NULL,                           -- card/bank_transfer/virtual_account/kakao_pay/naver_pay/point
    amount          REAL NOT NULL CHECK(amount >= 0),         -- payment amount
    status          TEXT NOT NULL CHECK(status IN ('pending','completed','failed','refunded')),
    pg_transaction_id TEXT NULL,                             -- PG transaction ID (fictional)
    card_issuer     TEXT NULL,                               -- card issuer (Shinhan/Samsung/KB/Hyundai/Lotte/Hana/Woori/NH/BC)
    card_approval_no TEXT NULL,                              -- card approval number (8 digits)
    installment_months INTEGER NULL,                         -- installment months (0=lump sum)
    bank_name       TEXT NULL,                               -- bank name (bank transfer/virtual account)
    account_no      TEXT NULL,                               -- virtual account number
    depositor_name  TEXT NULL,                               -- depositor name (bank transfer)
    easy_pay_method TEXT NULL,                               -- easy payment sub-method (KakaoPay balance/linked card, etc.)
    receipt_type    TEXT NULL,                               -- income deduction/expense proof (cash receipt)
    receipt_no      TEXT NULL,                               -- cash receipt number
    paid_at         TEXT NULL,                               -- payment completion time
    refunded_at     TEXT NULL,                               -- refund time
    created_at      TEXT NOT NULL
)
```

### Table: `shipping`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `order_id` | INTEGER | Yes | NULL | No |
| `carrier` | TEXT | Yes | NULL | No |
| `tracking_number` | TEXT | No | NULL | No |
| `status` | TEXT | Yes | NULL | No |
| `shipped_at` | TEXT | No | NULL | No |
| `delivered_at` | TEXT | No | NULL | No |
| `created_at` | TEXT | Yes | NULL | No |
| `updated_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE shipping (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    carrier         TEXT NOT NULL,                           -- CJ Logistics/Hanjin/Logen/Korea Post
    tracking_number TEXT NULL,                               -- tracking number
    status          TEXT NOT NULL,                           -- preparing/shipped/in_transit/delivered/returned
    shipped_at      TEXT NULL,                               -- ship date
    delivered_at    TEXT NULL,                               -- delivery date (must be after shipped_at)
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
```

### Table: `reviews`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `product_id` | INTEGER | Yes | NULL | No |
| `customer_id` | INTEGER | Yes | NULL | No |
| `order_id` | INTEGER | Yes | NULL | No |
| `rating` | INTEGER | Yes | NULL | No |
| `title` | TEXT | No | NULL | No |
| `content` | TEXT | No | NULL | No |
| `is_verified` | INTEGER | Yes | 1 | No |
| `created_at` | TEXT | Yes | NULL | No |
| `updated_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    rating          INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),  -- 1~5 stars (5=40%, 1=5%)
    title           TEXT NULL,                               -- review title (~80%)
    content         TEXT NULL,                               -- review body
    is_verified     INTEGER NOT NULL DEFAULT 1,              -- verified purchase flag
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
```

### Table: `inventory_transactions`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `product_id` | INTEGER | Yes | NULL | No |
| `type` | TEXT | Yes | NULL | No |
| `quantity` | INTEGER | Yes | NULL | No |
| `reference_id` | INTEGER | No | NULL | No |
| `notes` | TEXT | No | NULL | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE inventory_transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    type            TEXT NOT NULL,                           -- inbound/outbound/return/adjustment
    quantity        INTEGER NOT NULL,                        -- positive=inbound, negative=outbound
    reference_id    INTEGER NULL,                            -- related order ID
    notes           TEXT NULL,                               -- initial_stock/regular_inbound/return_inbound
    created_at      TEXT NOT NULL
)
```

### Table: `carts`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `customer_id` | INTEGER | Yes | NULL | No |
| `status` | TEXT | Yes | 'active' | No |
| `created_at` | TEXT | Yes | NULL | No |
| `updated_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE carts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    status          TEXT NOT NULL DEFAULT 'active',          -- active/converted/abandoned
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
```

### Table: `cart_items`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `cart_id` | INTEGER | Yes | NULL | No |
| `product_id` | INTEGER | Yes | NULL | No |
| `quantity` | INTEGER | Yes | 1 | No |
| `added_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE cart_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id         INTEGER NOT NULL REFERENCES carts(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    quantity        INTEGER NOT NULL DEFAULT 1,
    added_at        TEXT NOT NULL
)
```

### Table: `coupons`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `code` | TEXT | Yes | NULL | No |
| `name` | TEXT | Yes | NULL | No |
| `type` | TEXT | Yes | NULL | No |
| `discount_value` | REAL | Yes | NULL | No |
| `min_order_amount` | REAL | No | NULL | No |
| `max_discount` | REAL | No | NULL | No |
| `usage_limit` | INTEGER | No | NULL | No |
| `per_user_limit` | INTEGER | Yes | 1 | No |
| `is_active` | INTEGER | Yes | 1 | No |
| `started_at` | TEXT | Yes | NULL | No |
| `expired_at` | TEXT | Yes | NULL | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE coupons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,                    -- coupon code (CP2401001)
    name            TEXT NOT NULL,                           -- coupon name
    type            TEXT NOT NULL,                           -- percent/fixed
    discount_value  REAL NOT NULL CHECK(discount_value > 0),  -- discount rate (%) or amount (KRW)
    min_order_amount REAL NULL,                              -- minimum order amount
    max_discount    REAL NULL,                               -- max discount amount (percent type)
    usage_limit     INTEGER NULL,                            -- total usage limit
    per_user_limit  INTEGER NOT NULL DEFAULT 1,              -- per-user usage limit
    is_active       INTEGER NOT NULL DEFAULT 1,
    started_at      TEXT NOT NULL,                           -- validity start
    expired_at      TEXT NOT NULL,                           -- validity end
    created_at      TEXT NOT NULL
)
```

### Table: `coupon_usage`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `coupon_id` | INTEGER | Yes | NULL | No |
| `customer_id` | INTEGER | Yes | NULL | No |
| `order_id` | INTEGER | Yes | NULL | No |
| `discount_amount` | REAL | Yes | NULL | No |
| `used_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE coupon_usage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    coupon_id       INTEGER NOT NULL REFERENCES coupons(id),
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    discount_amount REAL NOT NULL,                           -- actual discount amount
    used_at         TEXT NOT NULL
)
```

### Table: `complaints`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `order_id` | INTEGER | No | NULL | No |
| `customer_id` | INTEGER | Yes | NULL | No |
| `staff_id` | INTEGER | No | NULL | No |
| `category` | TEXT | Yes | NULL | No |
| `channel` | TEXT | Yes | NULL | No |
| `priority` | TEXT | Yes | NULL | No |
| `status` | TEXT | Yes | NULL | No |
| `title` | TEXT | Yes | NULL | No |
| `content` | TEXT | Yes | NULL | No |
| `resolution` | TEXT | No | NULL | No |
| `type` | TEXT | Yes | 'inquiry' | No |
| `sub_category` | TEXT | No | NULL | No |
| `compensation_type` | TEXT | No | NULL | No |
| `compensation_amount` | REAL | No | 0 | No |
| `escalated` | INTEGER | Yes | 0 | No |
| `response_count` | INTEGER | Yes | 1 | No |
| `created_at` | TEXT | Yes | NULL | No |
| `resolved_at` | TEXT | No | NULL | No |
| `closed_at` | TEXT | No | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE complaints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NULL REFERENCES orders(id),     -- order-related inquiry (NULL=general)
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    staff_id        INTEGER NULL REFERENCES staff(id),      -- assigned CS agent
    category        TEXT NOT NULL,                           -- product_defect/delivery_issue/wrong_item/refund_request/exchange_request/general_inquiry/price_inquiry
    channel         TEXT NOT NULL,                           -- website/phone/email/chat/kakao
    priority        TEXT NOT NULL,                           -- low/medium/high/urgent
    status          TEXT NOT NULL,                           -- open/resolved/closed
    title           TEXT NOT NULL,                           -- inquiry title
    content         TEXT NOT NULL,                           -- inquiry content
    resolution      TEXT NULL,                               -- resolution detail (when resolved)
    type            TEXT NOT NULL DEFAULT 'inquiry',         -- inquiry/claim/report
    sub_category    TEXT NULL,                               -- detailed category (e.g., initial_defect/in_use_damage/misdelivery)
    compensation_type TEXT NULL,                             -- refund/exchange/partial_refund/point_compensation/none
    compensation_amount REAL NULL DEFAULT 0,                 -- compensation amount
    escalated       INTEGER NOT NULL DEFAULT 0,             -- escalated to supervisor (0/1)
    response_count  INTEGER NOT NULL DEFAULT 1,             -- number of back-and-forth responses
    created_at      TEXT NOT NULL,                           -- submitted date
    resolved_at     TEXT NULL,                               -- resolved date
    closed_at       TEXT NULL                                -- closed date
)
```

### Table: `returns`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `order_id` | INTEGER | Yes | NULL | No |
| `customer_id` | INTEGER | Yes | NULL | No |
| `return_type` | TEXT | Yes | NULL | No |
| `reason` | TEXT | Yes | NULL | No |
| `reason_detail` | TEXT | Yes | NULL | No |
| `status` | TEXT | Yes | NULL | No |
| `is_partial` | INTEGER | Yes | 0 | No |
| `refund_amount` | REAL | Yes | NULL | No |
| `refund_status` | TEXT | Yes | NULL | No |
| `carrier` | TEXT | Yes | NULL | No |
| `tracking_number` | TEXT | Yes | NULL | No |
| `requested_at` | TEXT | Yes | NULL | No |
| `pickup_at` | TEXT | Yes | NULL | No |
| `received_at` | TEXT | No | NULL | No |
| `inspected_at` | TEXT | No | NULL | No |
| `inspection_result` | TEXT | No | NULL | No |
| `completed_at` | TEXT | No | NULL | No |
| `claim_id` | INTEGER | No | NULL | No |
| `exchange_product_id` | INTEGER | No | NULL | No |
| `restocking_fee` | REAL | Yes | 0 | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE returns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    return_type     TEXT NOT NULL,                           -- refund/exchange
    reason          TEXT NOT NULL,                           -- defective/wrong_item/change_of_mind/damaged_in_transit/not_as_described/late_delivery
    reason_detail   TEXT NOT NULL,                           -- detailed reason description
    status          TEXT NOT NULL,                           -- requested/pickup_scheduled/in_transit/completed
    is_partial      INTEGER NOT NULL DEFAULT 0,              -- partial return flag (~17%)
    refund_amount   REAL NOT NULL,                           -- refund amount
    refund_status   TEXT NOT NULL,                           -- pending/refunded/exchanged/partial_refund
    carrier         TEXT NOT NULL,                           -- pickup carrier
    tracking_number TEXT NOT NULL,                           -- pickup tracking number
    requested_at    TEXT NOT NULL,                           -- return request date
    pickup_at       TEXT NOT NULL,                           -- pickup scheduled/completed date
    received_at     TEXT NULL,                               -- warehouse receipt date
    inspected_at    TEXT NULL,                               -- inspection completion date
    inspection_result TEXT NULL,                             -- good/opened_good/defective/unsellable
    completed_at    TEXT NULL,                               -- processing completion date
    claim_id        INTEGER NULL REFERENCES complaints(id), -- linked claim (if return originated from CS)
    exchange_product_id INTEGER NULL REFERENCES products(id), -- replacement product for exchanges
    restocking_fee  REAL NOT NULL DEFAULT 0,                 -- change-of-mind restocking fee
    created_at      TEXT NOT NULL
)
```

### Table: `wishlists`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `customer_id` | INTEGER | Yes | NULL | No |
| `product_id` | INTEGER | Yes | NULL | No |
| `is_purchased` | INTEGER | Yes | 0 | No |
| `notify_on_sale` | INTEGER | Yes | 0 | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE wishlists (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    is_purchased    INTEGER NOT NULL DEFAULT 0,              -- converted to purchase flag (0/1)
    notify_on_sale  INTEGER NOT NULL DEFAULT 0,              -- price drop notification (0/1)
    created_at      TEXT NOT NULL,
    UNIQUE(customer_id, product_id)                          -- prevent duplicate customer-product pairs
)
```

### Table: `calendar`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `date_key` | TEXT | No | NULL | Yes |
| `year` | INTEGER | Yes | NULL | No |
| `month` | INTEGER | Yes | NULL | No |
| `day` | INTEGER | Yes | NULL | No |
| `quarter` | INTEGER | Yes | NULL | No |
| `day_of_week` | INTEGER | Yes | NULL | No |
| `day_name` | TEXT | Yes | NULL | No |
| `is_weekend` | INTEGER | Yes | 0 | No |
| `is_holiday` | INTEGER | Yes | 0 | No |
| `holiday_name` | TEXT | No | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE calendar (
    date_key        TEXT PRIMARY KEY,                        -- YYYY-MM-DD
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    day             INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,                        -- 1~4
    day_of_week     INTEGER NOT NULL,                        -- 0=Mon ~ 6=Sun
    day_name        TEXT NOT NULL,                           -- Monday~Sunday
    is_weekend      INTEGER NOT NULL DEFAULT 0,              -- Sat/Sun = 1
    is_holiday      INTEGER NOT NULL DEFAULT 0,              -- public holiday = 1
    holiday_name    TEXT NULL                                -- holiday name
)
```

### Table: `customer_grade_history`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `customer_id` | INTEGER | Yes | NULL | No |
| `old_grade` | TEXT | No | NULL | No |
| `new_grade` | TEXT | Yes | NULL | No |
| `changed_at` | TEXT | Yes | NULL | No |
| `reason` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE customer_grade_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    old_grade       TEXT NULL,                               -- previous grade (NULL on initial signup)
    new_grade       TEXT NOT NULL,                           -- new grade
    changed_at      TEXT NOT NULL,                           -- change datetime
    reason          TEXT NOT NULL                            -- signup/upgrade/downgrade/yearly_review
)
```

### Table: `tags`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `name` | TEXT | Yes | NULL | No |
| `category` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE tags (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    category        TEXT NOT NULL                            -- feature/use_case/target/spec
)
```

### Table: `product_tags`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `product_id` | INTEGER | Yes | NULL | Yes |
| `tag_id` | INTEGER | Yes | NULL | Yes |

**CREATE Statement:**
```sql
CREATE TABLE product_tags (
    product_id      INTEGER NOT NULL REFERENCES products(id),
    tag_id          INTEGER NOT NULL REFERENCES tags(id),
    PRIMARY KEY (product_id, tag_id)
)
```

### Table: `product_views`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `customer_id` | INTEGER | Yes | NULL | No |
| `product_id` | INTEGER | Yes | NULL | No |
| `referrer_source` | TEXT | Yes | NULL | No |
| `device_type` | TEXT | Yes | NULL | No |
| `duration_seconds` | INTEGER | Yes | NULL | No |
| `viewed_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE product_views (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    referrer_source TEXT NOT NULL,                           -- direct/search/ad/recommendation/social/email
    device_type     TEXT NOT NULL,                           -- desktop/mobile/tablet
    duration_seconds INTEGER NOT NULL,                       -- page dwell time (seconds)
    viewed_at       TEXT NOT NULL
)
```

### Table: `point_transactions`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `customer_id` | INTEGER | Yes | NULL | No |
| `order_id` | INTEGER | No | NULL | No |
| `type` | TEXT | Yes | NULL | No |
| `reason` | TEXT | Yes | NULL | No |
| `amount` | INTEGER | Yes | NULL | No |
| `balance_after` | INTEGER | Yes | NULL | No |
| `expires_at` | TEXT | No | NULL | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE point_transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    order_id        INTEGER NULL REFERENCES orders(id),
    type            TEXT NOT NULL,                           -- earn/use/expire
    reason          TEXT NOT NULL,                           -- purchase/confirm/review/signup/use/expiry
    amount          INTEGER NOT NULL,                        -- + for earn, - for use/expire
    balance_after   INTEGER NOT NULL,                        -- running balance after this transaction
    expires_at      TEXT NULL,                               -- expiry date for earn transactions
    created_at      TEXT NOT NULL
)
```

### Table: `promotions`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `name` | TEXT | Yes | NULL | No |
| `type` | TEXT | Yes | NULL | No |
| `discount_type` | TEXT | Yes | NULL | No |
| `discount_value` | REAL | Yes | NULL | No |
| `min_order_amount` | REAL | No | NULL | No |
| `started_at` | TEXT | Yes | NULL | No |
| `ended_at` | TEXT | Yes | NULL | No |
| `is_active` | INTEGER | Yes | 1 | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE promotions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,                           -- seasonal/flash/category
    discount_type   TEXT NOT NULL,                           -- percent/fixed
    discount_value  REAL NOT NULL,
    min_order_amount REAL NULL,
    started_at      TEXT NOT NULL,
    ended_at        TEXT NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL
)
```

### Table: `promotion_products`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `promotion_id` | INTEGER | Yes | NULL | Yes |
| `product_id` | INTEGER | Yes | NULL | Yes |
| `override_price` | REAL | No | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE promotion_products (
    promotion_id    INTEGER NOT NULL REFERENCES promotions(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    override_price  REAL NULL,                               -- flash sale special price (NULL = use promotion discount)
    PRIMARY KEY (promotion_id, product_id)
)
```

### Table: `product_qna`
| Column | Type | Not Null | Default | PK |
|---|---|---|---|---|
| `id` | INTEGER | No | NULL | Yes |
| `product_id` | INTEGER | Yes | NULL | No |
| `customer_id` | INTEGER | No | NULL | No |
| `staff_id` | INTEGER | No | NULL | No |
| `parent_id` | INTEGER | No | NULL | No |
| `content` | TEXT | Yes | NULL | No |
| `is_answered` | INTEGER | Yes | 0 | No |
| `created_at` | TEXT | Yes | NULL | No |

**CREATE Statement:**
```sql
CREATE TABLE product_qna (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    customer_id     INTEGER NULL REFERENCES customers(id),   -- NULL for staff answers
    staff_id        INTEGER NULL REFERENCES staff(id),       -- NULL for customer questions
    parent_id       INTEGER NULL REFERENCES product_qna(id), -- self-join: answer→question
    content         TEXT NOT NULL,
    is_answered     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL
)
```

## Views

### View: `v_monthly_sales`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_monthly_sales AS
SELECT
    SUBSTR(o.ordered_at, 1, 7) AS month,               -- YYYY-MM
    COUNT(DISTINCT o.id) AS order_count,                -- number of orders
    COUNT(DISTINCT o.customer_id) AS customer_count,    -- unique buyers
    CAST(SUM(o.total_amount) AS INTEGER) AS revenue,    -- total revenue
    CAST(AVG(o.total_amount) AS INTEGER) AS avg_order,  -- average order value
    SUM(o.discount_amount) AS total_discount            -- total discount
FROM orders o
WHERE o.status NOT IN ('cancelled')
GROUP BY SUBSTR(o.ordered_at, 1, 7)
ORDER BY month
```

### View: `v_customer_summary`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_customer_summary AS
SELECT
    c.id,
    c.name,
    c.email,
    c.grade,
    c.gender,
    CASE
        WHEN c.birth_date IS NULL THEN NULL
        ELSE CAST((julianday('2025-06-30') - julianday(c.birth_date)) / 365.25 AS INTEGER)
    END AS age,
    c.created_at AS joined_at,
    COALESCE(os.order_count, 0) AS total_orders,
    COALESCE(os.total_spent, 0) AS total_spent,
    COALESCE(os.first_order, '') AS first_order_at,
    COALESCE(os.last_order, '') AS last_order_at,
    COALESCE(rv.review_count, 0) AS review_count,
    COALESCE(rv.avg_rating, 0) AS avg_rating_given,
    COALESCE(ws.wishlist_count, 0) AS wishlist_count,
    c.is_active,
    c.last_login_at,
    CASE
        WHEN c.is_active = 0 THEN 'inactive'
        WHEN c.last_login_at IS NULL THEN 'never_logged_in'
        WHEN c.last_login_at < DATE('2025-06-30', '-365 days') THEN 'dormant'
        ELSE 'active'
    END AS activity_status
FROM customers c
LEFT JOIN (
    SELECT customer_id,
           COUNT(*) AS order_count,
           CAST(SUM(total_amount) AS INTEGER) AS total_spent,
           MIN(ordered_at) AS first_order,
           MAX(ordered_at) AS last_order
    FROM orders
    WHERE status NOT IN ('cancelled')
    GROUP BY customer_id
) os ON c.id = os.customer_id
LEFT JOIN (
    SELECT customer_id,
           COUNT(*) AS review_count,
           ROUND(AVG(rating), 1) AS avg_rating
    FROM reviews
    GROUP BY customer_id
) rv ON c.id = rv.customer_id
LEFT JOIN (
    SELECT customer_id, COUNT(*) AS wishlist_count
    FROM wishlists
    GROUP BY customer_id
) ws ON c.id = ws.customer_id
```

### View: `v_product_performance`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_product_performance AS
SELECT
    p.id,
    p.name,
    p.brand,
    p.sku,
    c.name AS category,
    p.price,
    p.cost_price,
    ROUND((p.price - p.cost_price) / p.price * 100, 1) AS margin_pct,
    p.stock_qty,
    p.is_active,
    COALESCE(s.total_sold, 0) AS total_sold,
    COALESCE(s.total_revenue, 0) AS total_revenue,
    COALESCE(s.order_count, 0) AS order_count,
    COALESCE(rv.review_count, 0) AS review_count,
    COALESCE(rv.avg_rating, 0) AS avg_rating,
    COALESCE(ws.wishlist_count, 0) AS wishlist_count,
    COALESCE(rt.return_count, 0) AS return_count
FROM products p
JOIN categories c ON p.category_id = c.id
LEFT JOIN (
    SELECT oi.product_id,
           SUM(oi.quantity) AS total_sold,
           CAST(SUM(oi.subtotal) AS INTEGER) AS total_revenue,
           COUNT(DISTINCT oi.order_id) AS order_count
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.id
    WHERE o.status NOT IN ('cancelled')
    GROUP BY oi.product_id
) s ON p.id = s.product_id
LEFT JOIN (
    SELECT product_id,
           COUNT(*) AS review_count,
           ROUND(AVG(rating), 1) AS avg_rating
    FROM reviews
    GROUP BY product_id
) rv ON p.id = rv.product_id
LEFT JOIN (
    SELECT product_id, COUNT(*) AS wishlist_count
    FROM wishlists
    GROUP BY product_id
) ws ON p.id = ws.product_id
LEFT JOIN (
    SELECT oi.product_id, COUNT(DISTINCT r.id) AS return_count
    FROM returns r
    JOIN order_items oi ON r.order_id = oi.order_id
    GROUP BY oi.product_id
) rt ON p.id = rt.product_id
```

### View: `v_category_tree`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_category_tree AS
WITH RECURSIVE tree AS (
    SELECT id, name, parent_id, depth,
           name AS full_path,
           CAST(printf('%04d', sort_order) AS TEXT) AS sort_key
    FROM categories
    WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.name, c.parent_id, c.depth,
           tree.full_path || ' > ' || c.name,
           tree.sort_key || '.' || printf('%04d', c.sort_order)
    FROM categories c
    JOIN tree ON c.parent_id = tree.id
)
SELECT t.id, t.name, t.parent_id, t.depth, t.full_path,
       COALESCE(p.product_count, 0) AS product_count
FROM tree t
LEFT JOIN (
    SELECT category_id, COUNT(*) AS product_count
    FROM products
    GROUP BY category_id
) p ON t.id = p.category_id
ORDER BY t.sort_key
```

### View: `v_daily_orders`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_daily_orders AS
SELECT
    DATE(ordered_at) AS order_date,
    CASE CAST(strftime('%w', ordered_at) AS INTEGER)
        WHEN 0 THEN '일' WHEN 1 THEN '월' WHEN 2 THEN '화'
        WHEN 3 THEN '수' WHEN 4 THEN '목' WHEN 5 THEN '금' WHEN 6 THEN '토'
    END AS day_of_week,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) AS confirmed,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
    SUM(CASE WHEN status IN ('return_requested','returned') THEN 1 ELSE 0 END) AS returned,
    CAST(SUM(CASE WHEN status != 'cancelled' THEN total_amount ELSE 0 END) AS INTEGER) AS revenue,
    CAST(AVG(CASE WHEN status != 'cancelled' THEN total_amount END) AS INTEGER) AS avg_order_amount
FROM orders
GROUP BY DATE(ordered_at)
ORDER BY order_date
```

### View: `v_payment_summary`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_payment_summary AS
SELECT
    method,
    COUNT(*) AS payment_count,
    CAST(SUM(amount) AS INTEGER) AS total_amount,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM payments), 1) AS pct,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status = 'refunded' THEN 1 ELSE 0 END) AS refunded,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
FROM payments
GROUP BY method
ORDER BY payment_count DESC
```

### View: `v_order_detail`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_order_detail AS
SELECT
    o.id AS order_id,
    o.order_number,
    o.ordered_at,
    o.status AS order_status,
    o.total_amount,
    o.discount_amount,
    o.shipping_fee,
    o.notes,
    c.id AS customer_id,
    c.name AS customer_name,
    c.email AS customer_email,
    c.grade AS customer_grade,
    p.method AS payment_method,
    p.status AS payment_status,
    p.card_issuer,
    p.installment_months,
    s.carrier,
    s.tracking_number,
    s.status AS shipping_status,
    s.delivered_at,
    ca.address1 || ' ' || COALESCE(ca.address2, '') AS delivery_address
FROM orders o
JOIN customers c ON o.customer_id = c.id
LEFT JOIN payments p ON o.id = p.order_id
LEFT JOIN shipping s ON o.id = s.order_id
LEFT JOIN customer_addresses ca ON o.address_id = ca.id
```

### View: `v_revenue_growth`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_revenue_growth AS
SELECT
    month,
    revenue,
    prev_revenue,
    CASE
        WHEN prev_revenue > 0
        THEN ROUND((revenue - prev_revenue) * 100.0 / prev_revenue, 1)
        ELSE NULL
    END AS growth_pct
FROM (
    SELECT
        SUBSTR(ordered_at, 1, 7) AS month,
        CAST(SUM(total_amount) AS INTEGER) AS revenue,
        LAG(CAST(SUM(total_amount) AS INTEGER)) OVER (ORDER BY SUBSTR(ordered_at, 1, 7)) AS prev_revenue
    FROM orders
    WHERE status NOT IN ('cancelled')
    GROUP BY SUBSTR(ordered_at, 1, 7)
)
ORDER BY month
```

### View: `v_top_products_by_category`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_top_products_by_category AS
SELECT
    category_name,
    product_name,
    brand,
    total_revenue,
    total_sold,
    rank_in_category
FROM (
    SELECT
        cat.name AS category_name,
        p.name AS product_name,
        p.brand,
        COALESCE(SUM(oi.subtotal), 0) AS total_revenue,
        COALESCE(SUM(oi.quantity), 0) AS total_sold,
        ROW_NUMBER() OVER (
            PARTITION BY p.category_id
            ORDER BY COALESCE(SUM(oi.subtotal), 0) DESC
        ) AS rank_in_category
    FROM products p
    JOIN categories cat ON p.category_id = cat.id
    LEFT JOIN order_items oi ON p.id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.id AND o.status NOT IN ('cancelled')
    GROUP BY p.id
)
WHERE rank_in_category <= 5
```

### View: `v_customer_rfm`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_customer_rfm AS
WITH rfm_raw AS (
    SELECT
        c.id AS customer_id,
        c.name,
        c.grade,
        CAST(julianday('2025-06-30') - julianday(MAX(o.ordered_at)) AS INTEGER) AS recency_days,
        COUNT(o.id) AS frequency,
        CAST(SUM(o.total_amount) AS INTEGER) AS monetary
    FROM customers c
    JOIN orders o ON c.id = o.customer_id
    WHERE o.status NOT IN ('cancelled')
    GROUP BY c.id
),
rfm_scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,   -- more recent = higher score
        NTILE(5) OVER (ORDER BY frequency DESC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC) AS m_score
    FROM rfm_raw
)
SELECT
    customer_id, name, grade,
    recency_days, frequency, monetary,
    r_score, f_score, m_score,
    r_score + f_score + m_score AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
        ELSE 'Others'
    END AS segment
FROM rfm_scored
```

### View: `v_cart_abandonment`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_cart_abandonment AS
SELECT
    c.id AS cart_id,
    cust.name AS customer_name,
    cust.email,
    c.status,
    c.created_at,
    COUNT(ci.id) AS item_count,
    CAST(SUM(p.price * ci.quantity) AS INTEGER) AS potential_revenue,
    GROUP_CONCAT(p.name, ', ') AS products
FROM carts c
JOIN customers cust ON c.customer_id = cust.id
JOIN cart_items ci ON c.id = ci.cart_id
JOIN products p ON ci.product_id = p.id
WHERE c.status = 'abandoned'
GROUP BY c.id
```

### View: `v_supplier_performance`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_supplier_performance AS
SELECT
    s.id AS supplier_id,
    s.company_name,
    COUNT(DISTINCT p.id) AS product_count,
    SUM(CASE WHEN p.is_active = 1 THEN 1 ELSE 0 END) AS active_products,
    COALESCE(sales.total_revenue, 0) AS total_revenue,
    COALESCE(sales.total_sold, 0) AS total_sold,
    COALESCE(ret.return_count, 0) AS return_count,
    CASE
        WHEN COALESCE(sales.total_sold, 0) > 0
        THEN ROUND(COALESCE(ret.return_count, 0) * 100.0 / sales.total_sold, 2)
        ELSE 0
    END AS return_rate_pct
FROM suppliers s
LEFT JOIN products p ON s.id = p.supplier_id
LEFT JOIN (
    SELECT p2.supplier_id,
           CAST(SUM(oi.subtotal) AS INTEGER) AS total_revenue,
           SUM(oi.quantity) AS total_sold
    FROM order_items oi
    JOIN products p2 ON oi.product_id = p2.id
    JOIN orders o ON oi.order_id = o.id
    WHERE o.status NOT IN ('cancelled')
    GROUP BY p2.supplier_id
) sales ON s.id = sales.supplier_id
LEFT JOIN (
    SELECT p3.supplier_id, COUNT(*) AS return_count
    FROM returns r
    JOIN order_items oi ON r.order_id = oi.order_id
    JOIN products p3 ON oi.product_id = p3.id
    GROUP BY p3.supplier_id
) ret ON s.id = ret.supplier_id
GROUP BY s.id
```

### View: `v_hourly_pattern`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_hourly_pattern AS
SELECT
    CAST(SUBSTR(ordered_at, 12, 2) AS INTEGER) AS hour,
    COUNT(*) AS order_count,
    CAST(AVG(total_amount) AS INTEGER) AS avg_amount,
    CASE
        WHEN CAST(SUBSTR(ordered_at, 12, 2) AS INTEGER) BETWEEN 0 AND 5 THEN 'dawn'
        WHEN CAST(SUBSTR(ordered_at, 12, 2) AS INTEGER) BETWEEN 6 AND 11 THEN 'morning'
        WHEN CAST(SUBSTR(ordered_at, 12, 2) AS INTEGER) BETWEEN 12 AND 17 THEN 'afternoon'
        ELSE 'evening'
    END AS time_slot
FROM orders
WHERE status NOT IN ('cancelled')
GROUP BY CAST(SUBSTR(ordered_at, 12, 2) AS INTEGER)
ORDER BY hour
```

### View: `v_product_abc`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_product_abc AS
SELECT
    product_id, product_name, brand, total_revenue,
    revenue_pct,
    cumulative_pct,
    CASE
        WHEN cumulative_pct <= 80 THEN 'A'
        WHEN cumulative_pct <= 95 THEN 'B'
        ELSE 'C'
    END AS abc_class
FROM (
    SELECT
        product_id, product_name, brand, total_revenue,
        ROUND(total_revenue * 100.0 / SUM(total_revenue) OVER (), 2) AS revenue_pct,
        ROUND(SUM(total_revenue) OVER (ORDER BY total_revenue DESC) * 100.0
              / SUM(total_revenue) OVER (), 2) AS cumulative_pct
    FROM (
        SELECT
            p.id AS product_id,
            p.name AS product_name,
            p.brand,
            CAST(COALESCE(SUM(oi.subtotal), 0) AS INTEGER) AS total_revenue
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        LEFT JOIN orders o ON oi.order_id = o.id AND o.status NOT IN ('cancelled')
        GROUP BY p.id
    )
)
ORDER BY total_revenue DESC
```

### View: `v_staff_workload`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_staff_workload AS
SELECT
    s.id AS staff_id,
    s.name,
    s.department,
    COALESCE(comp.complaint_count, 0) AS complaint_count,
    COALESCE(comp.resolved_count, 0) AS resolved_count,
    COALESCE(comp.avg_resolve_hours, 0) AS avg_resolve_hours,
    COALESCE(ord.cs_order_count, 0) AS cs_order_count
FROM staff s
LEFT JOIN (
    SELECT
        staff_id,
        COUNT(*) AS complaint_count,
        SUM(CASE WHEN status IN ('resolved','closed') THEN 1 ELSE 0 END) AS resolved_count,
        CAST(AVG(
            CASE WHEN resolved_at IS NOT NULL
            THEN (julianday(resolved_at) - julianday(created_at)) * 24
            END
        ) AS INTEGER) AS avg_resolve_hours
    FROM complaints
    GROUP BY staff_id
) comp ON s.id = comp.staff_id
LEFT JOIN (
    SELECT staff_id, COUNT(*) AS cs_order_count
    FROM orders WHERE staff_id IS NOT NULL
    GROUP BY staff_id
) ord ON s.id = ord.staff_id
WHERE s.department = 'CS' OR comp.complaint_count > 0
```

### View: `v_coupon_effectiveness`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_coupon_effectiveness AS
SELECT
    cp.id AS coupon_id,
    cp.code,
    cp.name,
    cp.type,
    cp.discount_value,
    cp.is_active,
    COALESCE(u.usage_count, 0) AS usage_count,
    cp.usage_limit,
    COALESCE(u.total_discount, 0) AS total_discount_given,
    COALESCE(u.total_order_revenue, 0) AS total_order_revenue,
    CASE
        WHEN COALESCE(u.total_discount, 0) > 0
        THEN ROUND(u.total_order_revenue / u.total_discount, 1)
        ELSE 0
    END AS roi_ratio
FROM coupons cp
LEFT JOIN (
    SELECT
        cu.coupon_id,
        COUNT(*) AS usage_count,
        CAST(SUM(cu.discount_amount) AS INTEGER) AS total_discount,
        CAST(SUM(o.total_amount) AS INTEGER) AS total_order_revenue
    FROM coupon_usage cu
    JOIN orders o ON cu.order_id = o.id
    GROUP BY cu.coupon_id
) u ON cp.id = u.coupon_id
ORDER BY COALESCE(u.usage_count, 0) DESC
```

### View: `v_return_analysis`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_return_analysis AS
SELECT
    reason,
    COUNT(*) AS total_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM returns), 1) AS pct,
    SUM(CASE WHEN return_type = 'refund' THEN 1 ELSE 0 END) AS refund_count,
    SUM(CASE WHEN return_type = 'exchange' THEN 1 ELSE 0 END) AS exchange_count,
    CAST(AVG(refund_amount) AS INTEGER) AS avg_refund_amount,
    SUM(CASE WHEN inspection_result = 'defective' THEN 1 ELSE 0 END) AS defective_count,
    SUM(CASE WHEN inspection_result = 'good' THEN 1 ELSE 0 END) AS good_count,
    CAST(AVG(
        CASE WHEN completed_at IS NOT NULL
        THEN julianday(completed_at) - julianday(requested_at)
        END
    ) AS INTEGER) AS avg_process_days
FROM returns
GROUP BY reason
ORDER BY total_count DESC
```

### View: `v_yearly_kpi`
**Description:** Analyzed view for e-commerce metrics.

**CREATE Statement:**
```sql
CREATE VIEW v_yearly_kpi AS
SELECT
    o_stats.yr AS year,
    o_stats.total_revenue,
    o_stats.order_count,
    o_stats.customer_count,
    CAST(o_stats.total_revenue * 1.0 / o_stats.order_count AS INTEGER) AS avg_order_value,
    CAST(o_stats.total_revenue * 1.0 / o_stats.customer_count AS INTEGER) AS revenue_per_customer,
    COALESCE(c.new_customers, 0) AS new_customers,
    o_stats.cancel_count,
    ROUND(o_stats.cancel_count * 100.0 / o_stats.order_count, 1) AS cancel_rate_pct,
    o_stats.return_count,
    ROUND(o_stats.return_count * 100.0 / o_stats.order_count, 1) AS return_rate_pct,
    COALESCE(r.review_count, 0) AS review_count,
    COALESCE(comp.complaint_count, 0) AS complaint_count
FROM (
    SELECT
        SUBSTR(o.ordered_at, 1, 4) AS yr,
        CAST(SUM(CASE WHEN o.status NOT IN ('cancelled') THEN o.total_amount ELSE 0 END) AS INTEGER) AS total_revenue,
        COUNT(*) AS order_count,
        COUNT(DISTINCT o.customer_id) AS customer_count,
        SUM(CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END) AS cancel_count,
        SUM(CASE WHEN o.status IN ('return_requested','returned') THEN 1 ELSE 0 END) AS return_count
    FROM orders o
    GROUP BY SUBSTR(o.ordered_at, 1, 4)
) o_stats
LEFT JOIN (
    SELECT SUBSTR(created_at, 1, 4) AS yr, COUNT(*) AS new_customers
    FROM customers GROUP BY SUBSTR(created_at, 1, 4)
) c ON o_stats.yr = c.yr
LEFT JOIN (
    SELECT SUBSTR(created_at, 1, 4) AS yr, COUNT(*) AS review_count
    FROM reviews GROUP BY SUBSTR(created_at, 1, 4)
) r ON o_stats.yr = r.yr
LEFT JOIN (
    SELECT SUBSTR(created_at, 1, 4) AS yr, COUNT(*) AS complaint_count
    FROM complaints GROUP BY SUBSTR(created_at, 1, 4)
) comp ON o_stats.yr = comp.yr
ORDER BY o_stats.yr
```


