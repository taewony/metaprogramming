---
type: sqlite_table
database: techshop.db
table: order_items
title: order_items table
description: Line items connecting orders to products with quantity and price details.
tags:
- sqlite
- schema
- order_items
columns:
- name: id
  type: INTEGER
  primary_key: true
  not_null: false
- name: order_id
  type: INTEGER
  primary_key: false
  not_null: false
- name: product_id
  type: INTEGER
  primary_key: false
  not_null: false
- name: quantity
  type: INTEGER
  primary_key: false
  not_null: false
- name: unit_price
  type: REAL
  primary_key: false
  not_null: false
- name: subtotal
  type: REAL
  primary_key: false
  not_null: false
foreign_keys:
- column: order_id
  references: orders.id
- column: product_id
  references: products.id
---

# order_items

Line items connecting orders to products with quantity and price details.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `id` | `INTEGER` | true | false |
| `order_id` | `INTEGER` | false | false |
| `product_id` | `INTEGER` | false | false |
| `quantity` | `INTEGER` | false | false |
| `unit_price` | `REAL` | false | false |
| `subtotal` | `REAL` | false | false |

## Foreign Keys

- `order_id` -> `orders.id`
- `product_id` -> `products.id`
