---
type: sqlite_table
database: hospital.db
table: appointments
title: appointments table
description: Appointment bookings between patients and doctors.
tags:
- sqlite
- schema
- appointments
columns:
- name: appointment_id
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
- name: appointment_date
  type: DATE
  primary_key: false
  not_null: true
- name: appointment_time
  type: TIME
  primary_key: false
  not_null: true
- name: reason
  type: TEXT
  primary_key: false
  not_null: false
- name: status
  type: VARCHAR(20)
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

# appointments

Appointment bookings between patients and doctors.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `appointment_id` | `VARCHAR(10)` | true | false |
| `patient_id` | `VARCHAR(10)` | false | true |
| `doctor_id` | `VARCHAR(10)` | false | true |
| `appointment_date` | `DATE` | false | true |
| `appointment_time` | `TIME` | false | true |
| `reason` | `TEXT` | false | false |
| `status` | `VARCHAR(20)` | false | true |
| `notes` | `TEXT` | false | false |

## Foreign Keys

- `doctor_id` -> `doctors.doctor_id`
- `patient_id` -> `patients.patient_id`
