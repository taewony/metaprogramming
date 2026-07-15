---
type: sqlite_table
database: hospital.db
table: prescriptions
title: prescriptions table
description: Medication prescriptions issued to patients by doctors.
tags:
- sqlite
- schema
- prescriptions
columns:
- name: prescription_id
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
- name: prescription_date
  type: DATE
  primary_key: false
  not_null: true
- name: medication
  type: VARCHAR(100)
  primary_key: false
  not_null: true
- name: dosage
  type: VARCHAR(50)
  primary_key: false
  not_null: true
- name: frequency
  type: VARCHAR(50)
  primary_key: false
  not_null: true
- name: duration
  type: VARCHAR(20)
  primary_key: false
  not_null: true
- name: status
  type: VARCHAR(20)
  primary_key: false
  not_null: true
- name: renewable
  type: BOOLEAN
  primary_key: false
  not_null: true
foreign_keys:
- column: doctor_id
  references: doctors.doctor_id
- column: patient_id
  references: patients.patient_id
---

# prescriptions

Medication prescriptions issued to patients by doctors.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `prescription_id` | `VARCHAR(10)` | true | false |
| `patient_id` | `VARCHAR(10)` | false | true |
| `doctor_id` | `VARCHAR(10)` | false | true |
| `prescription_date` | `DATE` | false | true |
| `medication` | `VARCHAR(100)` | false | true |
| `dosage` | `VARCHAR(50)` | false | true |
| `frequency` | `VARCHAR(50)` | false | true |
| `duration` | `VARCHAR(20)` | false | true |
| `status` | `VARCHAR(20)` | false | true |
| `renewable` | `BOOLEAN` | false | true |

## Foreign Keys

- `doctor_id` -> `doctors.doctor_id`
- `patient_id` -> `patients.patient_id`
