---
type: sqlite_table
database: techshop.db
table: orders
title: orders table
description: Orders placed by customers with status, total amount, and order timestamp.
tags:
- sqlite
- schema
- orders
columns:
- name: id
  type: INTEGER
  primary_key: true
  not_null: false
- name: order_number
  type: TEXT
  primary_key: false
  not_null: false
- name: customer_id
  type: INTEGER
  primary_key: false
  not_null: false
- name: status
  type: TEXT
  primary_key: false
  not_null: false
- name: total_amount
  type: REAL
  primary_key: false
  not_null: false
- name: ordered_at
  type: TEXT
  primary_key: false
  not_null: false
foreign_keys:
- column: customer_id
  references: customers.id
---

# orders

Orders placed by customers with status, total amount, and order timestamp.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `id` | `INTEGER` | true | false |
| `order_number` | `TEXT` | false | false |
| `customer_id` | `INTEGER` | false | false |
| `status` | `TEXT` | false | false |
| `total_amount` | `REAL` | false | false |
| `ordered_at` | `TEXT` | false | false |

## Foreign Keys

- `customer_id` -> `customers.id`
