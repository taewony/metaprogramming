---
type: sqlite_table
database: hospital.db
table: insurance
title: insurance table
description: Patient insurance enrollment and coverage periods.
tags:
- sqlite
- schema
- insurance
columns:
- name: insurance_id
  type: VARCHAR(10)
  primary_key: true
  not_null: false
- name: patient_id
  type: VARCHAR(10)
  primary_key: false
  not_null: true
- name: provider
  type: VARCHAR(100)
  primary_key: false
  not_null: true
- name: insurance_type
  type: VARCHAR(50)
  primary_key: false
  not_null: true
- name: coverage_start
  type: DATE
  primary_key: false
  not_null: true
- name: coverage_end
  type: DATE
  primary_key: false
  not_null: true
- name: copay_percentage
  type: INT
  primary_key: false
  not_null: true
foreign_keys:
- column: patient_id
  references: patients.patient_id
---

# insurance

Patient insurance enrollment and coverage periods.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `insurance_id` | `VARCHAR(10)` | true | false |
| `patient_id` | `VARCHAR(10)` | false | true |
| `provider` | `VARCHAR(100)` | false | true |
| `insurance_type` | `VARCHAR(50)` | false | true |
| `coverage_start` | `DATE` | false | true |
| `coverage_end` | `DATE` | false | true |
| `copay_percentage` | `INT` | false | true |

## Foreign Keys

- `patient_id` -> `patients.patient_id`
