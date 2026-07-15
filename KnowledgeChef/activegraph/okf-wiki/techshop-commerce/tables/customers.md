---
type: sqlite_table
database: techshop.db
table: customers
title: customers table
description: Customers with contact details, membership grade, points, and active
  status.
tags:
- sqlite
- schema
- customers
columns:
- name: id
  type: INTEGER
  primary_key: true
  not_null: false
- name: email
  type: TEXT
  primary_key: false
  not_null: false
- name: name
  type: TEXT
  primary_key: false
  not_null: false
- name: phone
  type: TEXT
  primary_key: false
  not_null: false
- name: grade
  type: TEXT
  primary_key: false
  not_null: false
- name: point_balance
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

# customers

Customers with contact details, membership grade, points, and active status.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `id` | `INTEGER` | true | false |
| `email` | `TEXT` | false | false |
| `name` | `TEXT` | false | false |
| `phone` | `TEXT` | false | false |
| `grade` | `TEXT` | false | false |
| `point_balance` | `INTEGER` | false | false |
| `is_active` | `INTEGER` | false | false |
| `created_at` | `TEXT` | false | false |
