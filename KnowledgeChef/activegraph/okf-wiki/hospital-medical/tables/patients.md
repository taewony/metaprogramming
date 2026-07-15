---
type: sqlite_table
database: hospital.db
table: patients
title: patients table
description: Patient demographics, contact information, insurance number, and clinical
  attributes.
tags:
- sqlite
- schema
- patients
columns:
- name: patient_id
  type: VARCHAR(10)
  primary_key: true
  not_null: false
- name: name
  type: VARCHAR(50)
  primary_key: false
  not_null: true
- name: birth_date
  type: DATE
  primary_key: false
  not_null: true
- name: gender
  type: CHAR(1)
  primary_key: false
  not_null: true
- name: phone
  type: VARCHAR(20)
  primary_key: false
  not_null: true
- name: email
  type: VARCHAR(100)
  primary_key: false
  not_null: true
- name: address
  type: VARCHAR(200)
  primary_key: false
  not_null: true
- name: insurance_number
  type: VARCHAR(20)
  primary_key: false
  not_null: true
- name: blood_type
  type: VARCHAR(5)
  primary_key: false
  not_null: true
- name: allergies
  type: TEXT
  primary_key: false
  not_null: false
foreign_keys: []
---

# patients

Patient demographics, contact information, insurance number, and clinical attributes.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `patient_id` | `VARCHAR(10)` | true | false |
| `name` | `VARCHAR(50)` | false | true |
| `birth_date` | `DATE` | false | true |
| `gender` | `CHAR(1)` | false | true |
| `phone` | `VARCHAR(20)` | false | true |
| `email` | `VARCHAR(100)` | false | true |
| `address` | `VARCHAR(200)` | false | true |
| `insurance_number` | `VARCHAR(20)` | false | true |
| `blood_type` | `VARCHAR(5)` | false | true |
| `allergies` | `TEXT` | false | false |
