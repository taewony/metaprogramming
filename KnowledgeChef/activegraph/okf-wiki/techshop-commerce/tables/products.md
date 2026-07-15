---
type: sqlite_table
database: techshop.db
table: products
title: products table
description: Products with brand, SKU, price, cost, stock, and active status.
tags:
- sqlite
- schema
- products
columns:
- name: id
  type: INTEGER
  primary_key: true
  not_null: false
- name: name
  type: TEXT
  primary_key: false
  not_null: false
- name: brand
  type: TEXT
  primary_key: false
  not_null: false
- name: sku
  type: TEXT
  primary_key: false
  not_null: false
- name: price
  type: REAL
  primary_key: false
  not_null: false
- name: cost_price
  type: REAL
  primary_key: false
  not_null: false
- name: stock_qty
  type: INTEGER
  primary_key: false
  not_null: false
- name: is_active
  type: INTEGER
  primary_key: false
  not_null: false
- name: created_at
  type: TEXT
  primary_key: false
  not_null: false
foreign_keys: []
---

# products

Products with brand, SKU, price, cost, stock, and active status.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `id` | `INTEGER` | true | false |
| `name` | `TEXT` | false | false |
| `brand` | `TEXT` | false | false |
| `sku` | `TEXT` | false | false |
| `price` | `REAL` | false | false |
| `cost_price` | `REAL` | false | false |
| `stock_qty` | `INTEGER` | false | false |
| `is_active` | `INTEGER` | false | false |
| `created_at` | `TEXT` | false | false |
