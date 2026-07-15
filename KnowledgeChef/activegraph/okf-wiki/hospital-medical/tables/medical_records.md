---
type: sqlite_table
database: hospital.db
table: medical_records
title: medical_records table
description: Patient medical records authored by doctors.
tags:
- sqlite
- schema
- medical_records
columns:
- name: record_id
  type: VARCHAR(10)
  primary_key: true
  not_null: false
- name: patient_id
  type: VARCHAR(10)
  primary_key: false
  not_null: true
- name: doctor_id
  type: VARCHAR(10)
  primary_key: false
  not_null: true
- name: record_date
  type: DATE
  primary_key: false
  not_null: true
- name: record_type
  type: VARCHAR(20)
  primary_key: false
  not_null: true
- name: content
  type: TEXT
  primary_key: false
  not_null: true
- name: notes
  type: TEXT
  primary_key: false
  not_null: false
foreign_keys:
- column: doctor_id
  references: doctors.doctor_id
- column: patient_id
  references: patients.patient_id
---

# medical_records

Patient medical records authored by doctors.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `record_id` | `VARCHAR(10)` | true | false |
| `patient_id` | `VARCHAR(10)` | false | true |
| `doctor_id` | `VARCHAR(10)` | false | true |
| `record_date` | `DATE` | false | true |
| `record_type` | `VARCHAR(20)` | false | true |
| `content` | `TEXT` | false | true |
| `notes` | `TEXT` | false | false |

## Foreign Keys

- `doctor_id` -> `doctors.doctor_id`
- `patient_id` -> `patients.patient_id`
