---
type: sqlite_table
database: hospital.db
table: procedure_coverage
title: procedure_coverage table
description: Procedure coverage rates by insurance plan.
tags:
- sqlite
- schema
- procedure_coverage
columns:
- name: insurance_id
  type: VARCHAR(10)
  primary_key: true
  not_null: true
- name: procedure_code
  type: VARCHAR(10)
  primary_key: true
  not_null: true
- name: procedure_name
  type: VARCHAR(100)
  primary_key: false
  not_null: true
- name: coverage_rate
  type: INT
  primary_key: false
  not_null: true
- name: max_coverage
  type: INT
  primary_key: false
  not_null: true
foreign_keys:
- column: insurance_id
  references: insurance.insurance_id
---

# procedure_coverage

Procedure coverage rates by insurance plan.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `insurance_id` | `VARCHAR(10)` | true | true |
| `procedure_code` | `VARCHAR(10)` | true | true |
| `procedure_name` | `VARCHAR(100)` | false | true |
| `coverage_rate` | `INT` | false | true |
| `max_coverage` | `INT` | false | true |

## Foreign Keys

- `insurance_id` -> `insurance.insurance_id`
