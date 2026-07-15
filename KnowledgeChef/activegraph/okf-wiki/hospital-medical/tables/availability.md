---
type: sqlite_table
database: hospital.db
table: availability
title: availability table
description: Doctor availability slots by date and time.
tags:
- sqlite
- schema
- availability
columns:
- name: doctor_id
  type: VARCHAR(10)
  primary_key: true
  not_null: true
- name: available_date
  type: DATE
  primary_key: true
  not_null: true
- name: available_time
  type: TIME
  primary_key: true
  not_null: true
- name: status
  type: VARCHAR(10)
  primary_key: false
  not_null: true
foreign_keys:
- column: doctor_id
  references: doctors.doctor_id
---

# availability

Doctor availability slots by date and time.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `doctor_id` | `VARCHAR(10)` | true | true |
| `available_date` | `DATE` | true | true |
| `available_time` | `TIME` | true | true |
| `status` | `VARCHAR(10)` | false | true |

## Foreign Keys

- `doctor_id` -> `doctors.doctor_id`
